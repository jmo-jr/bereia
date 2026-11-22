const fs = require('fs');
const path = require('path');
const { greekCaseKey, buildCaseDictIndex } = require('../../lib/greek-form-lookup');
const { buildAccentAliasIndex, validateAliasEvidence } = require('../../lib/greek-accent-aliases');

// const DICT_PATH = path.join(__dirname, '..', 'nt_greek-pt_dict.json');
const DICT_PATH = path.join(__dirname, '..', 'nt/dict_flex_nt-lxx_greek-pt.json');
const FORM_INDEX_PATH = path.join(__dirname, 'dict_form_index_nt-lxx_greek-pt.json');
const ACCENT_ALIASES_PATH = path.join(__dirname, 'greek_accent_aliases.json');
const SOURCE_DIR = path.join(__dirname, '..', '..', 'interlinear', 'nt');
const MISSING_LEMMAS_LOG_PATH = path.join(__dirname, '..', '..', '..', 'nt-missing-lemmas.log');

const DICT_FIELDS = ['strongs', 'grego', 'transliteracao', 'verbete', 'ocorrencias', 'traducao', 'pt', 'morfologia', 'abrev_morf' ];

// Terms that should keep diacritics to avoid collapsing homographs.
const NORMALIZATION_EXCEPTIONS = new Set([ "α", "αλλα", "αν", "ανω", "αυτη", "αυτου", "γενεασ", "γενεας", "δη", "ει", "ειληφωσ", "εισ", "εις", "εκτοσ", "ελαιαι", "εν", "εξειλετο", "ετερα", "ετεραι", "ετοιμασομεν", "η", "ηι", "ηλιου", "ημερα", "ημεραι", "ην", "ησ", "ης", "ητε", "καπερναουμ", "κλεισ", "κλεις", "κραββατον", "μεριμναισ", "μοιχειαι", "μωραι", "ο", "ον", "οσ", "ος", "ου", "ουσ", "ους", "πονηριαι", "ποτε", "που", "προσευχη", "προσευχηι", "πωσ", "πως", "σησ", "σης", "στειραι", "ταλαντα", "ταλαντον", "τι", "τινα", "τινεσ", "τινες", "τινι", "τινοσ", "τινος", "τισ", "τις", "φοβου", "φρεναπαται", "ω", "ων", "ωσ", "ως", "ωσιν" ]);
const SPECIAL_CASES = new Set(["ὦ ", "Ὦ\u200B"]);

const loadJsonFile = filePath => JSON.parse(fs.readFileSync(filePath, 'utf8'));

const normalizeGreek = (value = '') => {
	const original = String(value);
  const trimmed = SPECIAL_CASES.has(original.trim())
    ? original
    : original.trim();

  if (!trimmed) {
    return '';
  }

  const normalized = trimmed.normalize('NFD');
  const stripped = normalized.replace(/[\u0300-\u036f]/g, '');
  const lowered = stripped.toLowerCase();

  if (NORMALIZATION_EXCEPTIONS.has(lowered)) {
    return trimmed.toLowerCase().normalize('NFC');
  }

  return lowered;
};

const buildDictIndex = dict =>
  Object.entries(dict).reduce((acc, [key, entry]) => {
    const normalizedKey = normalizeGreek(key);
    if (normalizedKey && !acc[normalizedKey]) {
      acc[normalizedKey] = entry;
    }
    return acc;
  }, {});

