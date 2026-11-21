const fs = require('node:fs');
const path = require('node:path');
const dictionary = require('../dictionary/core');
const { canNormalizeGreekVariant } = require('../../src/_data/nt');
const { readVerse, renderVerse } = require('./verse-html');
const { createLexicon, indexExceptions, resolveVerse } = require('./resolve');

const BOOK = 'Mt';
const CHAPTER = 8;
const greekSource = 'src/interlinear/nt/MT.json';
const formIndex = 'src/_data/nt/dict_form_index_nt-lxx_greek-pt.json';
const exceptionsFile = 'tools/lexical-alignment/exceptions.json';
const signaturesFile = 'tools/lexical-alignment/approved-verses.json';
const watchPaths = [greekSource, exceptionsFile, signaturesFile];
const reportDirectory = 'reports/lexical-alignment/mt-8';
const contractions = new Set(['à', 'às', 'da', 'das', 'do', 'dos', 'na', 'nas', 'no', 'nos',
  'ao', 'aos', 'pelo', 'pelos', 'pela', 'pelas']);
const auxiliaries = new Set(['tendo', 'foi', 'foram', 'seja', 'será', 'está', 'estava', 'estavam']);
const commonGrammar = new Set([
  ...contractions, ...auxiliaries,
  'a', 'as', 'o', 'os', 'um', 'uma', 'uns', 'umas', 'de', 'em',
  'ele', 'ela', 'eles', 'elas', 'lhe', 'lhes', 'me', 'se', 'te', 'que', 'e', 'para', 'por', 'com',
  'mas', 'porém', 'quando', 'onde', 'como', 'porque', 'então', 'ou', 'também', 'nem',
]);

function rooted(file) {
  return path.resolve(dictionary.ROOT, file);
}

function readExceptions() {
  const source = fs.readFileSync(rooted(exceptionsFile), 'utf8');
  const data = JSON.parse(source);
  const tokens = [...source.matchAll(/"(?:[^"\\]|\\.)*"|[{}:]/gs)].map(match => match[0]);
  const keySets = [];
  for (const [index, token] of tokens.entries()) {
    if (token === '{') keySets.push(new Set());
    else if (token === '}') keySets.pop();
    else if (token.startsWith('"') && tokens[index + 1] === ':') {
      const key = JSON.parse(token);
      const keys = keySets.at(-1);
      if (keys.has(key)) throw new Error(`Chave duplicada em ${exceptionsFile}: ${key}`);
      keys.add(key);
    }
  }
  return data;
}

function describe(entry) {
  return {
    form: entry.form,
    dictionaryForm: entry.dictionaryForm,
    lemma: entry.lemma,
    strong: entry.strong,
    morphologyCode: entry.morphologyCode,
    morphology: entry.morphology,
    ...(entry.evidence ? { evidence: entry.evidence } : {}),
  };
}

function lexicalClassification({ key, reason, status }) {
  if (status === 'no_greek_equivalent') return 'editorial_insertion';
  if (reason === 'unverified_greek_flexion') return 'possible_unverified_flexion';
  if (contractions.has(key)) return 'possible_contraction';
  if (auxiliaries.has(key)) return 'possible_auxiliary';
  if (commonGrammar.has(key)) return 'possible_grammatical_word';
  return 'review_synonym_or_construction';
}

