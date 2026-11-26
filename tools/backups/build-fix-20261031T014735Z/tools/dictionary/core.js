const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '../..');
const SOURCE = path.join(ROOT, 'src/_data/dict_lex_nt-lxx_greek-pt.json');
const DERIVED = path.join(ROOT, 'src/_data/dict_flex_nt-lxx_greek-pt.json');
const BACKUP = path.join(ROOT, 'tools/backups/dictionary-migration/dict_flex_nt-lxx_greek-pt.json');
const FIELDS = ['strongs', 'grego', 'transliteracao', 'verbete', 'ocorrencias',
  'traducao', 'pt', 'abrev_morf', 'morfologia', 'lxx', 'ocorrencias_lxx'];
const FLEX_FIELDS = FIELDS.filter(field => field !== 'strongs' && field !== 'verbete');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const serialize = value => JSON.stringify(value, null, 2) + '\n';
const compareStrong = (a, b) => Number(a) - Number(b) || a.localeCompare(b, 'en');

// JS enumerates integer keys first. Explicit serialization keeps identifiers
// with original whitespace beside their numeric peers in the lexical file.
function serializeLexicon(lexicon) {
  return '{\n' + Object.keys(lexicon).sort(compareStrong).map(key =>
    `  ${JSON.stringify(key)}: ${JSON.stringify(lexicon[key], null, 2).replaceAll('\n', '\n  ')}`,
  ).join(',\n') + '\n}\n';
}

function fixedEntry(entry) {
  for (const field of Object.keys(entry)) assert(FIELDS.includes(field), `Campo desconhecido: ${field}`);
  return Object.fromEntries(FIELDS.map(field => {
    const value = field === 'ocorrencias_lxx' && !Object.hasOwn(entry, field) ? 0 : entry[field];
    assert(value !== undefined, `Campo obrigatório ausente: ${field}`);
    return [field, value];
  }));
}

function migrate(original, lexical) {
  const result = Object.create(null);
  for (const entry of Object.values(original)) {
    const strong = entry.strongs;
    assert.equal(typeof strong, 'string');
    // Exact identifiers only: no trimming or inferred Strong.
    const metadata = /^\d+$/.test(strong) ? lexical['G' + strong] : undefined;
    if (!Object.hasOwn(result, strong)) {
      const pendencias = [
        ...(!metadata?.lemma ? ['Identificação lexical pendente; Strong original preservado.'] : []),
        ...(metadata && !metadata.translit ? ['Transliteração lexical ausente na fonte.'] : []),
      ];
      result[strong] = {
        lema: metadata?.lemma || null,
        transliteracao: metadata?.translit || null,
        ...(pendencias.length ? { pendencias } : {}),
        verbetes: [],
        flexoes: [],
      };
    }
    const group = result[strong];
    if (!group.verbetes.includes(entry.verbete)) group.verbetes.push(entry.verbete);
    const full = fixedEntry(entry);
    const flex = Object.fromEntries(FLEX_FIELDS.map(field => [field, full[field]]));
    flex.verbete = full.verbete;
    group.flexoes.push(flex);
  }
  for (const [strong, group] of Object.entries(result)) {
    if (group.verbetes.length === 1) {
      const { verbetes, flexoes, ...lexicalFields } = group;
      for (const flex of flexoes) delete flex.verbete;
      result[strong] = { ...lexicalFields, verbete: verbetes[0], flexoes };
    }
  }
  return result;
}

// Full list, including every homograph and repeated analysis. No ordering or
// original-key metadata is needed to reconstruct each complete record.
function records(lexicon) {
  const rows = [];
  for (const [strong, group] of Object.entries(lexicon)) {
    assert(Array.isArray(group.flexoes), `Flexões inválidas: ${strong}`);
    assert(!Object.hasOwn(group, 'origem_lexical'), 'Metadado lexical obsoleto');
    if (Object.hasOwn(group, 'pendencias')) assert(Array.isArray(group.pendencias) && group.pendencias.length, 'Pendências vazias');
    const common = Object.hasOwn(group, 'verbete');
    assert(common !== Object.hasOwn(group, 'verbetes'), `Defina verbete ou verbetes: ${strong}`);
    if (!common) assert(Array.isArray(group.verbetes) && group.verbetes.length > 1, `Variantes inválidas: ${strong}`);
    for (const flex of group.flexoes) {
      for (const field of Object.keys(flex)) {
        assert(FLEX_FIELDS.includes(field) || (!common && field === 'verbete'), `Campo de flexão desconhecido: ${field}`);
      }
      for (const field of FLEX_FIELDS) assert(Object.hasOwn(flex, field), `Campo obrigatório ausente: ${strong}/${field}`);
      assert(typeof flex.grego === 'string' && flex.grego.length, 'Forma grega inválida');
      const verbete = common ? group.verbete : flex.verbete;
      assert.equal(typeof verbete, 'string', `Verbete ausente: ${strong}/${flex.grego}`);
      if (!common) assert(group.verbetes.includes(verbete), 'Verbete não registrado no grupo');
      rows.push(fixedEntry({ strongs: strong, ...flex, verbete }));
    }
  }
  return rows;
}

function flatten(lexicon) {
  const dict = Object.create(null);
  // Compatibility projection: first encountered analysis per exact Greek form.
  // All other analyses remain in the lexical source and its form index.
  for (const entry of records(lexicon)) {
    if (!Object.hasOwn(dict, entry.grego)) dict[entry.grego] = entry;
  }
  return dict;
}

function buildFormIndex(lexicon) {
  const index = Object.create(null);
  for (const [strong, group] of Object.entries(lexicon)) {
    group.flexoes.forEach((flex, flexao) => {
      (index[flex.grego] ||= []).push({ strongs: strong, flexao });
    });
  }
  return index;
}

function writeIfChanged(file, content) {
  if (fs.existsSync(file) && fs.readFileSync(file, 'utf8') === content) return false;
  const temporary = file + '.tmp';
  fs.writeFileSync(temporary, content, 'utf8');
  fs.renameSync(temporary, file);
  return true;
}

module.exports = { ROOT, SOURCE, DERIVED, BACKUP, FIELDS, FLEX_FIELDS, read, serialize,
  serializeLexicon, fixedEntry, migrate, records, flatten, buildFormIndex, writeIfChanged };
