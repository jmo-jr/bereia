const test = require('node:test');
const assert = require('node:assert/strict');
const { createLexicon, propose } = require('./engine');
const { buildIndex } = require('../bible-reverse-index');
const { occurrenceRelations } = require('./relations');
const dictionary = { 'λόγος': { pt: 'palavra', traducao: 'palavra' }, 'ἀρχή': { pt: 'princípio' } };
const lexicon = createLexicon(dictionary, [], buildIndex(dictionary, 'hash'));

test('o caminho do índice filtra por versículo e não usa fallback sem diacríticos', () => {
  assert.equal(propose({ text: 'princípio', greek: ['ἀρχῇ'], lexicon }).candidates.length, 0);
  const result = propose({ text: 'palavra', greek: ['λόγος', 'καί'], lexicon });
  assert.equal(result.candidates.length, 1);
  assert.deepEqual(result.candidates[0].tokens, [1]);
  assert.ok(result.candidates[0].evidence.every(item => item.kind === 'indice-reverso-forma-exata'));
});

test('consulta reversa não inventa palavras ou perde a distinção entre hífen e espaço', () => {
  const d = { 'x': { pt: 'por meio' } };
  const l = createLexicon(d, [], buildIndex(d, 'hash'));
  const result = propose({ text: 'por meio e por-meio', greek: ['x'], lexicon: l });
  assert.equal(result.candidates.length, 1);
  assert.equal(result.candidates[0].text, 'por meio');
});

test('relação tem referência, evidência, posição e id estável sem aprovação inferida', () => {
  const proposal = propose({ text: 'Palavra', greek: ['λόγος'], lexicon });
  const first = occurrenceRelations('jo 2:1', proposal);
  const second = occurrenceRelations('jo 2:1', proposal);
  assert.deepEqual(first, second);
  const relation = first.relations[0];
  assert.equal(relation.status, 'PROPOSTA');
  assert.equal(relation.reference, 'jo 2:1');
  assert.equal(relation.start, 0);
  assert.ok(relation.evidence.length);
  assert.ok(!relation.id.startsWith('c'));
  assert.notEqual(occurrenceRelations('jo 2:2', proposal).relations[0].id, relation.id);
});

test('ambiguidades mantêm todas as ocorrências com conflitos por id estável', () => {
  const record = occurrenceRelations('jo 2:1', propose({ text: 'Palavra Palavra', greek: ['λόγος', 'λόγος'], lexicon }));
  assert.equal(record.relations.length, 4);
  const ids = new Set(record.relations.map(item => item.id));
  assert.equal(ids.size, 4);
  assert.ok(record.relations.every(item => item.status === 'PENDENTE' && item.conflicts.every(id => ids.has(id))));
});

test('aprovação só vem de arquivo aprovado com texto e grego idênticos', () => {
  const proposal = propose({ text: 'Palavra', greek: ['λόγος'], lexicon });
  const gold = { text: 'Palavra', greek: ['λόγος'], segments: [{ start: 0, text: 'Palavra', tokens: [1] }] };
  assert.equal(occurrenceRelations('jo 1:1', proposal, gold).relations[0].status, 'APROVADA');
  const stale = occurrenceRelations('jo 1:1', proposal, { ...gold, text: 'A Palavra' });
  assert.equal(stale.relations[0].status, 'PROPOSTA');
  assert.ok(stale.issues.length);
  const changedGreek = occurrenceRelations('jo 1:1', proposal, { ...gold, greek: ['λόγου'] });
  assert.equal(changedGreek.relations[0].status, 'PROPOSTA');
});

test('vínculo aprovado pode ser mantido sem candidato e notas de suprimento são preservadas', () => {
  const proposal = propose({ text: 'a Palavra', greek: ['λόγος', 'x'], lexicon });
  const gold = { text: 'a Palavra', greek: ['λόγος', 'x'], segments: [{ start: 2, text: 'Palavra', tokens: [1] }],
    unlinkedPortuguese: [{ start: 0, text: 'a', reason: 'Artigo suprido.' }], untranslatedTokens: [{ position: 2, reason: 'Representado pela pontuação.' }] };
  const record = occurrenceRelations('jo 1:1', proposal, gold);
  assert.equal(record.notes.length, 2);
  assert.ok(record.notes.every(item => item.status === 'APROVADA'));
  const missing = occurrenceRelations('jo 1:1', { ...proposal, candidates: [] }, gold);
  assert.equal(missing.relations[0].status, 'APROVADA');
});

test('anotação aprovada de termo suprido deixa sugestões concorrentes pendentes', () => {
  const proposal = { text: 'a Palavra', greek: ['λόγος'], candidates: [{ start: 0, text: 'a', tokens: [1], evidence: [], review: 'CANDIDATO_UNICO' }], unmatchedPortuguese: [], unmatchedGreek: [], issues: [] };
  const approved = { text: 'a Palavra', greek: ['λόγος'], segments: [], unlinkedPortuguese: [{ start: 0, text: 'a', reason: 'Artigo suprido.' }] };
  const record = occurrenceRelations('jo 1:1', proposal, approved);
  assert.equal(record.relations[0].status, 'PENDENTE');
  assert.ok(record.relations[0].conflicts.includes(record.notes[0].id));
});
