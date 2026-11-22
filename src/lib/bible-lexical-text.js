const canonicalGreek = value => String(value).toLowerCase().normalize('NFD').replace(/\u0300/g, '\u0301').normalize('NFC');
const looseGreek = value => canonicalGreek(value).normalize('NFD').replace(/\p{M}/gu, '');
const normalizePortuguese = text => String(text).normalize('NFC').toLocaleLowerCase('pt-BR').trim().replace(/\s+/gu, ' ');
const words = text => [...text.matchAll(/[\p{L}\p{N}][\p{L}\p{M}\p{N}]*/gu)].map(match => ({
  value: match[0].normalize('NFC').toLocaleLowerCase('pt-BR'), start: match.index, end: match.index + match[0].length,
}));

function phrases(value) {
  if (typeof value !== 'string' || /[()[\]{}]/u.test(value)) return [];
  // Do not expand grammatical notation such as eu/ele(a), bracketed text or gloss notes.
  return [...new Set(value.split(/[,;/]/u).map(part => part.trim()).filter(part =>
    part && part.length <= 120 && !(value.includes('/') && /^(eu|tu|ele|ela|nós|vós|vocês|eles|elas)$/iu.test(part)) && !/[()[\]{}:=\d]/u.test(part) && /^[\p{L}\p{M}\s’'–-]+$/u.test(part)))];
}

module.exports = { canonicalGreek, looseGreek, normalizePortuguese, words, phrases };
