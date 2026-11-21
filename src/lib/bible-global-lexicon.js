const fs = require('node:fs');
const path = require('node:path');
const { buildIndex } = require('../../tools/bible-reverse-index');
const { canonicalGreek, normalizePortuguese, words } = require('../../tools/bible-proposals/lexical');
const ROOT = path.resolve(__dirname, '../..');
function resolve(dictionary, rules) {
  if (rules.version !== 1 || !['alternatives', 'omit'].includes(rules.ambiguityPolicy) || !rules.entries || Array.isArray(rules.entries)) throw Error('Fonte global de tooltips inválida.');
  const index = buildIndex(dictionary, 'build');
  const terms = new Map(Object.entries(index.terms).map(([term, references]) => [term, {
    forms: [...new Set(references.map(reference => reference.dictionaryKey))], groups: [], enabled: true, origin: 'dicionário', note: '',
  }]));
  for (const [term, entry] of Object.entries(rules.entries)) {
    if (normalizePortuguese(term) !== term || !words(term).length) throw Error(`Termo global inválido: ${term}.`);
    if (entry.forms !== undefined && (!Array.isArray(entry.forms) || entry.forms.some(form => typeof form !== 'string' || !form))) throw Error(`Formas inválidas: ${term}.`);
    if (entry.groups !== undefined && (!Array.isArray(entry.groups) || entry.groups.some(group => !Array.isArray(group) || group.length < 2 || group.some(form => typeof form !== 'string' || !form)))) throw Error(`Grupos inválidos: ${term}.`);
    if (entry.enabled !== undefined && typeof entry.enabled !== 'boolean') throw Error(`Estado inválido: ${term}.`);
    const previous = terms.get(term);
    const extend = entry.mode === 'extend';
    const forms = [...new Set([...(extend ? previous?.forms || [] : []), ...(entry.forms || [])])];
    const groups = [...new Map([...(extend ? previous?.groups || [] : []), ...(entry.groups || [])].map(group => [JSON.stringify(group), group])).values()];
    terms.set(term, { forms, groups, enabled: entry.enabled !== false, origin: entry.origin || 'fonte global', note: entry.note || '' });
  }
  return { terms, ambiguityPolicy: rules.ambiguityPolicy, pendingIndex: index.pending };
}
function load(root = ROOT) {
  const dictionary = JSON.parse(fs.readFileSync(path.join(root, 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json'), 'utf8'));
  const rules = JSON.parse(fs.readFileSync(path.join(root, 'src/tooltip-relations.json'), 'utf8'));
  return { dictionary, rules, ...resolve(dictionary, rules) };
}
function findMatches(text, greek, lexicon, excludedTokens = new Set()) {
  const pt = words(text), supplied = [...text.matchAll(/\[[^\]]*\]/gu)].map(match => [match.index, match.index + match[0].length]);
  const maxWords = lexicon.maxWords || (lexicon.maxWords = [...lexicon.terms.keys()].reduce((max, term) => Math.max(max, words(term).length), 1));
  const results = [];
  for (let i = 0; i < pt.length;) {
    let selected;
    for (let length = Math.min(maxWords, pt.length - i); length >= 1; length--) {
      const start = pt[i].start, end = pt[i + length - 1].end;
      if (supplied.some(([from, to]) => start < to && from < end)) continue;
      const term = normalizePortuguese(text.slice(start, end)), entry = lexicon.terms.get(term);
      if (!entry?.enabled) continue;
      const candidates = new Map();
      const patterns = [...entry.forms.map(form => [form]), ...entry.groups];
      for (const pattern of patterns) for (let position = 0; position <= greek.length - pattern.length; position++) {
        if (!pattern.every((form, index) => !excludedTokens.has(position + index + 1) && canonicalGreek(form) === canonicalGreek(greek[position + index]))) continue;
        const forms = greek.slice(position, position + pattern.length), key = pattern.map(canonicalGreek).join('\u0000');
        if (!candidates.has(key)) candidates.set(key, { forms, dictionaryForms: pattern, occurrences: [] });
        candidates.get(key).occurrences.push(pattern.map((_, index) => position + index + 1));
      }
      if (!candidates.size) continue;
      selected = { term, start, end, text: text.slice(start, end), length, candidates: [...candidates.values()] };
      break;
    }
    if (selected) { results.push(selected); i += selected.length; }
    else i++;
  }
  return results;
}
module.exports = { ROOT, resolve, load, findMatches, canonicalGreek, normalizePortuguese };
