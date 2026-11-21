const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { parseDocument } = require('htmlparser2');
const { findAll, textContent, removeElement } = require('domutils');
const { resolve, findMatches } = require('../../src/lib/bible-global-lexicon');
const { createGlobalRenderer } = require('../../src/lib/bible-global-renderer');
const { exportGlobal, importGlobal, COLUMNS } = require('./global');
const { encode, parse } = require('../bible-review/csv');
const dictionary = {
  'λόγος': { grego: 'λόγος', pt: 'palavra', transliteracao: 'logos', morfologia: 'Substantivo - Nominativo Masculino Singular', verbete: 'G3056: palavra' },
  'ῥῆμα': { grego: 'ῥῆμα', pt: 'palavra', transliteracao: 'rhēma', morfologia: 'Substantivo - Nominativo Neutro Singular', verbete: 'G4487: declaração' },
  'ἐν': { grego: 'ἐν', pt: 'em', morfologia: 'Preposição' },
  'αὐτῷ': { grego: 'αὐτῷ', pt: 'ele', morfologia: 'Pronome - Dativo' },
};
const rules = () => ({ version: 1, ambiguityPolicy: 'alternatives', entries: {} });
function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-global-'));
  const write = (name, data) => { const file = path.join(root, name); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n'); };
  write('src/_data/nt/dict_flex_nt-lxx_greek-pt.json', dictionary);
  write('src/tooltip-relations.json', rules());
  write('src/interlinear/nt/JO.json', [2, 3, 4].map(chapter => ({ chapter, pericopes: [{ verses: [{ verse: 1, tokens: (chapter === 2 ? ['λόγος', 'ῥῆμα'] : chapter === 3 ? ['λόγος', 'λόγος'] : ['ἀρχῇ']).map(lemma => ({ lemma })) }] }] })));
  return { root, write, remove() { fs.rmSync(root, { recursive: true }); } };
}
const html = (chapter, text = 'Palavra') => `<html><body><span class="verse" id="jo_${chapter}-1"><span class="verse-text">${text}</span></span></body></html>`;
function visible(markup) { const doc = parseDocument(markup); findAll(node => node.attribs?.class === 'bible-original-content', doc.children).forEach(removeElement); return textContent(doc); }

test('a fonte global funciona em vários capítulos sem arquivos de alinhamento', () => {
  const f = fixture();
  try {
    const renderer = createGlobalRenderer({ root: f.root });
    const one = renderer.transform(html(2)), two = renderer.transform(html(3));
    assert.match(one, /Alternativas lexicais/); assert.match(textContent(parseDocument(one)), /λόγος/); assert.match(textContent(parseDocument(one)), /ῥῆμα/);
    assert.doesNotMatch(two, /Alternativas lexicais/);
    assert.equal(visible(one), 'Palavra'); assert.equal(visible(two), 'Palavra');
    assert.equal(renderer.report().totals.tooltips, 2);
    assert.equal(renderer.report().totals.alternatives, 1);
    assert.equal(fs.existsSync(path.join(f.root, 'src/alinhamentos')), false);
  } finally { f.remove(); }
});

test('expressões agrupam tokens e a comparação não ignora diacríticos de flexões', () => {
  const config = rules(); config.entries.nela = { groups: [['ἐν', 'αὐτῷ']] };
  config.entries['princípio'] = { forms: ['ἀρχή'] };
  const lexicon = resolve(dictionary, config);
  assert.equal(findMatches('Nela', ['Ἐν', 'αὐτῷ'], lexicon)[0].candidates[0].forms.length, 2);
  assert.equal(findMatches('Nela', ['Ἐν'], lexicon).length, 0);
  assert.equal(findMatches('princípio', ['ἀρχῇ'], lexicon).length, 0);
});

test('HTML, entidades e marcações são preservados e os tooltips antigos não são aninhados', () => {
  const f = fixture();
  try {
    const renderer = createGlobalRenderer({ root: f.root });
    const input = html(3, '<cite><span class="redletter">Palavra</span> &amp; <em>Palavra</em></cite> <span class="tooltip" title="Nota">Palavra</span>');
    const output = renderer.transform(input);
    assert.equal(visible(output), 'Palavra & Palavra Palavra');
    assert.match(output, /class="redletter"/); assert.match(output, /title="Nota"/);
    assert.equal(findAll(node => node.attribs?.class === 'bible-original-content', parseDocument(output).children).length, 2);
  } finally { f.remove(); }
});

