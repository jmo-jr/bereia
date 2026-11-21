const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { load, ROOT, resolve, canonicalGreek, normalizePortuguese } = require('../../src/lib/bible-global-lexicon');
const { encode, parse } = require('../bible-review/csv');
const { setValue } = require('../bible-review/json-patch');
const { safeOutput } = require('../bible-proposals/generate');
const hash = text => crypto.createHash('sha256').update(text).digest('hex');
const COLUMNS = ['termo_pt', 'formas_gregas', 'grupos_gregos', 'ativo', 'observacao', 'origem', 'id'];
const row = (term, entry) => ({ termo_pt: term, formas_gregas: entry.forms.join(' | '), grupos_gregos: entry.groups.map(group => group.join(' + ')).join(' || '),
  ativo: entry.enabled ? 'sim' : 'não', observacao: entry.note, origem: entry.origin, id: 't-' + hash(term).slice(0, 24) });
function exportGlobal({ root = ROOT, file = path.join(root, 'reports/bible-global.csv') } = {}) {
  const lexicon = load(root), rows = [...lexicon.terms].sort(([a], [b]) => a.localeCompare(b, 'pt-BR')).map(([term, entry]) => row(term, entry));
  const snapshot = { version: 1, rulesHash: hash(fs.readFileSync(path.join(root, 'src/tooltip-relations.json'))), dictionaryHash: hash(fs.readFileSync(path.join(root, 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json'))), rows };
  const plans = [[file, encode([COLUMNS, ...rows.map(item => COLUMNS.map(name => item[name]))])], [file.replace(/\.csv$/iu, '') + '.global.json', JSON.stringify(snapshot, null, 2) + '\n']];
  for (const [filename, content] of plans) {
    safeOutput(root, path.dirname(filename));
    if (fs.existsSync(filename) && (fs.lstatSync(filename).isSymbolicLink() || fs.readFileSync(filename, 'utf8') !== content)) throw Error(`Arquivo global existente preservado: ${filename}. Use --file com outro nome.`);
  }
  for (const [filename, content] of plans) { fs.mkdirSync(path.dirname(filename), { recursive: true }); if (!fs.existsSync(filename)) fs.writeFileSync(filename, content); }
  return { file, terms: rows.length };
}
function importGlobal({ root = ROOT, file, apply = false } = {}) {
  if (!file || !/\.csv$/iu.test(file)) throw Error('Informe --file com o CSV global.');
  const snapshot = JSON.parse(fs.readFileSync(file.replace(/\.csv$/iu, '') + '.global.json', 'utf8'));
  const target = path.join(root, 'src/tooltip-relations.json'), before = fs.readFileSync(target, 'utf8');
  if (snapshot.version !== 1 || hash(before) !== snapshot.rulesHash || hash(fs.readFileSync(path.join(root, 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json'))) !== snapshot.dictionaryHash) throw Error('Fonte global ou dicionário mudou. Exporte outra rodada e preserve sua revisão.');
  let rows;
  for (const delimiter of [';', ',']) {
    try { const data = parse(fs.readFileSync(file, 'utf8'), delimiter); if (data[0]?.length === COLUMNS.length && COLUMNS.every(name => data[0].includes(name)) && new Set(data[0]).size === COLUMNS.length) { rows = data.slice(1).map(cells => { if (cells.length !== COLUMNS.length) throw Error('Campos CSV inválidos.'); return Object.fromEntries(data[0].map((name, index) => [name, cells[index]])); }); break; } } catch { /* separator */ }
  }
  if (!rows) throw Error('CSV global inválido; preserve as colunas e UTF-8.');
  const originals = new Map(snapshot.rows.map(item => [item.id, item])), rules = JSON.parse(before), changed = [], ids = new Set(), terms = new Set();
  for (const item of rows) {
    const term = normalizePortuguese(item.termo_pt);
    if (!term || terms.has(term)) throw Error(`Termo vazio ou duplicado: ${term}.`);
    terms.add(term);
    const original = originals.get(item.id);
    if (item.id && (!original || ids.has(item.id))) throw Error('Id global desconhecido ou duplicado. Para adicionar termo, deixe id/origem vazios.');
    if (item.id) ids.add(item.id);
    if (original && item.origem !== original.origem) throw Error('A coluna origem é apenas referência.');
    if (!original && item.origem) throw Error('Novo termo deve ter origem vazia.');
    if (original && COLUMNS.every(name => item[name] === original[name])) continue;
    const forms = item.formas_gregas ? original && item.formas_gregas === original.formas_gregas ? item.formas_gregas.split(' | ') : item.formas_gregas.split('|').map(form => form.trim()) : [];
    const groups = item.grupos_gregos ? original && item.grupos_gregos === original.grupos_gregos ? item.grupos_gregos.split(' || ').map(group => group.split(' + ')) : item.grupos_gregos.split('||').map(group => group.split('+').map(form => form.trim())) : [];
    const enabled = /^(sim|true|1)$/iu.test(item.ativo.trim());
    if (!enabled && !/^(não|nao|false|0)$/iu.test(item.ativo.trim())) throw Error(`Estado inválido para ${term}: use sim ou não.`);
    if (enabled && !forms.length && !groups.length) throw Error(`${term}: informe forma ou grupo grego.`);
    if (original && normalizePortuguese(original.termo_pt) !== term) rules.entries[normalizePortuguese(original.termo_pt)] = { ...(rules.entries[normalizePortuguese(original.termo_pt)] || {}), mode: 'replace', enabled: false };
    rules.entries[term] = { ...(rules.entries[term] || {}), forms, groups, enabled, mode: 'replace', origin: 'revisão global', note: item.observacao };
    changed.push(term);
  }
  const { dictionary } = load(root);
  resolve(dictionary, rules);
  const known = new Set(Object.keys(dictionary).map(canonicalGreek));
  const directory = path.join(root, 'src/interlinear/nt');
  if (fs.existsSync(directory)) for (const name of fs.readdirSync(directory).filter(name => name.endsWith('.json'))) {
    for (const chapter of JSON.parse(fs.readFileSync(path.join(directory, name), 'utf8'))) for (const pericope of chapter.pericopes || []) for (const verse of pericope.verses || []) for (const token of verse.tokens || []) known.add(canonicalGreek(token.lemma));
  }
  for (const term of changed) for (const form of [...rules.entries[term].forms, ...rules.entries[term].groups.flat()]) if (!known.has(canonicalGreek(form))) throw Error(`Forma grega não encontrada no dicionário/TM: ${form}.`);
  let content = before;
  const originalRules = JSON.parse(before);
  for (const [term, entry] of Object.entries(rules.entries)) if (JSON.stringify(originalRules.entries[term]) !== JSON.stringify(entry)) content = setValue(content, ['entries', term], entry);
  if (apply && content !== before) {
    if (fs.lstatSync(target).isSymbolicLink()) throw Error('Fonte global não pode ser link simbólico.');
    if (hash(fs.readFileSync(target)) !== snapshot.rulesHash) throw Error('Fonte global mudou durante a validação.');
    fs.writeFileSync(target, content);
  }
  return { applied: apply && content !== before, changedTerms: changed.length, terms: changed, file: 'src/tooltip-relations.json' };
}
function seed({ root = ROOT } = {}) {
  const lexicon = load(root), rules = lexicon.rules;
  if (Object.keys(rules.entries).length) throw Error('Fonte global existente preservada; a inicialização só vale para entries vazio.');
  const folder = path.join(root, 'src/alinhamentos');
  if (fs.existsSync(folder)) for (const book of fs.readdirSync(folder)) {
    const directory = path.join(folder, book); if (!fs.statSync(directory).isDirectory()) continue;
    for (const name of fs.readdirSync(directory).filter(name => name.endsWith('.json'))) {
      const data = JSON.parse(fs.readFileSync(path.join(directory, name), 'utf8'));
      for (const entry of Object.values(data.verses)) for (const segment of entry.segments) {
        if (!segment.tokens.length || segment.tokens.some((position, index) => index && position !== segment.tokens[index - 1] + 1)) continue;
        const forms = segment.tokens.map(position => entry.greek[position - 1]);
        for (const label of [segment.text, ...(segment.alternatives || [])]) {
          const term = normalizePortuguese(label), base = lexicon.terms.get(term);
          if (forms.length === 1 && base?.forms.some(form => canonicalGreek(form) === canonicalGreek(forms[0]))) continue;
          const rule = rules.entries[term] ||= { forms: [], groups: [], mode: 'extend', origin: 'expressão cadastrada', note: '' };
          if (forms.length === 1) { if (!rule.forms.includes(forms[0])) rule.forms.push(forms[0]); }
          else if (!rule.groups.some(group => JSON.stringify(group) === JSON.stringify(forms))) rule.groups.push(forms);
        }
      }
    }
  }
  fs.writeFileSync(path.join(root, 'src/tooltip-relations.json'), JSON.stringify(rules, null, 2) + '\n');
  return { seeded: Object.keys(rules.entries).length };
}
if (require.main === module) {
  try {
    const args = process.argv.slice(2), mode = args.shift(), options = {};
    for (let i = 0; i < args.length; i++) { if (args[i] === '--apply') options.apply = true; else if (args[i] === '--file' && args[i + 1]) options.file = path.resolve(args[++i]); else throw Error('Use --file caminho.csv e, para importar, --apply.'); }
    console.log(JSON.stringify(mode === 'export' ? exportGlobal(options) : mode === 'import' ? importGlobal(options) : mode === 'seed' ? seed(options) : (() => { throw Error('Use export ou import.'); })(), null, 2));
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = { COLUMNS, exportGlobal, importGlobal, seed };
