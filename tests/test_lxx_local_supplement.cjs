const test = require('node:test');
const assert = require('node:assert/strict');
const { buildIndexes, findCandidates } = require('../tools/lxx/audit_local_supplement');

test('cruzamento local mantém prioridade do lema e distingue indícios por flexão', () => {
  const lexicon = { fonte: 'origem', α: {
    αμμος: { def: 'areia', flex: { genitivo: 'αμμων', misturado: 'αμμοι – areias' } },
    αλλος: { def: 'outro', flex: {} },
  }, adjetivos: { αλλος: { def: 'outro (variante)', flex: {} } } };
  const original = JSON.stringify(lexicon);
  const indexes = buildIndexes(lexicon);
  const lemma = findCandidates({ lemma: 'ἄλλος', form: 'Αμμων' }, indexes);
  assert.equal(lemma.status, 'lemma_unaccented');
  assert.equal(new Set(lemma.evidence.map(e => e.entryId)).size, 2);
  const collision = findCandidates({ lemma: 'Αμμων', form: 'Αμμων' }, indexes);
  assert.equal(collision.status, 'surface_flex_only');
  assert.equal(collision.evidence[0].field, 'flex.genitivo');
  assert.equal(findCandidates({ lemma: 'desconhecido', form: 'αμμοι' }, indexes).status, 'surface_mixed_only');
  assert.equal(findCandidates({ lemma: 'desconhecido', form: 'zz' }, indexes).status, 'not_found');
  assert.equal(JSON.stringify(lexicon), original);
});
