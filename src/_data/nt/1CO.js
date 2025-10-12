const data = require('../../interlinear/nt/1CO.json');
const dict = require('../greeknt_dict.json');

// TODO: Trazer `grego` de dict (depois de eliminar duplicatas)
const DICT_FIELDS = ['transliteracao', 'traducao', 'verbete', 'desgram', 'ocorrencia', 'grego'];

const normalizeGreek = (value = '') =>
  value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();

const dictIndex = Object.entries(dict).reduce((acc, [key, entry]) => {
  const normalizedKey = normalizeGreek(key);
  if (normalizedKey && !acc[normalizedKey]) {
    acc[normalizedKey] = entry;
  }
  return acc;
}, {});

const enhanceTokenWithDict = (token = {}) => {
  const normalized = normalizeGreek(token.greek || '');
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

module.exports = () => {
  return data.map(chapterEntry => {
    const pericopes = (chapterEntry.pericopes || []).map(pericope => {
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
    });

    const verses = pericopes.flatMap(pericope => pericope.verses);

    return {
      number: Number(chapterEntry.chapter),
      pericopes,
      verses,
    };
  });
};

//console.log(JSON.stringify(data[0], null, 2));
