const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const c = require('../../tools/dictionary/core');
const { expectedRecords, expectedProjection, bag } = require('./expected');
const source = c.read(c.SOURCE);
const before = c.read(c.BACKUP);
const rows = c.records(source);
const after = c.flatten(source);
const baseline = require('../../tools/dictionary/baseline.json');

test('backup imutável e todas as flexões preservadas com apenas os padrões autorizados', () => {
  assert.equal(crypto.createHash('sha256').update(fs.readFileSync(c.BACKUP)).digest('hex'), baseline.backup_sha256);
  assert.deepEqual(bag(rows), bag(expectedRecords(before)));
  assert.equal(rows.length, baseline.entradas);
  assert.equal(new Set(rows.map(x => x.grego)).size, baseline.formas_gregas);
  assert.equal(new Set(rows.map(x => JSON.stringify([x.abrev_morf, x.morfologia]))).size, baseline.analises_morfologicas);
  assert.equal(Object.keys(source).length, baseline.grupos_strong);
  assert.equal(new Set(Object.values(source).map(x => x.lema).filter(Boolean)).size, baseline.lemas_resolvidos);
  assert.equal(Object.values(before).filter(x => !Object.hasOwn(x, 'ocorrencias_lxx')).length, 3);
});

test('estrutura simples, sequência fixa, verbete antes das flexões e pendências somente preenchidas', () => {
  for (const group of Object.values(source)) {
    assert(!Object.hasOwn(group, 'origem_lexical'));
    if (Object.hasOwn(group, 'pendencias')) assert(group.pendencias.length > 0);
    assert(Object.keys(group).indexOf('verbete' in group ? 'verbete' : 'verbetes') < Object.keys(group).indexOf('flexoes'));
    for (const flex of group.flexoes) {
      assert.deepEqual(Object.keys(flex), [...c.FLEX_FIELDS, ...('verbete' in flex ? ['verbete'] : [])]);
      assert(!Object.hasOwn(flex, '_origem'));
      assert(!Object.hasOwn(flex, 'campos'));
      assert(!Object.hasOwn(flex, 'chave_compatibilidade'));
    }
  }
  for (const entry of Object.values(after)) assert.deepEqual(Object.keys(entry), c.FIELDS);
  const textualOrder = [...fs.readFileSync(c.SOURCE, 'utf8').matchAll(/^  "([^"]+)": \{/gm)].map(x => Number(x[1]));
  assert.equal(textualOrder.length, baseline.grupos_strong);
  assert(textualOrder.every((value, i) => i === 0 || value >= textualOrder[i - 1]));
});

test('projeção por grego corresponde ao oráculo independente, sem chaves artificiais', () => {
  assert.deepEqual(bag(Object.entries(after)), bag(Object.entries(expectedProjection(before))));
  assert.equal(Object.keys(after).length, 18277);
  for (const [key, entry] of Object.entries(after)) assert.equal(key, entry.grego);
  const changedKeys = Object.entries(before).filter(([key, entry]) => key !== entry.grego);
  assert.equal(changedKeys.length, 31);
  assert(changedKeys.every(([, entry]) => Object.hasOwn(after, entry.grego)));
});

test('homógrafos e análises combinadas preservados no léxico e no índice', () => {
  const index = c.buildFormIndex(source);
  for (const [form, strongs] of [['ζητήσεις', ['2214', '2212']], ['κακοποιῶν', ['2554', '2555']], ['καλῶν', ['2570', '2564']]]) {
    assert.deepEqual(new Set(index[form].map(x => x.strongs)), new Set(strongs));
  }
  assert.equal(index['εὗρον'].length, 2);
  assert.equal(index['ὢν'].length, 3);
  assert.equal(Object.values(index).filter(refs => refs.length > 1).length, 7);
  assert.equal(Object.values(index).reduce((n, refs) => n + refs.length, 0), 18285);
  assert.equal(rows.filter(x => x.abrev_morf.includes('/')).length, 1846);
  assert.equal(Object.values(source).filter(x => x.lema === null).reduce((n, x) => n + x.flexoes.length, 0), 136);
  for (const [strongs, group] of Object.entries(source)) {
    group.flexoes.forEach((flex, flexao) => {
      assert.equal(index[flex.grego].filter(ref => ref.strongs === strongs && ref.flexao === flexao).length, 1);
    });
  }
});

test('metadados lexicais continuam associados ao Strong exato', () => {
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
  assert.deepEqual(bag(c.records(c.migrate(before, lexical))), bag(expectedRecords(before)));
});

test('multiplicidade não depende da ordenação e campos desconhecidos não são descartados', () => {
  const reversed = Object.fromEntries(Object.entries(source).reverse().map(([k, group]) => [k, { ...group, flexoes: [...group.flexoes].reverse() }]));
  assert.deepEqual(bag(c.records(reversed)), bag(rows));
  const one = { ...Object.values(before)[0] };
  const sample = { a: { ...one }, b: { ...one } };
  const migrated = c.migrate(sample, {});
  assert.equal(migrated[one.strongs].flexoes.length, 2);
  assert.deepEqual(bag(c.records(migrated)), bag(expectedRecords(sample)));
  assert.equal(Object.keys(c.flatten(migrated)).length, 1);
  migrated[one.strongs].flexoes[0].campo_novo = 'não descartar';
  assert.throws(() => c.records(migrated), /Campo de flexão desconhecido/);
});

test('derivados determinísticos e atualizados', () => {
  require('../../tools/dictionary/generate')({ check: true });
  assert.equal(c.serialize(c.flatten(JSON.parse(c.serializeLexicon(source)))), c.serialize(after));
});

test('verbete da flexão prevalece sobre o comum sem alterar as demais flexões', () => {
  const flex = { ...Object.values(source)[0].flexoes[0] };
  delete flex.verbete;
  const lexicon = { '1': { lema: 'Α', transliteracao: 'Alpha', verbete: 'comum',
    flexoes: [{ ...flex }, { ...flex, verbete: 'específico' }] } };
  assert.deepEqual(c.records(lexicon).map(row => row.verbete), ['comum', 'específico']);
  lexicon['1'].flexoes[1].verbete = 123;
  assert.throws(() => c.records(lexicon), /Verbete ausente/);
});
