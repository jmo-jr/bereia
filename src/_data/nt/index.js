const fs = require('fs');
const path = require('path');

const dict = require('../new_greeknt_dict.json');

const SOURCE_DIR = path.join(__dirname, '..', '..', 'interlinear', 'nt');

const DICT_FIELDS = ['transliteracao', 'traducao', 'verbete', 'desgram', 'classegram', 'ocorrencia', 'grego', 'strongs'];

const normalizeGreek = (value = '') =>
  value
    // .normalize('NFD')
    // .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();

const dictIndex = Object.entries(dict).reduce((acc, [key, entry]) => {
  const normalizedKey = normalizeGreek(key);
  if (normalizedKey && !acc[normalizedKey]) {
    acc[normalizedKey] = entry;
  }
  return acc;
}, {});

const enhanceTokenWithDict = (token = {}) => {
  const normalized = normalizeGreek(token.lemma || '');
  const dictEntry = dictIndex[normalized];

  if (!dictEntry) {
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

const normalizePericope = (pericope = {}) => {
  const verses = (pericope.verses || []).map(verseEntry => ({
    number: Number(verseEntry.verse),
    tokens: (verseEntry.tokens || []).map(enhanceTokenWithDict),
  }));

  return {
    ...pericope,
    start_verse: pericope.start_verse !== undefined ? Number(pericope.start_verse) : undefined,
    end_verse: pericope.end_verse !== undefined ? Number(pericope.end_verse) : undefined,
    verses,
  };
};

const normalizeBookData = (bookContent = []) =>
  bookContent.map(chapterEntry => {
    const pericopes = (chapterEntry.pericopes || []).map(normalizePericope);
    const verses = pericopes.flatMap(pericope => pericope.verses);

    return {
      number: Number(chapterEntry.chapter),
      pericopes,
      verses,
    };
  });

const loadAllBooks = () => {
  if (!fs.existsSync(SOURCE_DIR)) {
    return {};
  }

  return fs
    .readdirSync(SOURCE_DIR)
    .filter(filename => filename.toLowerCase().endsWith('.json'))
    .reduce((acc, filename) => {
      const bookId = path.basename(filename, path.extname(filename));
      const rawContent = require(path.join(SOURCE_DIR, filename));

      acc[bookId] = normalizeBookData(rawContent);
      return acc;
    }, {});
};

module.exports = loadAllBooks;