test('dados de outra flexão não são apresentados como se fossem da forma original', () => {
  const f = fixture();
  try {
    const config = rules(); config.entries['princípio'] = { forms: ['ἀρχῇ'] }; f.write('src/tooltip-relations.json', config);
    const output = createGlobalRenderer({ root: f.root }).transform(html(4, 'princípio'));
    assert.match(textContent(parseDocument(output)), /ἀρχῇ/); assert.match(textContent(parseDocument(output)), /Dados desta flexão não disponíveis/);
    assert.doesNotMatch(output, /Nominativo/);
  } finally { f.remove(); }
});

test('uma edição no CSV global afeta todos os capítulos e não muda o dicionário', () => {
  const f = fixture();
  try {
    const before = fs.readFileSync(path.join(f.root, 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json'), 'utf8');
    const { file } = exportGlobal({ root: f.root });
    const table = parse(fs.readFileSync(file, 'utf8'));
    const item = table.slice(1).find(row => row[0] === 'palavra'); item[1] = 'λόγος';
    fs.writeFileSync(file, encode(table));
    assert.equal(importGlobal({ root: f.root, file }).applied, false);
    assert.equal(importGlobal({ root: f.root, file, apply: true }).changedTerms, 1);
    const renderer = createGlobalRenderer({ root: f.root });
    const first = renderer.transform(html(2)), second = renderer.transform(html(3));
    assert.doesNotMatch(first, /G4487/); assert.match(textContent(parseDocument(first)), /λόγος/); assert.match(textContent(parseDocument(second)), /λόγος/);
    assert.equal(renderer.report().totals.alternatives, 0);
    assert.equal(fs.readFileSync(path.join(f.root, 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json'), 'utf8'), before);
    assert.equal(fs.existsSync(path.join(f.root, 'src/alinhamentos')), false);
  } finally { f.remove(); }
});

test('desativação global e alias novo não exigem aprovar as outras linhas', () => {
  const f = fixture();
  try {
    const { file } = exportGlobal({ root: f.root });
    const table = parse(fs.readFileSync(file, 'utf8'));
    table.find(row => row[0] === 'palavra')[3] = 'não';
    table.push(['verbo', 'λόγος', '', 'sim', 'Alias global conferido.', '', '']);
    fs.writeFileSync(file, encode(table));
    importGlobal({ root: f.root, file, apply: true });
    const renderer = createGlobalRenderer({ root: f.root });
    assert.doesNotMatch(renderer.transform(html(3)), /bible-original-content/);
    assert.match(renderer.transform(html(3, 'Verbo')), /bible-original-content/);
  } finally { f.remove(); }
});

test('CSV global editado não é sobrescrito e fonte antiga ou forma desconhecida não é importada', () => {
  const f = fixture();
  try {
    const { file } = exportGlobal({ root: f.root });
    const table = parse(fs.readFileSync(file, 'utf8')); table.find(row => row[0] === 'palavra')[1] = 'grego inventado';
    fs.writeFileSync(file, encode(table));
    assert.throws(() => exportGlobal({ root: f.root }), /preservado/);
    assert.throws(() => importGlobal({ root: f.root, file, apply: true }), /não encontrada/);
    f.write('src/tooltip-relations.json', { ...rules(), entries: { x: { enabled: false } } });
    assert.throws(() => importGlobal({ root: f.root, file }), /mudou/);
  } finally { f.remove(); }
});

test('id bíblico duplicado não é usado para associar um original errado', () => {
  const f = fixture();
  try {
    const renderer = createGlobalRenderer({ root: f.root });
    const duplicate = html(3).replace('</body>', html(3) + '</body>');
    assert.doesNotMatch(renderer.transform(duplicate), /bible-original-content/);
    assert.ok(renderer.report().issues.length);
  } finally { f.remove(); }
});

test('a fonte global vale inclusive onde há alinhamento antigo, salvo opção explícita de exceção', () => {
  const f = fixture();
  try {
    f.write('src/alinhamentos/jo/3.json', { sourceBook: 'JO', verses: { 1: { text: 'Palavra', greek: ['λόγος', 'λόγος'], segments: [{ start: 0, text: 'Palavra', tokens: [1] }] } } });
    const config = rules(); config.entries.palavra = { enabled: false }; f.write('src/tooltip-relations.json', config);
    assert.doesNotMatch(createGlobalRenderer({ root: f.root }).transform(html(3)), /bible-original-content/);
  } finally { f.remove(); }
});
