const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createEnhanceTokenWithDict } = require('../../src/_data/nt');
const root = path.resolve(__dirname, '../..');
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));

test('formas aprovadas retornam seus registros literais/NFC e mantêm seus índices', () => {
  const approval = read('tools/audit/approvals/agudo-grave-255.json');
  const lexical = read('src/_data/nt/dict_lex_nt-lxx_greek-pt.json');
  const dictionary = read('src/_data/nt/dict_flex_nt-lxx_greek-pt.json');
  const index = read('src/_data/nt/dict_form_index_nt-lxx_greek-pt.json');
  const lookup = createEnhanceTokenWithDict(dictionary, { record() { assert.fail('Forma aprovada sem cobertura'); } }, ['ocorrencias_lxx']);
  const forms = new Set();
  for (const approved of approval.aplicacoes) {
    const expected = lexical[approved.strong].flexoes[approved.flexao];
    assert.equal(expected.grego, approved.campos.grego);
    assert(!forms.has(expected.grego)); forms.add(expected.grego);
    assert.deepEqual(index[expected.grego], [{ strongs: approved.strong, flexao: approved.flexao }]);
    for (const form of [expected.grego, expected.grego.normalize('NFD')]) {
      const actual = lookup({ lemma: form });
      assert.equal(actual.lemma, form);
      assert.equal(actual.strongs, approved.strong);
      for (const field of ['grego', 'transliteracao', 'ocorrencias', 'traducao', 'pt', 'abrev_morf', 'morfologia', 'ocorrencias_lxx']) {
        assert.equal(actual[field], expected[field], `${form}/${field}`);
      }
    }
  }
  assert.equal(forms.size, approval.quantidade);
});
