const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { greekCaseKey } = require('../../src/lib/greek-form-lookup');
const { createEnhanceTokenWithDict } = require('../../src/_data/nt');
const root = path.resolve(__dirname, '../..');
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));

test('caixa conserva acentos, espíritos, iota subscrito e espaços', () => {
  assert.equal(greekCaseKey('Ἀρχῇ'), greekCaseKey('ἀρχῇ'.normalize('NFD')));
  assert.notEqual(greekCaseKey('ἀρχῇ'), greekCaseKey('ἀρχή'));
  assert.notEqual(greekCaseKey('ἕκτος'), greekCaseKey('ἐκτός'));
  assert.notEqual(greekCaseKey('ἀρχὴ'), greekCaseKey('ἀρχή'));
  assert.equal(greekCaseKey('ᾼ'), 'ᾳ');
  assert.notEqual(greekCaseKey('ᾼ'), greekCaseKey('ΑΙ'));
  assert.notEqual(greekCaseKey('Ὦ '), greekCaseKey('ὦ'));
});

test('consulta por caixa mantém a grafia do token e dos nomes próprios', () => {
  const dict = { 'Ἰησοῦς': { grego: 'Ἰησοῦς', strongs: '2424', pt: 'Jesus' } };
  const lookup = createEnhanceTokenWithDict(dict, { record() { assert.fail('Não deve faltar'); } });
  const result = lookup({ lemma: 'ἰησοῦς' });
  assert.equal(result.lemma, 'ἰησοῦς');
  assert.equal(result.grego, 'Ἰησοῦς');
  assert.equal(dict['Ἰησοῦς'].grego, 'Ἰησοῦς');
});

test('colisões não escolhem o primeiro Strong nem retomam o fallback legado', () => {
  const missing = [];
  const dict = { 'λόγος': { grego: 'λόγος', strongs: '1', pt: 'um' },
                 'Λόγος': { grego: 'Λόγος', strongs: '2', pt: 'dois' } };
  const lookup = createEnhanceTokenWithDict(dict, { record: (t, c) => missing.push(c) });
  const result = lookup({ lemma: 'ΛΌΓΟΣ' });
  assert.equal(result.consulta_dicionario, 'ambiguidade_caixa');
  assert.equal(result.pt, undefined);
  assert.deepEqual(result.analises_dicionario.map(r => r.strongs), ['1', '2']);
  assert.equal(missing[0].motivo, 'ambiguidade_caixa');
});

test('caso real Εὗρον preserva as duas análises do índice completo', () => {
  const dict = read('src/_data/nt/dict_flex_nt-lxx_greek-pt.json');
  const index = read('src/_data/nt/dict_form_index_nt-lxx_greek-pt.json');
  const lookup = createEnhanceTokenWithDict(dict, { record() {} }, [], index);
  const result = lookup({ lemma: 'Εὗρον' });
  assert.equal(result.consulta_dicionario, 'caixa_multianalise');
  assert.equal(result.abrev_morf, dict['εὗρον'].abrev_morf);
  assert.deepEqual(result.analises_dicionario.map(r => ({ strongs: r.strongs, flexao: r.flexao })), index['εὗρον']);
});

test('mesma grafia com Strong diferentes não é resolvida pela projeção plana', () => {
  const dict = { 'λόγος': { grego: 'λόγος', strongs: '1', pt: 'um' } };
  const index = { 'λόγος': [{ strongs: '1', flexao: 0 }, { strongs: '2', flexao: 0 }] };
  const lookup = createEnhanceTokenWithDict(dict, { record() {} }, [], index);
  const result = lookup({ lemma: 'Λόγος' });
  assert.equal(result.consulta_dicionario, 'ambiguidade_caixa');
  assert.equal(result.strongs, undefined);
  assert.deepEqual(result.analises_dicionario.map(r => r.strongs), ['1', '2']);
});
