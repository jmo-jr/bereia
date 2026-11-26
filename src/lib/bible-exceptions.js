const fs = require('node:fs');
const path = require('node:path');
const { words, canonicalGreek } = require('./bible-lexical-text');
const { reconcile } = require('./bible-reconcile');
function loadExceptions(root) {
  const filename = path.join(root, 'src/tooltip-exceptions.json');
  const data = fs.existsSync(filename) ? JSON.parse(fs.readFileSync(filename, 'utf8')) : { version: 1, verses: {} };
  if (data.version !== 1 || !data.verses || Array.isArray(data.verses)) throw Error('JSON de exceções inválido.');
  for (const [reference, verse] of Object.entries(data.verses)) {
    if (!/^[a-z0-9]+ [1-9]\d*:[1-9]\d*$/u.test(reference) || typeof verse.portuguese !== 'string' || !Array.isArray(verse.greek) || verse.greek.some(form => typeof form !== 'string') || !Array.isArray(verse.associations)) throw Error(`Âncora de exceção inválida: ${reference}.`);
    const tokens = words(verse.portuguese);
    let end = 0;
    for (const item of verse.associations) {
      const start = tokens[item.position - 1]?.start;
      if (!Number.isSafeInteger(item.position) || start === undefined || start < end || !item.text || verse.portuguese.slice(start, start + item.text.length) !== item.text || tokens.some(word => start + item.text.length > word.start && start + item.text.length < word.end)) throw Error(`Posição/trecho não confere com a âncora: ${reference}.`);
      end = start + item.text.length;
      if (item.suppress === true) continue;
      if (!Array.isArray(item.groups) || !item.groups.length) throw Error(`Grupos ausentes na exceção: ${reference}.`);
      for (const group of item.groups) {
        if (!Array.isArray(group.tokens) || !group.tokens.length || new Set(group.tokens).size !== group.tokens.length || group.tokens.some(position => !Number.isSafeInteger(position) || position < 1 || position > verse.greek.length)) throw Error(`Token grego inválido na exceção: ${reference}.`);
        if (group.dictionaryKeys && (group.dictionaryKeys.length !== group.tokens.length || group.dictionaryKeys.some((key, index) => typeof key !== 'string' || canonicalGreek(key) !== canonicalGreek(verse.greek[group.tokens[index] - 1])))) throw Error(`Análise grega incompatível na exceção: ${reference}.`);
      }
    }
    for (const position of verse.ignoreGreek || []) if (!Number.isSafeInteger(position) || position < 1 || position > verse.greek.length) throw Error(`Token ignorado inválido: ${reference}.`);
  }
  return data;
}
function resolveExceptions(data, reference, text, greek, lexicon) {
  const entry = data.verses[reference];
  if (!entry) return { matches: [], suppressed: [], excludedTokens: new Set(), issues: [], relocated: 0 };
  const stale = reason => ({ matches: [], suppressed: [], excludedTokens: new Set(), issues: [reason], relocated: 0 });
  if (JSON.stringify(entry.greek) !== JSON.stringify(greek)) return stale('Exceção não aplicada: a sequência grega mudou em relação à âncora persistente.');
  if (JSON.stringify(words(entry.portuguese).map(word => word.value)) !== JSON.stringify(words(text).map(word => word.value))) return stale('Exceção não aplicada: as palavras portuguesas mudaram em relação à âncora persistente. A posição existente não basta para confirmá-la.');
  const sourceWords = words(entry.portuguese);
  const segments = entry.associations.map((item, index) => ({ start: sourceWords[item.position - 1].start, text: item.text, tokens: [], association: index }));
  const moved = reconcile({ text: entry.portuguese, segments }, text);
  const matches = [], suppressed = [], issues = [];
  for (const pending of moved.pending.filter(item => Number.isInteger(item.index))) issues.push(`Exceção não aplicada ao trecho “${pending.text}”: posição ou conteúdo ficou incerto.`);
  for (const segment of moved.segments) {
    const item = entry.associations[segment.association];
    if (item.suppress) { suppressed.push({ start: segment.start, end: segment.start + segment.text.length }); continue; }
    const candidates = [];
    for (const group of item.groups) {
      const forms = group.tokens.map(position => greek[position - 1]);
      const keys = group.dictionaryKeys || forms;
      if (keys.some((key, index) => !Object.hasOwn(lexicon.dictionary, key) && (lexicon.analysisIndex.get(canonicalGreek(forms[index])) || []).length > 1)) {
        issues.push(`Exceção “${item.text}” exige dictionaryKeys para distinguir análises homógrafas.`);
        continue;
      }
      candidates.push({ forms, dictionaryForms: keys, occurrences: [group.tokens] });
    }
    if (candidates.length) matches.push({ term: segment.text.toLocaleLowerCase('pt-BR'), start: segment.start, end: segment.start + segment.text.length, text: segment.text, candidates, confirmed: true });
  }
  return { matches, suppressed, excludedTokens: new Set(entry.ignoreGreek || []), issues, relocated: moved.segments.filter(segment => segment.start !== segments[segment.association].start).length };
}
module.exports = { loadExceptions, resolveExceptions };
