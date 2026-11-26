const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { parseDocument } = require('htmlparser2');
const { textContent, findAll, removeElement } = require('domutils');
const { createGlobalRenderer } = require('../../src/lib/bible-global-renderer');
const { resolve } = require('../../src/lib/bible-global-lexicon');
const { loadExceptions } = require('../../src/lib/bible-exceptions');
const d = {
  'λόγος': { grego: 'λόγος', pt: 'palavra', strongs: '1', morfologia: 'Análise A' },
  'ΛΌΓΟΣ': { grego: 'λόγος', pt: 'palavra', strongs: '2', morfologia: 'Análise B' },
};
function fixture({ text = 'A Palavra', greek = ['λόγος'], anchorText = text, anchorGreek = greek, associations, entries = {} } = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-context-'));
  const write = (name, data) => { const filename = path.join(root, name); fs.mkdirSync(path.dirname(filename), { recursive: true }); fs.writeFileSync(filename, JSON.stringify(data)); };
  write('src/_data/nt/dict_flex_nt-lxx_greek-pt.json', d);
  write('src/tooltip-relations.json', { version: 1, ambiguityPolicy: 'alternatives', entries });
  write('src/tooltip-exceptions.json', { version: 1, verses: associations ? { 'jo 1:1': { portuguese: anchorText, greek: anchorGreek, associations } } : {} });
  write('src/interlinear/nt/JO.json', [{ chapter: 1, pericopes: [{ verses: [{ verse: 1, tokens: greek.map(lemma => ({ lemma })) }] }] }]);
  const html = `<span class="verse" id="jo_1-1"><span class="verse-text">${text}</span></span>`;
  return { root, html, write, remove() { fs.rmSync(root, { recursive: true }); } };
}
const decoded = html => textContent(parseDocument(html));
const association = { position: 2, text: 'Palavra', groups: [{ tokens: [1], dictionaryKeys: ['ΛΌΓΟΣ'] }] };

test('homógrafos graficamente iguais com análises diferentes continuam como alternativas', () => {
  const f = fixture();
  try {
    const renderer = createGlobalRenderer({ root: f.root }); const html = renderer.transform(f.html);
    assert.match(decoded(html), /Análise A/); assert.match(decoded(html), /Análise B/);
    assert.equal(renderer.report().totals.alternatives, 1);
    assert.equal(renderer.report().totals.contextConfirmedTokens, 0);
  } finally { f.remove(); }
});

test('mesma forma com a mesma identidade lexical e morfológica não gera falsa ambiguidade', () => {
  const dictionary = { 'λόγος': { ...d['λόγος'] }, 'ΛΌΓΟΣ': { ...d['λόγος'] } };
  const lexicon = resolve(dictionary, { version: 1, ambiguityPolicy: 'alternatives', entries: {} });
  const { findMatches } = require('../../src/lib/bible-global-lexicon');
  assert.equal(findMatches('palavra', ['λόγος', 'λόγος'], lexicon)[0].candidates.length, 1);
});

test('exceção explícita seleciona a análise pelo identificador do dicionário', () => {
  const f = fixture({ associations: [association] });
  try {
    const renderer = createGlobalRenderer({ root: f.root }); const html = renderer.transform(f.html);
    assert.doesNotMatch(decoded(html), /Análise A/); assert.match(decoded(html), /Análise B/);
    assert.equal(renderer.report().totals.contextConfirmedTokens, 1);
    assert.equal(renderer.report().totals.lexicalTokens, 0);
  } finally { f.remove(); }
});

test('mudança de palavras invalida a exceção mesmo quando a posição ainda contém Palavra', () => {
  const f = fixture({ text: 'Outra Palavra', anchorText: 'A Palavra', associations: [association] });
  try {
    const renderer = createGlobalRenderer({ root: f.root }); const html = renderer.transform(f.html);
    assert.match(decoded(html), /Análise A/); assert.match(decoded(html), /Análise B/);
    assert.equal(renderer.report().totals.contextConfirmedTokens, 0);
    assert.match(renderer.report().issues[0].issues[0], /âncora/);
  } finally { f.remove(); }
});

test('espaços, caixa e pontuação permitem revalidação pela âncora sem gravar a fonte', () => {
  const f = fixture({ text: 'A   Palavra!', anchorText: 'A Palavra', associations: [association] });
  try {
    const filename = path.join(f.root, 'src/tooltip-exceptions.json'), before = fs.readFileSync(filename, 'utf8');
    const renderer = createGlobalRenderer({ root: f.root }); renderer.transform(f.html);
    assert.equal(renderer.report().totals.contextConfirmedTokens, 1);
    assert.equal(fs.readFileSync(filename, 'utf8'), before);
  } finally { f.remove(); }
});

test('mudança no grego nunca reaproveita um índice numérico para outra forma', () => {
  const f = fixture({ greek: ['outro'], anchorGreek: ['λόγος'], associations: [association] });
  try {
    const renderer = createGlobalRenderer({ root: f.root }); renderer.transform(f.html);
    assert.equal(renderer.report().totals.contextConfirmedTokens, 0);
    assert.match(renderer.report().issues[0].issues[0], /sequência grega/);
  } finally { f.remove(); }
});

test('grupos representam associação conjunta; grupos distintos representam alternativas', () => {
  const f = fixture({ text: 'Nela', greek: ['ἐν', 'αὐτῷ'], associations: [{ position: 1, text: 'Nela', groups: [{ tokens: [1, 2] }] }] });
  try {
    const renderer = createGlobalRenderer({ root: f.root }); const html = renderer.transform(f.html);
    assert.match(decoded(html), /ἐν/); assert.match(decoded(html), /αὐτῷ/);
    assert.equal(renderer.report().totals.alternatives, 0);
    assert.equal(renderer.report().totals.contextConfirmedTokens, 1);
  } finally { f.remove(); }
});

test('expressão atravessa tags sem perder texto ou remover marcações', () => {
  const f = fixture({ text: 'por <em>meio</em> de', greek: ['διά'], entries: { 'por meio de': { forms: ['διά'] } } });
  try {
    const renderer = createGlobalRenderer({ root: f.root }); const html = renderer.transform(f.html);
    const doc = parseDocument(html); const controls = findAll(node => node.attribs?.class === 'bible-original-content', doc.children);
    assert.equal(controls.length, 3);
    assert.match(html, /<em>/);
    controls.forEach(removeElement);
    assert.equal(textContent(doc), 'por meio de');
    assert.equal(renderer.report().totals.tooltips, 1);
    assert.equal(renderer.report().totals.displayedTokens, 3);
  } finally { f.remove(); }
});

test('auditorias distinguem cobertura insuficiente de alternativas e suprimentos explícitos', () => {
  const f = fixture({ text: 'Palavra ausente [veio]' });
  try {
    const renderer = createGlobalRenderer({ root: f.root }); renderer.transform(f.html);
    const reports = renderer.reports();
    assert.ok(reports.coverage.terms.some(item => item.term === 'ausente' && item.status === 'PENDENTE'));
    assert.ok(!reports.coverage.terms.some(item => item.term === 'veio'));
    assert.equal(reports.ambiguities.terms[0].term, 'palavra');
    assert.equal(reports.summary.totals.suppliedExplicitTokens, 1);
    assert.equal(reports.summary.totals.contextConfirmedTokens, 0);
  } finally { f.remove(); }
});

test('âncoras persistentes inválidas são erros de configuração, não decisões silenciosas', () => {
  const f = fixture({ associations: [{ ...association, position: 1 }] });
  try { assert.throws(() => loadExceptions(f.root), /âncora/); } finally { f.remove(); }
});
