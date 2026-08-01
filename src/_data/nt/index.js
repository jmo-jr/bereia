const fs = require('fs');
const path = require('path');

const DICT_PATH = path.join(__dirname, '..', 'nt_greek-pt_dict.json');
const SOURCE_DIR = path.join(__dirname, '..', '..', 'interlinear', 'nt');

const DICT_FIELDS = ['strongs', 'grego', 'transliteracao', 'verbete', 'ocorrencias', 'traducao', 'pt', 'morfologia', 'abrev_morf' ];

// Terms that should keep diacritics to avoid collapsing homographs.
const NORMALIZATION_EXCEPTIONS = new Set(["α", "εν", "η", "ης", "ην", "ητε", "ου", "ει", "ως", "ο", "ος", "αν", "τις", "που", "πως", "αυτου", "αυτη", "δη", "ανω", "ημερα", "εκτος", "τι" "εις"]);

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

const createEnhanceTokenWithDict = dict => {
  const dictIndex = buildDictIndex(dict);

  return (token = {}) => {
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
};

const normalizePericope = (pericope = {}, enhanceTokenWithDict) => {
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

const normalizeBookData = (bookContent = [], enhanceTokenWithDict) =>
  bookContent.map(chapterEntry => {
    const pericopes = (chapterEntry.pericopes || []).map(pericope =>
      normalizePericope(pericope, enhanceTokenWithDict),
    );
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

  const dict = loadJsonFile(DICT_PATH);
  const enhanceTokenWithDict = createEnhanceTokenWithDict(dict);

  return fs
    .readdirSync(SOURCE_DIR)
    .filter(filename => filename.toLowerCase().endsWith('.json'))
    .reduce((acc, filename) => {
      const bookId = path.basename(filename, path.extname(filename));
      const rawContent = loadJsonFile(path.join(SOURCE_DIR, filename));

      acc[bookId] = normalizeBookData(rawContent, enhanceTokenWithDict);
      return acc;
    }, {});
};

module.exports = loadAllBooks;
