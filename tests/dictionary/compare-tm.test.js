const test = require('node:test');
const assert = require('node:assert/strict');
const { collectTM, compare } = require('../../tools/dictionary/compare-tm');

test('comparação literal preserva Unicode, caixa e todas as entradas homógrafas', () => {
  const forms = ['ἄνθρωπος', 'ἄνθρωπος'.normalize('NFD'), 'Ἄνθρωπος', 'ανθρωπος', 'λόγος', 'ξένος'];
  const tm = collectTM([['MT.json', [{ chapter: 1, pericopes: [{ verses: [
    { verse: 1, tokens: forms.map(lemma => ({ lemma })) },
    { verse: 2, tokens: [{ lemma: forms[0] }] },
  ] }] }]]]);
  const lexicon = {
    1: { lema: 'ἄνθρωπος', flexoes: [{ grego: 'ἄνθρωπος' }, { grego: 'λόγος' }] },
    2: { lema: 'ἄνθρωπος', flexoes: [{ grego: 'ἄνθρωπος' }, { grego: 'ἄλλος' }] },
    3: { lema: 'ξένος', flexoes: [] },
  };
  const before = JSON.stringify(lexicon);
  const report = compare(tm, lexicon);
  assert.equal(report.resumo.tokens_tm, 7);
  assert.equal(report.resumo.formas_tm_ausentes, 4);
  assert.equal(report.resumo.ausentes_com_candidatos, 3);
  assert.equal(report.formas_tm_ausentes[0].candidatos[0].diferenca, 'representacao_unicode');
  assert.equal(report.formas_tm_ausentes[1].candidatos[0].diferenca, 'maiusculas_e_ou_diacriticos');
  assert.equal(report.formas_tm_ausentes[2].candidatos[0].diferenca, 'diacriticos');
  assert.equal(report.formas_tm_ausentes[0].candidatos[0].entradas.length, 2);
  assert.equal(report.formas_tm_ausentes[0].candidatos[0].presente_exatamente_no_tm, true);
  assert.deepEqual(report.formas_tm_ausentes[3].candidatos, []);
  assert.deepEqual(report.formas_lexico_sem_ocorrencia_exata_tm.map(row => row.forma_lexico), ['ἄλλος']);
  assert.deepEqual(tm.get('ἄνθρωπος')[1], { arquivo: 'MT.json', capitulo: 1, versiculo: 2, token: 1 });
  assert.equal(JSON.stringify(lexicon), before);
});

test('dados inválidos interrompem a auditoria em vez de omitir formas', () => {
  assert.throws(() => collectTM([['MT.json', [{ chapter: 1 }]]]), /perícopes inválidas/);
  assert.throws(() => compare(new Map(), { 1: { flexoes: [{}] } }), /grego inválido/);
});