const createMissingLemmaTracker = () => {
  const lemmas = new Map();

  return {
    record(token = {}, context = {}) {
      const lemma = String(token.lemma || '').trim();

      if (!lemma) {
        return;
      }

      const normalized = normalizeGreek(lemma);
      const key = `${lemma}\u0000${normalized}`;
      const hasBook = context.bookId !== undefined && context.bookId !== '';
      const hasChapter = context.chapterNumber !== undefined;
      const hasVerse = context.verseNumber !== undefined;
      const reference = [
        hasBook ? context.bookId : undefined,
        hasChapter && hasVerse ? `${context.chapterNumber}:${context.verseNumber}` : undefined,
      ].filter(value => value !== undefined).join(' ');

      if (!lemmas.has(key)) {
        lemmas.set(key, {
          lemma,
          normalized,
          occurrences: 0,
          references: new Set(),
          motivo: context.motivo || 'forma_ausente',
        });
      }

      const entry = lemmas.get(key);
      entry.occurrences += 1;

      if (reference) {
        entry.references.add(reference);
      }
    },

    writeLog() {
      const generatedAt = new Date().toISOString();
      const entries = Array.from(lemmas.values())
        .map(entry => ({
          ...entry,
          references: Array.from(entry.references).sort(),
        }))
        .sort((a, b) => a.normalized.localeCompare(b.normalized) || a.lemma.localeCompare(b.lemma));

      const content = [
        `Lemmas sem equivalentes no dicionario do NT`,
        `Gerado em: ${generatedAt}`,
        `Dicionario: ${path.relative(process.cwd(), DICT_PATH)}`,
        `Origem: ${path.relative(process.cwd(), SOURCE_DIR)}`,
        `Total de lemmas unicos: ${entries.length}`,
        '',
        entries.length
          ? entries.map(entry => [
              `lemma: ${entry.lemma}`,
              `normalizado: ${entry.normalized}`,
              `ocorrencias: ${entry.occurrences}`,
              `motivo: ${entry.motivo}`,
              `referencias: ${entry.references.join(', ')}`,
            ].join('\n')).join('\n\n')
          : 'Nenhum lemma sem equivalente foi encontrado.',
        '',
      ].join('\n');

      fs.writeFileSync(MISSING_LEMMAS_LOG_PATH, content, 'utf8');
    },
  };
};

const createEnhanceTokenWithDict = (dict, missingLemmaTracker, extraFields = [], formIndex = {}, accentPolicy = null) => {
  const dictIndex = buildDictIndex(dict);
  const caseDictIndex = buildCaseDictIndex(dict, formIndex);
  const accentAliasIndex = buildAccentAliasIndex(dict, formIndex, accentPolicy);
  const canonicalDictIndex = new Map();
  for (const [form, entry] of Object.entries(dict)) {
    const key = form.normalize('NFC');
    if (!canonicalDictIndex.has(key)) canonicalDictIndex.set(key, entry);
  }

  return (token = {}, context = {}) => {
    const form = String(token.lemma || '');
    let caseAnalyses;
    let accentMatch;
    // Prioridade segura para formas cobertas. O fallback legado permanece
    // somente durante a migração de cobertura, sob acompanhamento da auditoria.
    let dictEntry = Object.hasOwn(dict, form) ? dict[form] : canonicalDictIndex.get(form.normalize('NFC'));
    if (!dictEntry) {
      const candidates = caseDictIndex.get(greekCaseKey(form)) || [];
      const distinctForms = new Set(candidates.map(candidate => candidate.reference.grego.normalize('NFC')));
      const distinctStrongs = new Set(candidates.map(candidate => candidate.reference.strongs));
      if (distinctForms.size > 1 || distinctStrongs.size > 1) {
        // Nunca atravessar uma ambiguidade de caixa escolhendo o primeiro
        // registro da projeção ou retomando o fallback sem marcas.
        missingLemmaTracker.record(token, { ...context, motivo: 'ambiguidade_caixa' });
        return { ...token, consulta_dicionario: 'ambiguidade_caixa',
          analises_dicionario: candidates.map(candidate => ({ ...candidate.reference })) };
      }
      if (candidates.length > 1) caseAnalyses = candidates.map(candidate => ({ ...candidate.reference }));
      dictEntry = candidates[0]?.entry;
      if (!dictEntry) {
        accentMatch = accentAliasIndex.resolve(form, context);
        if (accentMatch.estado === 'pendente') {
          missingLemmaTracker.record(token, { ...context, motivo: accentMatch.motivo });
          return { ...token, consulta_dicionario: 'alias_acento_pendente', motivo_dicionario: accentMatch.motivo };
        }
        dictEntry = accentMatch.estado === 'resolvido' ? accentMatch.entrada : dictIndex[normalizeGreek(form)];
      }
    }

    if (!dictEntry) {
      missingLemmaTracker.record(token, context);
      return { ...token };
    }

    const lexicon = [...DICT_FIELDS, ...extraFields].reduce((acc, field) => {
      if (dictEntry[field] !== undefined) {
        acc[field] = dictEntry[field];
      }
      return acc;
    }, {});

    return {
      ...token,
      ...lexicon,
      ...(caseAnalyses ? { consulta_dicionario: 'caixa_multianalise', analises_dicionario: caseAnalyses } : {}),
      ...(accentMatch?.estado === 'resolvido' ? { consulta_dicionario: 'alias_agudo_grave',
        alias_dicionario: { id: accentMatch.alias.id, destino: accentMatch.alias.destino, referencia: accentMatch.referencia },
        ocorrencias_forma_tm: accentMatch.alias.ocorrencias_forma_tm } : {}),
    };
  };
};

