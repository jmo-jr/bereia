const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '../..');
const SOURCE = path.join(ROOT, 'src/_data/dict_lex_nt-lxx_greek-pt.json');
const DERIVED = path.join(ROOT, 'src/_data/dict_flex_nt-lxx_greek-pt.json');
const BACKUP = path.join(ROOT, 'tools/backups/dictionary-migration/dict_flex_nt-lxx_greek-pt.json');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const serialize = value => JSON.stringify(value, null, 2) + '\n';
const compareStrong = (a, b) => Number(a) - Number(b) || a.localeCompare(b, 'en');

// Integer-like JS keys are enumerated before other keys. Serialize explicitly
// so identifiers with original whitespace remain beside their numeric peers.
function serializeLexicon(lexicon) {
  return '{\n' + Object.keys(lexicon).sort(compareStrong).map(key =>
    `  ${JSON.stringify(key)}: ${JSON.stringify(lexicon[key], null, 2).replaceAll('\n', '\n  ')}`,
  ).join(',\n') + '\n}\n';
}

function migrate(original, lexical) {
  const result = Object.create(null);
  Object.entries(original).forEach(([key, entry], order) => {
    const strong = entry.strongs;
    assert.equal(typeof strong, 'string');
    // Exact identifiers only: no trimming, normalization or inferred Strong.
    const metadata = /^\d+$/.test(strong) ? lexical['G' + strong] : undefined;
    if (!Object.hasOwn(result, strong)) {
      result[strong] = {
        lema: metadata?.lemma || null,
        transliteracao: metadata?.translit || null,
        origem_lexical: metadata ? 'src/_data/archive/strongsg.js' : null,
        pendencias: [
          ...(!metadata?.lemma ? ['Identificação lexical pendente; Strong original preservado.'] : []),
          ...(metadata && !metadata.translit ? ['Transliteração lexical ausente na fonte.'] : []),
        ],
        verbetes: [],
        flexoes: [],
      };
    }
    const group = result[strong];
    let variant = group.verbetes.indexOf(entry.verbete);
    if (variant === -1) variant = group.verbetes.push(entry.verbete) - 1;
    const flex = {};
    for (const [field, value] of Object.entries(entry)) {
      if (field !== 'strongs' && field !== 'verbete') flex[field] = value;
    }
    flex._origem = { chave: key, ordem: order, campos: Object.keys(entry), verbete: variant };
    group.flexoes.push(flex);
  });
  for (const group of Object.values(result)) {
    if (group.verbetes.length === 1) {
      group.verbete = group.verbetes[0];
      delete group.verbetes;
      for (const flex of group.flexoes) delete flex._origem.verbete;
    }
  }
  return result;
}

function flatten(lexicon) {
  const rows = [];
  const keys = new Set();
  const orders = new Set();
  for (const [strong, group] of Object.entries(lexicon)) {
    assert(Array.isArray(group.flexoes), `Flexões inválidas: ${strong}`);
    for (const flex of group.flexoes) {
      const origin = flex._origem;
      assert(origin && typeof origin.chave === 'string', `Origem ausente: ${strong}`);
      assert(Number.isSafeInteger(origin.ordem) && origin.ordem >= 0, 'Ordem inválida');
      assert(!keys.has(origin.chave), `Chave duplicada: ${origin.chave}`);
      assert(!orders.has(origin.ordem), `Ordem duplicada: ${origin.ordem}`);
      keys.add(origin.chave); orders.add(origin.ordem);
      const entry = Object.create(null);
      const fields = origin.campos;
      assert(Array.isArray(fields) && new Set(fields).size === fields.length, 'Campos inválidos');
      for (const field of fields) {
        if (field === 'strongs') entry[field] = strong;
        else if (field === 'verbete') {
          entry[field] = Object.hasOwn(group, 'verbete') ? group.verbete : group.verbetes?.[origin.verbete];
          assert.equal(typeof entry[field], 'string', 'Referência de verbete inválida');
        } else {
          assert(Object.hasOwn(flex, field), `Campo ausente: ${origin.chave}/${field}`);
          entry[field] = flex[field];
        }
      }
      for (const field of Object.keys(flex)) {
        assert(field === '_origem' || fields.includes(field), `Campo não registrado em _origem.campos: ${field}`);
      }
      rows.push([origin.ordem, origin.chave, entry]);
    }
  }
  return Object.fromEntries(rows.sort((a, b) => a[0] - b[0]).map(([, key, entry]) => [key, entry]));
}

// Exact forms only; arrays preserve homographs and distinct analyses.
function buildFormIndex(lexicon) {
  const index = Object.create(null);
  for (const [strong, group] of Object.entries(lexicon)) {
    group.flexoes.forEach((flex, flexao) => {
      for (const form of new Set([flex._origem.chave, flex.grego])) {
        (index[form] ||= []).push({ strongs: strong, flexao });
      }
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

module.exports = { ROOT, SOURCE, DERIVED, BACKUP, read, serialize, serializeLexicon,
  migrate, flatten, buildFormIndex, writeIfChanged };
