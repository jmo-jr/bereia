const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const { parseFragment } = require('parse5');
const { ROOT, buildFormIndex } = require('../dictionary/core');
const { canNormalizeGreekVariant } = require('../../src/_data/nt');
const { readVerse, renderVerse } = require('./verse-html');
const { createLexicon, indexExceptions, resolveVerse } = require('./resolve');
const { createPilot } = require('./pilot');

function flex(grego, pt, abrev_morf = 'V') {
  return { grego, pt, traducao: pt, transliteracao: 'teste', abrev_morf, morfologia: abrev_morf };
}

function group(lema, ...flexoes) {
  return { lema, verbete: 'significado', flexoes };
}

const dictionary = {
  '2532': group('καί', { ...flex('καί', 'e/também', 'Conj'), traducao: 'e, também, que' }),
  '3588': group('ὁ', flex('ὁ', 'o', 'T-NSM'), flex('τό', 'o', 'T-NSN')),
  '1510': group('εἰμί', flex('ἦν', 'existia, estava, era', 'V-IAI-3S')),
  '4160': group('ποιέω', flex('ποίησον', 'faz', 'V-AMA-2S')),
  '2511': group('καθαρίζω', flex('καθαρίσαι', 'tornar limpo', 'V-AAN')),
  '575': group('ἀπό', flex('ἀπό', 'de', 'Prep')),
  '746': { ...group('ἀρχή', flex('ἀρχή', 'princípio', 'N-NSF')), verbete: 'começo' },
  '1': group('ὦ', flex('ὦ', 'ó', 'Interj')),
  '2': group('εἰμί', flex('ὦ', 'seja', 'V-PAS-1S')),
  '3': group('σημάδι', flex('ὦ\u200B', 'sinal', 'N')),
};

const lexicon = createLexicon(dictionary, buildFormIndex(dictionary), { allowVariant: canNormalizeGreekVariant });
const reference = 'Mt 8:2';

function run(html, rawGreek, exceptions = {}, options = {}) {
  const verse = readVerse(html);
  const configured = indexExceptions(exceptions, 'Mt', 8, new Set([2]));
  const rawTokens = rawGreek.map(token => typeof token === 'string' ? { lemma: token } : token);
  const approved = options.signature ?? verse.signature;
  return {
    ...resolveVerse(verse, rawTokens, lexicon, reference, configured.references, approved, key => key === 'que'),
    issues: configured.issues,
    verse,
  };
}

test('conta palavras visíveis e preserva a grafia e a posição em HTML inline', () => {
  const raw = 'E <em>apro</em>ximando-se, d&rsquo;água; <i>da</i> [isto] <span hidden>nota fora</span><br>foi.';
  const parsed = readVerse(raw);
  assert.deepEqual(parsed.tokens.map(token => token.text), ['E', 'aproximando-se', 'd’água', 'da', 'isto', 'foi']);
  assert.deepEqual(parsed.tokens.map(token => token.position), [1, 2, 3, 4, 5, 6]);
  assert.equal(parsed.tokens[4].editorial, true);
  assert.equal(parsed.signature, readVerse('E aproximando-se, d\'água; da [isto] foi.').signature);
});

test('resolve repetição da mesma análise e preserva a grafia do TM', () => {
  const { results } = run('E existia, estava; era e.', ['Καὶ', 'καὶ', 'ἦν', 'ἦν']);
  assert.deepEqual(results.map(result => result.status), Array(5).fill('resolved_automatically'));
  assert.deepEqual(results.map(result => result.association[0].form), ['Καὶ', 'ἦν', 'ἦν', 'ἦν', 'Καὶ']);
});

test('duas flexões do mesmo lema precisam de exceções em posições distintas', () => {
  const { results } = run('O o', ['ὁ', 'τό'], { o: { 'ὁ': ['Mt 8:2:1'], 'τό': ['Mt 8:2:2'] } });
  assert.deepEqual(results.map(result => result.candidates.map(entry => entry.form)), [['ὁ', 'τό'], ['ὁ', 'τό']]);
  assert.deepEqual(results.map(result => result.association[0].form), ['ὁ', 'τό']);
  assert.deepEqual(results.map(result => result.status), Array(2).fill('resolved_by_exception'));
});

test('aceita dois termos gregos para uma contração e compartilha uma tradução composta', () => {
  const html = 'Do tor<strong>nar</strong> limpo';
  const { verse, results } = run(html, ['ἀπὸ', 'τό', 'καθαρίσαι'], { do: { 'ἀπὸ': ['Mt 8:2:1'], 'τό': ['Mt 8:2:1'] } });
  assert.deepEqual(results.map(result => result.association.map(entry => entry.form)),
    [['ἀπὸ', 'τό'], ['καθαρίσαι'], ['καθαρίσαι']]);
  const output = renderVerse(html, verse, results, 'v2');
  assert.equal(readVerse(output.body).text, readVerse(html).text);
  assert.match(output.body, /aria-label="tornar"/);
  assert.match(output.body, /<strong><span class="lexical-trigger"[^>]+>nar<\/span><\/strong>/);
  assert.equal([...output.body.matchAll(/<button/g)].length, 3);
  assert.equal([...output.details.matchAll(/data-pagefind-ignore/g)].length, 2);
  assert.equal([...output.details.matchAll(/lang="grc"/g)].length, 3);
  assert.equal(readVerse(output.body + output.details).text, readVerse(html).text);
});

