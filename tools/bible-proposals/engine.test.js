const test = require('node:test');
const assert = require('node:assert/strict');
const { phrases, createLexicon, propose, evaluate } = require('./engine');
const approved = (reference, phrase, greek, tokens = [1]) => ({ reference, entry: { text: phrase, greek, segments: [{ start: 0, text: phrase, tokens }] } });

test('dicionário preserva diacríticos, registra fallback e não expande notação gramatical', () => {
  assert.deepEqual(phrases('eu/ele(a) era, estava'), []);
  assert.deepEqual(phrases('era/estava'), ['era', 'estava']);
  const lexicon = createLexicon({ 'ἀρχή': { pt: 'princípio' } });
  const result = propose({ text: 'princípio', greek: ['ἀρχῇ'], lexicon });
  assert.equal(result.candidates[0].priority, 'baixa');
  assert.equal(result.candidates[0].evidence[0].kind, 'dicionario-forma-aproximada');
  assert.ok(result.candidates[0].warning);
});

test('vínculo único continua sendo proposta, com evidência e posição UTF-16', () => {
  const result = propose({ text: '😀 Palavra.', greek: ['λόγος'], lexicon: createLexicon({ 'λόγος': { pt: 'palavra' } }) });
  assert.equal(result.status, 'PROPOSTA_NAO_APROVADA');
  assert.equal(result.candidates[0].start, 3);
  assert.equal(result.candidates[0].review, 'CANDIDATO_UNICO');
  assert.deepEqual(result.candidates[0].tokens, [1]);
  assert.equal(result.candidates[0].evidence[0].field, 'pt');
  assert.equal(result.segments, undefined);
});

test('palavras repetidas produzem todas as alternativas conflitantes', () => {
  const result = propose({ text: 'Palavra e Palavra', greek: ['λόγος', 'λόγος'], lexicon: createLexicon({ 'λόγος': { pt: 'palavra' } }) });
  assert.equal(result.candidates.length, 4);
  assert.ok(result.candidates.every(candidate => candidate.review === 'AMBIGUO' && candidate.conflicts.length));
});

test('expressões aprendidas e alternativas explícitas conservam múltiplos tokens', () => {
  const example = approved('jo 1:51', 'digo a vocês', ['λέγω', 'ὑμῖν'], [1, 2]);
  example.entry.segments[0].alternatives = ['lhes digo'];
  const result = propose({ text: 'lhes digo', greek: ['λέγω', 'ὑμῖν'], lexicon: createLexicon({}, [example]) });
  assert.equal(result.candidates.length, 1);
  assert.deepEqual(result.candidates[0].tokens, [1, 2]);
  assert.equal(result.candidates[0].evidence[0].kind, 'equivalencia-explicita');
  assert.equal(result.candidates[0].evidence[0].examples[0].reference, 'jo 1:51');
});

test('avaliação exclui todos os exemplos do próprio versículo', () => {
  const example = approved('jo 1:1', 'Palavra', ['λόγος']);
  const lexicon = createLexicon({}, [example]);
  const result = propose({ text: 'Palavra', greek: ['λόγος'], lexicon, excludeReference: 'jo 1:1' });
  assert.equal(result.candidates.length, 0);
  assert.equal(evaluate(result, example.entry).matchedApprovedSegments, 0);
});

test('agrupamentos não contíguos não viram regra lexical genérica', () => {
  const lexicon = createLexicon({}, [approved('jo 1:27', 'de quem', ['οὗ', 'x', 'αὐτοῦ'], [1, 3])]);
  assert.equal(propose({ text: 'de quem', greek: ['οὗ', 'x', 'αὐτοῦ'], lexicon }).candidates.length, 0);
});

test('não remove HTML nem associa termos supridos entre colchetes', () => {
  const lexicon = createLexicon({ 'ἦλθεν': { pt: 'veio' } });
  const result = propose({ text: '[veio] e veio', greek: ['ἦλθεν'], lexicon });
  assert.equal(result.candidates.length, 1);
  assert.equal(result.candidates[0].start, 9);
  assert.match(result.unmatchedPortuguese[0].reason, /suprido/);
  assert.equal(propose({ text: '<rl>veio</rl>', greek: ['ἦλθεν'], lexicon }).candidates.length, 0);
});

test('não atravessa cláusulas e sinaliza truncamento sem falsa unicidade', () => {
  const lexicon = createLexicon({}, [approved('jo 1:1', 'por meio', ['διά'])]);
  assert.equal(propose({ text: 'por, meio', greek: ['διά'], lexicon }).candidates.length, 0);
  const result = propose({ text: 'por meio e por meio', greek: ['διά'], lexicon, maxCandidates: 1 });
  assert.equal(result.candidates[0].review, 'RESULTADO_PARCIAL');
  assert.ok(result.issues.length);
});