const normalizePericope = (pericope = {}, enhanceTokenWithDict, context = {}) => {
  const verses = (pericope.verses || []).map(verseEntry => ({
    number: Number(verseEntry.verse),
    tokens: (verseEntry.tokens || []).map((token, position) => enhanceTokenWithDict(token, {
      ...context,
      verseNumber: Number(verseEntry.verse),
      tokenPosition: position + 1,
    })),
  }));

  return {
    ...pericope,
    start_verse: pericope.start_verse !== undefined ? Number(pericope.start_verse) : undefined,
    end_verse: pericope.end_verse !== undefined ? Number(pericope.end_verse) : undefined,
    verses,
  };
};

const normalizeBookData = (bookContent = [], enhanceTokenWithDict, bookId) =>
  bookContent.map(chapterEntry => {
    const chapterNumber = Number(chapterEntry.chapter);
    const pericopes = (chapterEntry.pericopes || []).map(pericope =>
      normalizePericope(pericope, enhanceTokenWithDict, { corpus: 'nt', bookId, chapterNumber }),
    );
    const verses = pericopes.flatMap(pericope => pericope.verses);

    return {
      number: chapterNumber,
      pericopes,
      verses,
    };
  });

const loadAllBooks = () => {
  if (!fs.existsSync(SOURCE_DIR)) {
    return {};
  }

  const dict = loadJsonFile(DICT_PATH);
  const missingLemmaTracker = createMissingLemmaTracker();
  const manifest = fs.existsSync(ACCENT_ALIASES_PATH) ? loadJsonFile(ACCENT_ALIASES_PATH) : null;
  const policy = manifest ? { manifest, validBooks: validateAliasEvidence(manifest) } : null;
  const enhanceTokenWithDict = createEnhanceTokenWithDict(dict, missingLemmaTracker, [], loadJsonFile(FORM_INDEX_PATH), policy);

  const books = fs
    .readdirSync(SOURCE_DIR)
    .filter(filename => filename.toLowerCase().endsWith('.json'))
    .reduce((acc, filename) => {
      const bookId = path.basename(filename, path.extname(filename));
      const rawContent = loadJsonFile(path.join(SOURCE_DIR, filename));

      acc[bookId] = normalizeBookData(rawContent, enhanceTokenWithDict, bookId);
      return acc;
    }, {});

  missingLemmaTracker.writeLog();

  return books;
};

module.exports = loadAllBooks;

// Reutilizado pela LXX sem executar o carregamento nem gravar o log do NT.
module.exports.createEnhanceTokenWithDict = createEnhanceTokenWithDict;