test('separa sinônimo, alternativa gramatical e palavra editorial de associações confirmadas', () => {
  const { results } = run('Que começo [isto]', ['καὶ', 'ἀρχή']);
  assert.deepEqual(results.map(result => result.status), [
    'pending_lexical_review', 'pending_lexical_review', 'no_greek_equivalent',
  ]);
  assert.equal(results[0].reason, 'grammatical_alternative_needs_context');
  assert.equal(results[1].suggestions[0].evidence, 'verbete');
  assert.ok(results.every(result => !result.association.length));
});

test('grafias semelhantes com morfologias distintas permanecem incertas', () => {
  const { results, unidentified } = run('Princípio', ['ἀρχῇ']);
  assert.deepEqual(unidentified, [{ form: 'ἀρχῇ', position: 1 }]);
  assert.equal(results[0].reason, 'unverified_greek_flexion');
  assert.equal(results[0].suggestions[0].dictionaryForm, 'ἀρχή');
  assert.deepEqual(results[0].association, []);
});

test('preserva homógrafos reais e marcadores, aceitando análise no token quando disponível', () => {
  assert.equal(run('Ó', ['ὦ']).results[0].reason, 'greek_homograph');
  const override = run('Ó', ['ὦ'], { ó: { 'ὦ': ['Mt 8:2:1'] } });
  assert.equal(override.results[0].status, 'exception_requires_review');
  assert.equal(run('Ó', [{ lemma: 'ὦ', strongs: '1' }]).results[0].association[0].strong, '1');
  assert.equal(run('Sinal', ['ὦ\u200B']).results[0].association[0].strong, '3');
});

test('bloqueia exceção desatualizada mesmo quando a mesma palavra continua na posição', () => {
  const old = readVerse('O vento o mar').signature;
  const exceptions = { o: { 'τό': ['Mt 8:2:3'] } };
  const { results } = run('E vento o mar o', ['ὁ', 'τό'], exceptions, { signature: old });
  assert.equal(results[2].reason, 'reference_outdated');
  assert.equal(results[2].association.length, 0);
  const changed = run('O vento e mar o', ['ὁ', 'τό'], exceptions, { signature: old });
  assert.equal(changed.results[2].reason, 'reference_word_changed');
});

test('valida referências repetidas, incompatíveis e formas ausentes do TM', () => {
  const { results, issues } = run('O', ['ὁ'], {
    o: { 'ὁ': ['Mt 8:2:1', 'Mt 8:2:1', 'Mt 8:3:1', 'Mt 8:2:0'] },
  });
  assert.deepEqual(issues.map(issue => issue.reason), ['duplicate_reference', 'unknown_reference', 'invalid_reference_format']);
  assert.equal(results[0].association.length, 0);
  assert.equal(run('O', ['ὁ'], { o: { 'τό': ['Mt 8:2:1'] } }).results[0].reason, 'greek_form_not_identified');
});

test('pede contexto quando a mesma grafia portuguesa pode exercer funções gramaticais diferentes', () => {
  const { results } = run('Jesus o tocou', ['ὁ']);
  assert.equal(results[1].reason, 'grammatical_role_needs_context');
  assert.deepEqual(results[1].association, []);
  assert.deepEqual(results[1].candidates.map(entry => entry.form), ['ὁ']);
});

test('uma ocorrência verbal grega não confirma duas ocorrências da mesma palavra portuguesa', () => {
  const greek = ['Ποίησον', 'ποιεῖ'];
  const original = run('faz isto e faz', greek);
  for (const index of [0, 3]) {
    assert.equal(original.results[index].reason, 'repeated_verb_needs_context');
    assert.deepEqual(original.results[index].association, []);
  }
  const reviewed = run('faz isto e faz', greek, { faz: { 'Ποίησον': ['Mt 8:2:1'] } });
  assert.equal(reviewed.results[0].status, 'resolved_by_exception');
  assert.equal(reviewed.results[3].status, 'pending_context_review');
  assert.equal(run('faz e faz', ['Ποίησον', 'ποίησον']).results[2].status, 'resolved_automatically');
});

test('o piloto usa as fontes versionadas e resolve os exemplos do Liquid', () => {
  const pilot = createPilot();
  const liquid = fs.readFileSync(path.join(ROOT, 'src/biblia/nt/mateus/8.liquid'), 'utf8');
  const verses = [...liquid.matchAll(/{% verse bookAbbrev bookChapter (\d+)[^%]*%}([\s\S]*?){% endverse %}/g)];
  assert.equal(verses.length, 34);
  function aligned(number) {
    const [, , html] = verses.find(([, reference]) => Number(reference) === number);
    const output = pilot.align(html.trim(), number, 'mt_8-' + number);
    assert.equal(readVerse(output.body).text, readVerse(html.trim()).text);
    return output;
  }
  assert.match(aligned(1).details, /ἀπὸ.*τοῦ/);
  assert.match(aligned(2).details, /λεπρὸς.*Nominativo Masculino Singular/);
  assert.match(aligned(2).details, /ἐὰν/);
  const third = readVerse(aligned(3).body);
  assert.equal(third.tokens.find(token => token.position === 7).key, 'o');
  assert.ok(!third.tokens.find(token => token.position === 7).segments.some(segment => segment.interactive));
  const ninth = aligned(9);
  const byPosition = readVerse(ninth.body).tokens;
  assert.equal(byPosition[34].key, 'faz');
  assert.ok(byPosition[34].segments.some(segment => segment.interactive));
  assert.equal(byPosition[37].key, 'faz');
  assert.ok(!byPosition[37].segments.some(segment => segment.interactive));
  assert.match(ninth.details, /Πορεύθητι.*πορεύεται/);
  assert.equal(parseFragment(ninth.body).childNodes
    .filter(node => node.tagName === 'button' && node.childNodes[0]?.value === 'vai').length, 2);
});
