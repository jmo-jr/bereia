const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { generateIndex } = require('../bible-reverse-index');
const { generate, readChapters, safeOutput, argumentsFrom } = require('./generate');

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-proposals-'));
  const write = (name, data) => { const file = path.join(root, name); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, typeof data === 'string' ? data : JSON.stringify(data)); };
  write('src/_data/ntBooks.json', [{ permalink: '/interlinear/jo/', bkpermalink: '/biblia/joao/', chapters: 2 }]);
  write('src/_data/nt/dict_flex_nt-lxx_greek-pt.json', { 'λόγος': { pt: 'palavra' } });
  write('src/interlinear/nt/JO.json', [1, 2].map(chapter => ({ chapter, pericopes: [{ verses: [{ verse: 1, tokens: [{ lemma: 'λόγος' }] }, { verse: 2, tokens: [{ lemma: 'λόγος' }] }] }] })));
  write('src/alinhamentos/jo/1.json', { sourceBook: 'JO', verses: { 1: { text: 'Palavra', greek: ['λόγος'], segments: [{ start: 0, text: 'Palavra', tokens: [1] }] } } });
  write('src/biblia/nt/joao/1.liquid', '---\nbookAbbrev: "jo"\nbookChapter: 1\n---\n{% verse bookAbbrev bookChapter 1 %}Palavra{% endverse %}');
  write('src/biblia/nt/joao/1.txt', '1 NÃO USAR ESTA VERSÃO');
  write('src/biblia/nt/joao/2.txt', 'Título\n1 Palavra\n2 <rl>Palavra</rl>\n');
  generateIndex({ root });
  return { root, write, remove() { fs.rmSync(root, { recursive: true }); } };
}
function snapshots(directory) {
  const result = {};
  function walk(folder) { for (const item of fs.readdirSync(folder, { withFileTypes: true })) {
    const file = path.join(folder, item.name);
    if (item.isDirectory()) walk(file); else result[path.relative(directory, file)] = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  } }
  walk(directory); return result;
}

test('lote prefere Liquid, usa TXT sem template e não altera fontes ou aprovados', () => {
  const f = fixture();
  try {
    const before = snapshots(path.join(f.root, 'src'));
    const { summary, output } = generate({ root: f.root });
    assert.equal(summary.totals.skippedApproved, 1);
    assert.equal(summary.totals.verses, 2);
    assert.equal(summary.totals.incompleteVerses, 1);
    assert.equal(summary.totals.missingTranslationVerses, 1);
    const chapter = JSON.parse(fs.readFileSync(path.join(output, 'jo/2.json'), 'utf8'));
    assert.equal(chapter.sourceFormat, 'txt');
    assert.equal(chapter.verses[1].text, 'Palavra');
    assert.equal(chapter.verses[1].segments, undefined);
    assert.equal(chapter.type, 'RELACOES_POR_OCORRENCIA');
    assert.equal(chapter.version, 2);
    assert.ok(chapter.verses[1].relations.length);
    assert.deepEqual(snapshots(path.join(f.root, 'src')), before);
    const first = snapshots(output);
    generate({ root: f.root });
    assert.deepEqual(snapshots(output), first);
  } finally { f.remove(); }
});

test('escopo de livro/capítulo e avaliação excluem a própria referência', () => {
  const f = fixture();
  try {
    const result = generate({ root: f.root, book: 'jo', chapter: 1, evaluate: true });
    assert.equal(result.summary.evaluation.approvedSegments, 1);
    assert.equal(result.summary.evaluation.matchedApprovedSegments, 1);
    const doc = JSON.parse(fs.readFileSync(path.join(result.output, 'jo/1.json'), 'utf8'));
    assert.ok(doc.verses[1].relations.every(candidate => candidate.evidence.every(evidence => evidence.kind === 'indice-reverso-forma-exata')));
    assert.throws(() => readChapters(f.root, { book: 'mt' }), /Livro desconhecido/);
    assert.throws(() => readChapters(f.root, { book: 'jo', chapter: 3 }), /Capítulo inexistente/);
  } finally { f.remove(); }
});

test('saída não pode sobrescrever src, aprovados ou links para as fontes', () => {
  const f = fixture();
  try {
    assert.throws(() => generate({ root: f.root, out: path.join(f.root, 'src/alinhamentos') }), /fora de src/);
    fs.symlinkSync(path.join(f.root, 'src'), path.join(f.root, 'atalho'), 'dir');
    assert.throws(() => safeOutput(f.root, path.join(f.root, 'atalho/novos')), /fora de src/);
    const out = path.join(f.root, 'reports/test'); fs.mkdirSync(out, { recursive: true });
    fs.symlinkSync(path.join(f.root, 'src'), path.join(out, 'jo'), 'dir');
    assert.throws(() => generate({ root: f.root, out, includeApproved: true }), /fora de src/);
  } finally { f.remove(); }
});

test('não omite shortcode desconhecido ou versículo duplicado', () => {
  const f = fixture();
  try {
    f.write('src/biblia/nt/joao/1.liquid', 'bookAbbrev: jo\nbookChapter: 1\n{% verse outro 1 1 %}Palavra{% endverse %}');
    assert.match(readChapters(f.root).missing[0].reason, /shortcode verse/);
    fs.unlinkSync(path.join(f.root, 'src/biblia/nt/joao/1.liquid'));
    f.write('src/biblia/nt/joao/1.txt', '1 Palavra\n1 Palavra\n');
    assert.match(readChapters(f.root).missing[0].reason, /duplicado/);
  } finally { f.remove(); }
});

