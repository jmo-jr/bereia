const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const c = require('../../tools/dictionary/core');
const source = c.read(c.SOURCE);
const before = c.read(c.BACKUP);
const after = c.flatten(source);
const baseline = require('../../tools/dictionary/baseline.json');
const canonical = value => Array.isArray(value) ? value.map(canonical) :
  value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])])) : value;
const bag = rows => {
  const counts = new Map();
  for (const row of rows) {
    const key = JSON.stringify(canonical(row));
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return counts;
};

test('backup imutável, campos, valores e multiplicidade completos', () => {
  assert.equal(crypto.createHash('sha256').update(fs.readFileSync(c.BACKUP)).digest('hex'), baseline.backup_sha256);
  assert.deepEqual(bag(Object.entries(after)), bag(Object.entries(before)));
  assert.equal(Object.keys(after).length, baseline.entradas);
  assert.equal(new Set(Object.values(after).map(x => x.grego)).size, baseline.formas_gregas);
  assert.equal(new Set(Object.values(after).map(x => JSON.stringify([x.abrev_morf, x.morfologia]))).size, baseline.analises_morfologicas);
  assert.equal(Object.keys(source).length, baseline.grupos_strong);
  assert.equal(new Set(Object.values(source).map(x => x.lema).filter(Boolean)).size, baseline.lemas_resolvidos);
});

test('ordem das entradas e campos e formatação original preservadas', () => {
  assert.equal(c.serialize(after), fs.readFileSync(c.BACKUP, 'utf8'));
  const textualOrder = [...fs.readFileSync(c.SOURCE, 'utf8').matchAll(/^  "([^"]+)": \{/gm)].map(x => Number(x[1]));
  assert.equal(textualOrder.length, baseline.grupos_strong);
  assert(textualOrder.every((value, i) => i === 0 || value >= textualOrder[i - 1]));
});

test('homógrafos, chaves invisíveis e análises combinadas preservados', () => {
  const index = c.buildFormIndex(source);
  for (const [form, strongs] of [['ζητήσεις', ['2214', '2212']], ['κακοποιῶν', ['2554', '2555']], ['καλῶν', ['2570', '2564']]]) {
    assert.deepEqual(new Set(index[form].map(x => x.strongs)), new Set(strongs));
  }
  assert.equal(index['εὗρον'].length, 2);
  assert.equal(after['ἔφαγον'].abrev_morf, before['ἔφαγον'].abrev_morf);
  assert.equal(after['εὐχαριστῶ'].abrev_morf, before['εὐχαριστῶ'].abrev_morf);
  assert.equal(Object.values(after).filter(x => x.abrev_morf.includes('/')).length, 1846);
  assert.equal(Object.values(source).filter(x => x.lema === null).reduce((n, x) => n + x.flexoes.length, 0), 136);
});

test('metadados lexicais têm procedência e correspondência exata de Strong', () => {
  const archive = fs.readFileSync(path.join(c.ROOT, 'src/_data/archive/strongsg.js'), 'utf8');
  assert.equal(crypto.createHash('sha256').update(archive).digest('hex'), baseline.lexical_archive_sha256);
  const lexical = JSON.parse(archive.slice(archive.indexOf('{', archive.indexOf('var strongsGreekDictionary')), archive.lastIndexOf('}') + 1));
  for (const [strong, group] of Object.entries(source)) {
    if (!/^\d+$/.test(strong)) {
      assert.equal(group.lema, null);
      assert(group.pendencias.length > 0);
    } else {
      assert.equal(group.lema, lexical['G' + strong]?.lemma || null);
      assert.equal(group.transliteracao, lexical['G' + strong]?.translit || null);
    }
  }
  const index = c.buildFormIndex(source);
  for (const [strongs, group] of Object.entries(source)) {
    group.flexoes.forEach((flex, flexao) => {
      for (const form of new Set([flex.grego, flex._origem.chave])) {
        assert.equal(index[form].filter(ref => ref.strongs === strongs && ref.flexao === flexao).length, 1);
      }
    });
  }
});

test('multiplicidade e ordem sobrevivem à reordenação dos objetos lexicais', () => {
  const reversed = Object.fromEntries(Object.entries(source).reverse().map(([k, group]) => [k, { ...group, flexoes: [...group.flexoes].reverse() }]));
  assert.deepEqual(bag(Object.entries(c.flatten(reversed))), bag(Object.entries(before)));
  assert.equal(c.serialize(c.flatten(reversed)), c.serialize(after));
  const sample = { a: { strongs: '1', grego: 'Α', verbete: 'alfa', pt: 'a' }, b: { strongs: '1', grego: 'Α', verbete: 'alfa', pt: 'a' } };
  const migrated = c.migrate(sample, {});
  assert.equal(migrated['1'].flexoes.length, 2);
  assert.deepEqual(bag(Object.entries(c.flatten(migrated))), bag(Object.entries(sample)));
  migrated['1'].flexoes[1]._origem.chave = 'a';
  assert.throws(() => c.flatten(migrated), /Chave duplicada/);
});

test('derivados determinísticos e atualizados', () => {
  require('../../tools/dictionary/generate')({ check: true });
  assert.equal(c.serialize(c.flatten(JSON.parse(c.serializeLexicon(source)))), c.serialize(after));
});