function createPilot() {
  const greek = dictionary.read(rooted(greekSource)).find(chapter => chapter.chapter === CHAPTER);
  const greekVerses = new Map(greek.pericopes.flatMap(({ verses }) => verses.map(verse => [verse.verse, verse.tokens])));
  const lexicon = createLexicon(dictionary.read(dictionary.SOURCE), dictionary.read(rooted(formIndex)), {
    allowVariant: canNormalizeGreekVariant,
  });
  const { references, issues } = indexExceptions(readExceptions(), BOOK, CHAPTER, new Set(greekVerses.keys()));
  const signatures = dictionary.read(rooted(signaturesFile));
  const processed = new Map();

  function align(content, number, id) {
    const verse = readVerse(content);
    const reference = `${BOOK} ${CHAPTER}:${number}`;
    const greekTokens = greekVerses.get(number) || [];
    const { results, unidentified } = resolveVerse(
      verse, greekTokens, lexicon, reference, references, signatures[reference], key => commonGrammar.has(key),
    );
    processed.set(number, { verse, reference, results, greekTokens, unidentified });
    return renderVerse(content, verse, results, id);
  }

  function reports() {
    const totals = {
      portugueseTokens: 0, automaticallyResolved: 0, resolvedByException: 0,
      multipleAssociations: 0, noGreekEquivalent: 0, lexicalPending: 0,
      unresolvedAmbiguities: 0, exceptionsPending: 0, blockedByMarkup: 0,
      unidentifiedGreekTokens: 0, coveragePercent: 0,
    };
    const pending = new Map();
    const ambiguities = [];
    const validation = [...issues];
    const verseSignatures = {};
    const validationReferences = new Set();

    for (const data of [...processed.values()].sort((a, b) => a.reference.localeCompare(b.reference, 'pt', { numeric: true }))) {
      const { verse, reference, results, greekTokens, unidentified } = data;
      verseSignatures[reference] = verse.signature;
      totals.unidentifiedGreekTokens += unidentified.length;
      const availableGreek = greekTokens.map(token => token.lemma);
      for (const result of results) {
        const { word, key, reference: ref, position, status, reason, association, candidates, exception } = result;
        const record = { word, reference: ref, position, context: verse.text, reason, status };
        totals.portugueseTokens += 1;
        if (status === 'resolved_automatically') totals.automaticallyResolved += 1;
        if (status === 'resolved_by_exception') totals.resolvedByException += 1;
        if (status === 'no_greek_equivalent') totals.noGreekEquivalent += 1;
        if (status === 'exception_requires_review') totals.exceptionsPending += 1;
        if (association.length > 1) totals.multipleAssociations += 1;
        if (association.length && result.renderingBlocked) totals.blockedByMarkup += 1;
        if (exception) validationReferences.add(ref);

        if (status === 'pending_lexical_review' || status === 'no_greek_equivalent' ||
            (status === 'exception_requires_review' && reason === 'review_lexical_equivalence')) {
          if (status !== 'no_greek_equivalent') totals.lexicalPending += 1;
          if (!pending.has(key)) pending.set(key, []);
          pending.get(key).push({
            ...record,
            classification: lexicalClassification(result),
            suggestions: (result.suggestions || []).map(describe),
            availableGreek,
            unidentifiedGreek: unidentified,
          });
        }
        if (candidates.length > 1 || exception) {
          if (!association.length && candidates.length > 1) totals.unresolvedAmbiguities += 1;
          ambiguities.push({
            ...record,
            ambiguity: candidates.length > 1 ?
              new Set(candidates.map(entry => entry.form)).size < candidates.length ? 'greek_homograph' :
                'competing_greek_forms' : null,
            candidates: candidates.map(describe),
            exception: exception || null,
            confirmed: association.map(describe),
          });
        }
      }
    }

    for (const [reference, entry] of references) {
      if (!validationReferences.has(reference)) {
        validation.push({ reference, word: entry.word, forms: entry.forms, reason: 'position_not_found' });
        totals.exceptionsPending += 1;
      }
    }
    for (const reference of Object.keys(signatures)) {
      if (![...references.keys()].some(key => key.startsWith(reference + ':'))) {
        validation.push({ reference, reason: 'signature_without_exception' });
      }
    }
    const confirmed = totals.automaticallyResolved + totals.resolvedByException;
    if (totals.portugueseTokens) {
      totals.coveragePercent = Number((100 * confirmed / totals.portugueseTokens).toFixed(2));
    }
    return {
      'coverage.json': [...pending].sort(([a], [b]) => a.localeCompare(b, 'pt')).map(
        ([word, occurrences]) => ({ word, occurrences }),
      ),
      'ambiguities.json': { occurrences: ambiguities, validation },
      'summary.json': { reference: `${BOOK} ${CHAPTER}`, verses: processed.size, ...totals, validationIssues: validation.length, verseSignatures },
    };
  }

  function writeReports() {
    if (!processed.size) return;
    if (processed.size !== greekVerses.size || [...greekVerses.keys()].some(number => !processed.has(number))) {
      throw new Error(`Capítulo incompleto no alinhamento de ${BOOK} ${CHAPTER}`);
    }
    const folder = rooted(reportDirectory);
    fs.mkdirSync(folder, { recursive: true });
    for (const [filename, report] of Object.entries(reports())) {
      dictionary.writeIfChanged(path.join(folder, filename), dictionary.serialize(report));
    }
  }

  return { align, writeReports };
}

module.exports = { createPilot, watchPaths };