test('argumentos inválidos são rejeitados antes da geração', () => {
  assert.deepEqual(argumentsFrom(['--book', 'JO', '--chapter', '2']), { book: 'jo', chapter: 2 });
  assert.throws(() => argumentsFrom(['--chapter', '2']), /requer/);
  assert.throws(() => argumentsFrom(['--book']), /Falta/);
  assert.throws(() => argumentsFrom(['--unknown']), /desconhecida/);
});

test('localiza o livro pelos metadados mesmo quando o slug da pasta diverge', () => {
  const f = fixture();
  try {
    fs.renameSync(path.join(f.root, 'src/biblia/nt/joao'), path.join(f.root, 'src/biblia/nt/outro-slug'));
    const inventory = readChapters(f.root, { book: 'jo', chapter: 1 });
    assert.equal(inventory.chapters.length, 1);
    assert.ok(inventory.chapters[0].file.includes('outro-slug'));
  } finally { f.remove(); }
});

test('HTML legado mantém o texto interno original e erros de id ficam no diagnóstico', () => {
  const f = fixture();
  try {
    const prefix = 'bookAbbrev: jo\nbookChapter: 1\n';
    f.write('src/biblia/nt/joao/1.liquid', prefix + '<span id="jo_1-1" class="verse"><span class="verse-number">1</span><span class="verse-text">Palavra <em>viva</em></span></span>');
    const inventory = readChapters(f.root, { book: 'jo', chapter: 1 });
    assert.equal(inventory.chapters[0].format, 'html-em-liquid');
    assert.equal(inventory.chapters[0].verses[0].text, 'Palavra <em>viva</em>');
    f.write('src/biblia/nt/joao/1.liquid', prefix + '<span id="jo_1-1" class="verse"><span class="verse-text">Palavra</span></span>'.repeat(2));
    assert.match(readChapters(f.root, { book: 'jo', chapter: 1 }).missing[0].reason, /duplicado/);
  } finally { f.remove(); }
});

test('continuações TXT são preservadas e sinalizadas, sem absorver a próxima perícope', () => {
  const f = fixture();
  try {
    f.write('src/biblia/nt/joao/2.txt', 'Título\n1 Palavra\ncontinuação\n--\nOutro título\n2 Palavra\n');
    const chapter = readChapters(f.root, { book: 'jo', chapter: 2 }).chapters[0];
    assert.equal(chapter.verses[0].text, 'Palavra\ncontinuação');
    assert.ok(chapter.verses[0].sourceIssues.length);
    assert.equal(chapter.verses[1].text, 'Palavra');
    const result = generate({ root: f.root, book: 'jo', chapter: 2 });
    assert.equal(result.summary.totals.incompleteVerses, 1);
  } finally { f.remove(); }
});

test('gerador exige índice atual e não o regenera silenciosamente', () => {
  const f = fixture();
  try {
    fs.unlinkSync(path.join(f.root, 'reports/bible-reverse-index.json'));
    assert.throws(() => generate({ root: f.root }), /bible:index/);
    generateIndex({ root: f.root });
    fs.appendFileSync(path.join(f.root, 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json'), ' ');
    assert.throws(() => generate({ root: f.root }), /desatualizado/);
  } finally { f.remove(); }
});

test('regeneração preserva arquivo de revisão editado, inclusive status alterado manualmente', () => {
  const f = fixture();
  try {
    const result = generate({ root: f.root, book: 'jo', chapter: 2 });
    const filename = path.join(result.output, 'jo/2.json');
    const document = JSON.parse(fs.readFileSync(filename, 'utf8'));
    document.verses[1].relations[0].status = 'APROVADA';
    fs.writeFileSync(filename, JSON.stringify(document));
    const edited = fs.readFileSync(filename, 'utf8');
    assert.throws(() => generate({ root: f.root, book: 'jo', chapter: 2 }), /Arquivo de revisão editado/);
    assert.equal(fs.readFileSync(filename, 'utf8'), edited);
    assert.equal(JSON.parse(fs.readFileSync(path.join(f.root, 'src/alinhamentos/jo/1.json'), 'utf8')).verses[2], undefined);
  } finally { f.remove(); }
});

test('inclusão de aprovados preserva decisões e avaliação nunca exporta aprovações', () => {
  const f = fixture();
  try {
    const first = generate({ root: f.root, book: 'jo', chapter: 1, includeApproved: true });
    const filename = path.join(first.output, 'jo/1.json');
    let document = JSON.parse(fs.readFileSync(filename, 'utf8'));
    assert.equal(document.verses[1].relations[0].status, 'APROVADA');
    assert.equal(first.summary.totals.approvedRelations, 1);
    const evaluated = generate({ root: f.root, book: 'jo', chapter: 1, evaluate: true });
    document = JSON.parse(fs.readFileSync(path.join(evaluated.output, 'jo/1.json'), 'utf8'));
    assert.ok(document.verses[1].relations.every(item => item.status !== 'APROVADA'));
  } finally { f.remove(); }
});

test('filtros sucessivos mantêm hashes dos outros arquivos sem confundir geração com edição manual', () => {
  const f = fixture();
  try {
    generate({ root: f.root, includeApproved: true });
    generate({ root: f.root, book: 'jo', chapter: 1, includeApproved: true });
    const result = generate({ root: f.root, book: 'jo', chapter: 2 });
    assert.equal(result.summary.chapters.length, 1);
    assert.ok(result.summary.fileHashes['jo/1.json']);
    assert.ok(result.summary.fileHashes['jo/2.json']);
  } finally { f.remove(); }
});
