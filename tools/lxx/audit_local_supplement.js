#!/usr/bin/env node
// Complementa apenas a auditoria: nenhuma entrada é aplicada ao interlinear.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const ROOT = path.resolve(__dirname, '../..');
const exact = value => value.normalize('NFC').toLowerCase();
const loose = value => exact(value).normalize('NFD').replace(/\p{M}/gu, '').replaceAll('ς', 'σ');
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');

function buildIndexes(lexicon) {
  const entries = [];
  const heads = [new Map(), new Map()];
  const flexions = new Map();
  function add(index, key, evidence) {
    if (!index.has(key)) index.set(key, []);
    index.get(key).push(evidence);
  }
  function visit(value, entryId, field = 'flex') {
    if (typeof value === 'string') {
      const pure = /^[\p{Script=Greek}\p{M}\s/;,·]+$/u.test(value);
      for (const word of value.match(/[\p{Script=Greek}][\p{Script=Greek}\p{M}]*/gu) || []) {
        add(flexions, loose(word), { entryId, field, value, word, mixed: !pure });
      }
    } else if (value && typeof value === 'object') {
      for (const [key, child] of Object.entries(value)) visit(child, entryId, `${field}.${key}`);
    }
  }
  for (const [group, items] of Object.entries(lexicon)) {
    if (!items || typeof items !== 'object' || Array.isArray(items)) continue;
    for (const [key, entry] of Object.entries(items)) {
      if (!entry || typeof entry !== 'object' || typeof entry.def !== 'string') continue;
      const entryId = `${group}/${key}`;
      entries.push({ entryId, group, key, ...entry });
      add(heads[0], exact(key), { entryId, field: 'key', value: key });
      add(heads[1], loose(key), { entryId, field: 'key', value: key });
      visit(entry.flex, entryId);
    }
  }
  return { entries, heads, flexions };
}

function findCandidates(record, indexes) {
  for (const [index, normalize, status] of [
    [indexes.heads[0], exact, 'lemma_accented'],
    [indexes.heads[1], loose, 'lemma_unaccented'],
  ]) {
    const evidence = record.lemma ? index.get(normalize(record.lemma)) : null;
    if (evidence?.length) return { status, evidence };
  }
  const head = indexes.heads[1].get(loose(record.form));
  if (head?.length) return { status: 'surface_head_only', evidence: head };
  const flex = indexes.flexions.get(loose(record.form));
  if (flex?.length) return {
    status: flex.some(item => !item.mixed) ? 'surface_flex_only' : 'surface_mixed_only', evidence: flex,
  };
  return { status: 'not_found', evidence: [] };
}

function audit({ input, lexicon, output }) {
  const previous = JSON.parse(fs.readFileSync(input, 'utf8'));
  const local = JSON.parse(fs.readFileSync(lexicon, 'utf8'));
  const indexes = buildIndexes(local);
  const records = previous.records.filter(record => record.status === 'not_found').map(record => {
    const match = findCandidates(record, indexes);
    const entryIds = [...new Set(match.evidence.map(item => item.entryId))];
    return { ...record, tbesg_status: record.status, ...match, candidate_entry_ids: entryIds,
      weak_surface_match: match.status.startsWith('surface_'),
      proper_name_surface_collision: record.pos === 'proper noun' && match.status.startsWith('surface_'),
      ambiguity: entryIds.length > 1, review: match.evidence.length ? 'INCERTO' : 'INFORMACAO_INSUFICIENTE' };
  });
  const summary = { inputGroups: records.length, inputOccurrences: 0, inputForms: new Set(records.map(r => r.form)).size, matches: {} };
  const used = new Set();
  for (const record of records) {
    summary.inputOccurrences += record.occurrences;
    summary.matches[record.status] ||= { groups: 0, occurrences: 0, multipleGroups: 0 };
    const category = summary.matches[record.status];
    category.groups++;
    category.occurrences += record.occurrences;
    if (record.ambiguity) category.multipleGroups++;
    record.candidate_entry_ids.forEach(id => used.add(id));
  }
  const result = {
    source: { file: path.relative(ROOT, lexicon), sha256: hash(lexicon), declared_origin: local.fonte,
      tbesg_report_sha256: hash(input), entries: indexes.entries.length },
    method: 'Somente registros not_found da auditoria TBESG. Prioridade: chave pelo lema com diacríticos; chave pelo lema sem diacríticos; forma textual como chave; forma textual extraída de flex. Resultados por forma são indícios fracos e não identificam o lema. Duplicatas de grupos são preservadas. Nenhuma tradução ou análise morfológica aprovada/aplicada.',
    summary, lexicon: indexes.entries.filter(entry => used.has(entry.entryId)), records,
  };
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
  return result;
}

if (require.main === module) {
  const input = path.join(ROOT, 'tools/relatorios/lxx-tbesg-cobertura.json');
  const lexicon = path.join(ROOT, 'src/_data/lxx/lexico_lxx_gr-pt-heb.json');
  const output = path.join(ROOT, 'tools/relatorios/lxx-lexico-complementar.json');
  try { console.log(JSON.stringify(audit({ input, lexicon, output }).summary, null, 2)); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = { buildIndexes, findCandidates, audit };
