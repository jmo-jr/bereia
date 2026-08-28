const fs = require('fs');
const path = require('path');

// const DICT_PATH = path.join(__dirname, '..', 'nt_greek-pt_dict.json');
const DICT_PATH = path.join(__dirname, '..', 'dict_flex_nt-lxx_greek-pt.json');
const SOURCE_DIR = path.join(__dirname, '..', '..', 'interlinear', 'nt');
const MISSING_LEMMAS_LOG_PATH = path.join(__dirname, '..', '..', '..', 'nt-missing-lemmas.log');

const DICT_FIELDS = ['strongs', 'grego', 'transliteracao', 'verbete', 'ocorrencias', 'traducao', 'pt', 'morfologia', 'abrev_morf' ];

// Terms that should keep diacritics to avoid collapsing homographs.
const NORMALIZATION_EXCEPTIONS = new Set(["α", "εν", "η", "ης", "ην", "ητε", "ου", "ει", "ως", "ο", "ος", "αν", "τις", "που", "πως", "αυτου", "αυτη", "δη", "ανω", "ημερα", "εκτος", "τι", "εις", "τινι", "γενεας", "ετερα", "τινες", "ηλιου", "φοβου", "προσευχη"]);

const loadJsonFile = filePath => JSON.parse(fs.readFileSync(filePath, 'utf8'));

const normalizeGreek = (value = '') => {
  const trimmed = String(value).trim();

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
              `referencias: ${entry.references.join(', ')}`,
            ].join('\n')).join('\n\n')
          : 'Nenhum lemma sem equivalente foi encontrado.',
        '',
      ].join('\n');

      fs.writeFileSync(MISSING_LEMMAS_LOG_PATH, content, 'utf8');
    },
  };
};

const createEnhanceTokenWithDict = (dict, missingLemmaTracker) => {
  const dictIndex = buildDictIndex(dict);

  return (token = {}, context = {}) => {
    const normalized = normalizeGreek(token.lemma || '');
    const dictEntry = dictIndex[normalized];

    if (!dictEntry) {
      missingLemmaTracker.record(token, context);
      return { ...token };
    }

    const lexicon = DICT_FIELDS.reduce((acc, field) => {
      if (dictEntry[field] !== undefined) {
        acc[field] = dictEntry[field];
      }
      return acc;
    }, {});

    return {
      ...token,
      ...lexicon,
    };
  };
};

const normalizePericope = (pericope = {}, enhanceTokenWithDict, context = {}) => {
  const verses = (pericope.verses || []).map(verseEntry => ({
    number: Number(verseEntry.verse),
    tokens: (verseEntry.tokens || []).map(token => enhanceTokenWithDict(token, {
      ...context,
      verseNumber: Number(verseEntry.verse),
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
      normalizePericope(pericope, enhanceTokenWithDict, { bookId, chapterNumber }),
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
  const enhanceTokenWithDict = createEnhanceTokenWithDict(dict, missingLemmaTracker);

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
