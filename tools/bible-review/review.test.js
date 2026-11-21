const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const { generateIndex } = require('../bible-reverse-index');
const { generate } = require('../bible-proposals/generate');
const { exportReview, importReview, readRows, COLUMNS } = require('./review');
const { encode, parse } = require('./csv');
const { setValue } = require('./json-patch');

function fixture(existing = false) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-review-'));
  const write = (name, content) => { const file = path.join(root, name); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, typeof content === 'string' ? content : JSON.stringify(content)); };
  write('src/_data/ntBooks.json', [{ permalink: '/interlinear/jo/', bkpermalink: '/biblia/joao/', chapters: 2 }]);
  write('src/_data/nt/dict_flex_nt-lxx_greek-pt.json', { 'λόγος': { grego: 'λόγος', pt: 'palavra' }, 'θεός': { grego: 'θεός', pt: 'Deus' } });
  write('src/interlinear/nt/JO.json', [{ chapter: 2, pericopes: [{ verses: [
    { verse: 1, tokens: [{ lemma: 'λόγος' }, { lemma: 'θεός' }] },
    { verse: 2, tokens: [{ lemma: 'ἄλλος' }, { lemma: 'λόγος' }] },
  ] }] }]);
  const source = '---\nbookAbbrev: jo\nbookChapter: 2\n---\n{% verse bookAbbrev bookChapter 1 %}Palavra Deus{% endverse %}\n{% verse bookAbbrev bookChapter 2 %}Outra Palavra{% endverse %}';
  write('src/biblia/nt/joao/2.liquid', source);
  const target = path.join(root, 'src/alinhamentos/jo/2.json');
  const preserved = '"2" : { "text":"Outra Palavra", "greek":["ἄλλος","λόγος"], "segments":[{"start":0,"text":"Outra","tokens":[1]},{"start":6,"text":"Palavra","tokens":[2]}], "notes":["PRESERVAR EXATAMENTE"] }';
  if (existing) write('src/alinhamentos/jo/2.json', '{\n "sourceBook" : "JO",\n "verses" : {\n  ' + preserved + '\n }\n}\n');
  generateIndex({ root });
  generate({ root, book: 'jo', chapter: 2, includeApproved: true });
  const csv = exportReview({ root, book: 'jo', chapter: 2 }).files[0];
  return { root, csv, target, preserved, write,
    rows() { return readRows(fs.readFileSync(this.csv, 'utf8')); },
    edit(fn) { const rows = this.rows(); fn(rows); fs.writeFileSync(this.csv, encode([COLUMNS, ...rows.map(row => COLUMNS.map(column => row[column]))])); },
    remove() { fs.rmSync(root, { recursive: true }); },
  };
}
const choose = rows => rows.find(row => row.referencia === 'jo 2:1' && row.tipo === 'VINCULO' && row.trecho_pt === 'Palavra');

test('CSV preserva grego, separadores, aspas, quebras e caracteres de fórmula sem executar nada', () => {
  const rows = [['texto', 'grego'], ['a; "b"\nc', 'ἀρχῇ'], ['=1+1', '+2'], ["'=literal", "'Palavra"], ['-3', '@SUM(A1)']];
  assert.deepEqual(parse(encode(rows)), rows);
  assert.throws(() => parse('"texto'), /aspas não fechadas/);
  assert.throws(() => parse('"texto"fora;campo'), /fora das aspas/);
});

test('CSV novo não aprova vínculos e exportação protege revisões já editadas', () => {
  const f = fixture();
  try {
    assert.ok(fs.readFileSync(f.csv, 'utf8').startsWith('\uFEFF'));
    assert.ok(f.rows().every(row => row.decisao === ''));
    assert.equal(importReview({ root: f.root, file: f.csv, apply: true }).changed, false);
    assert.equal(fs.existsSync(f.target), false);
    f.edit(rows => { choose(rows).observacao = 'Conferido; ainda em revisão.'; });
    assert.throws(() => exportReview({ root: f.root, book: 'jo', chapter: 2 }), /preservada/);
  } finally { f.remove(); }
});

test('conferência não escreve; aplicação parcial cria somente o vínculo escolhido e pendências', () => {
  const f = fixture();
  try {
    f.edit(rows => { choose(rows).decisao = 'APROVAR'; });
    const preview = importReview({ root: f.root, file: f.csv });
    assert.equal(preview.changed, true); assert.equal(preview.applied, false);
    assert.equal(fs.existsSync(f.target), false);
    const result = importReview({ root: f.root, file: f.csv, apply: true });
    const data = JSON.parse(fs.readFileSync(f.target, 'utf8'));
    assert.equal(result.applied, true);
    assert.equal(data.verses[1].segments.length, 1);
    assert.deepEqual(data.verses[1].segments[0].tokens, [1]);
    assert.equal(data.verses[1].pendingReview.length, 2);
    assert.ok(fs.existsSync(result.receipt));
    assert.throws(() => importReview({ root: f.root, file: f.csv, apply: true }), /Fonte mudou/);
  } finally { f.remove(); }
});

test('aprovações conflitantes ou posições inválidas abortam o lote inteiro antes de escrever', () => {
  const f = fixture();
  try {
    f.edit(rows => { for (const row of rows.filter(row => row.referencia === 'jo 2:1' && row.tipo === 'VINCULO')) { row.decisao = 'APROVAR'; row.tokens_gregos = '2'; } });
    assert.throws(() => importReview({ root: f.root, file: f.csv, apply: true }), /disputado/);
    assert.equal(fs.existsSync(f.target), false);
    f.edit(rows => { for (const row of rows) row.decisao = ''; choose(rows).decisao = 'APROVAR'; choose(rows).tokens_gregos = '99'; });
    assert.throws(() => importReview({ root: f.root, file: f.csv, apply: true }), /inválido/);
    assert.equal(fs.existsSync(f.target), false);
  } finally { f.remove(); }
});

test('fonte ou dicionário alterados depois da exportação bloqueiam a importação', () => {
  const f = fixture();
  try {
    f.edit(rows => { choose(rows).decisao = 'APROVAR'; });
    fs.appendFileSync(path.join(f.root, 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json'), ' ');
    assert.throws(() => importReview({ root: f.root, file: f.csv, apply: true }), /Fonte mudou/);
    assert.equal(fs.existsSync(f.target), false);
  } finally { f.remove(); }
});

test('ids e colunas de referência não podem ser alterados ou duplicados', () => {
  const f = fixture();
  try {
    const original = fs.readFileSync(f.csv, 'utf8');
    f.edit(rows => { rows[0].id = 'outro'; });
    assert.throws(() => importReview({ root: f.root, file: f.csv }), /ID desconhecido/);
    fs.writeFileSync(f.csv, original);
    f.edit(rows => { rows.push({ ...rows[0] }); });
    assert.throws(() => importReview({ root: f.root, file: f.csv }), /ID duplicado/);
    fs.writeFileSync(f.csv, original);
    f.edit(rows => { rows[0].texto_versiculo = 'Alterado'; });
    assert.throws(() => importReview({ root: f.root, file: f.csv }), /referência/);
  } finally { f.remove(); }
});

test('reordenação e filtragem de linhas não apagam vínculos aprovados nem reformatam outros versículos', () => {
  const f = fixture(true);
  try {
    f.edit(rows => { const row = choose(rows); row.decisao = 'APROVAR'; rows.splice(0, rows.length, row); });
    importReview({ root: f.root, file: f.csv, apply: true });
    const raw = fs.readFileSync(f.target, 'utf8');
    assert.ok(raw.includes(f.preserved));
    assert.equal(JSON.parse(raw).verses[2].segments.length, 2);
    assert.ok(raw.indexOf('"2"') < raw.indexOf('"1"'));
  } finally { f.remove(); }
});

test('rejeição explícita retira só o vínculo aprovado indicado e registra o que ficou pendente', () => {
  const f = fixture(true);
  try {
    f.edit(rows => { const row = rows.find(row => row.referencia === 'jo 2:2' && row.trecho_pt === 'Palavra' && row.tipo === 'VINCULO'); row.decisao = 'REJEITAR'; row.observacao = 'Revisar a ocorrência.'; });
    importReview({ root: f.root, file: f.csv, apply: true });
    const entry = JSON.parse(fs.readFileSync(f.target, 'utf8')).verses[2];
    assert.deepEqual(entry.segments.map(item => item.text), ['Outra']);
    assert.equal(entry.pendingReview.length, 2);
    assert.ok(fs.readFileSync(f.target, 'utf8').includes('"notes":["PRESERVAR EXATAMENTE"]'));
  } finally { f.remove(); }
});

test('nota sem candidato requer justificativa e permite cadastrar suprimento português', () => {
  const f = fixture();
  try {
    f.edit(rows => {
      const row = rows.find(row => row.referencia === 'jo 2:2' && row.tipo === 'PORTUGUES_SEM_CANDIDATO');
      row.decisao = 'APROVAR'; row.tipo = 'PORTUGUES_SEM_VINCULO_DIRETO';
    });
    assert.throws(() => importReview({ root: f.root, file: f.csv }), /justificativa/);
    f.edit(rows => { rows.find(row => row.decisao === 'APROVAR').observacao = 'Suprimento conferido na ocorrência.'; });
    importReview({ root: f.root, file: f.csv, apply: true });
    assert.equal(JSON.parse(fs.readFileSync(f.target, 'utf8')).verses[2].unlinkedPortuguese[0].text, 'Outra');
  } finally { f.remove(); }
});

test('alteração mecânica de espaços reposiciona vínculos existentes sem perdê-los', () => {
  const f = fixture(true);
  try {
    const source = path.join(f.root, 'src/biblia/nt/joao/2.liquid');
    fs.writeFileSync(source, fs.readFileSync(source, 'utf8').replace('Outra Palavra', 'Outra  Palavra'));
    generate({ root: f.root, book: 'jo', chapter: 2, includeApproved: true });
    const exported = exportReview({ root: f.root, book: 'jo', chapter: 2, outDir: path.join(f.root, 'reports/revised') });
    const rows = readRows(fs.readFileSync(exported.files[0], 'utf8'));
    rows.find(row => row.referencia === 'jo 2:2' && row.trecho_pt === 'Palavra' && row.tipo === 'VINCULO').decisao = 'APROVAR';
    fs.writeFileSync(exported.files[0], encode([COLUMNS, ...rows.map(row => COLUMNS.map(column => row[column]))]));
    importReview({ root: f.root, file: exported.files[0], apply: true });
    const entry = JSON.parse(fs.readFileSync(f.target, 'utf8')).verses[2];
    assert.equal(entry.text, 'Outra  Palavra'); assert.equal(entry.segments.length, 2);
    assert.equal(entry.segments[1].start, 7);
  } finally { f.remove(); }
});

test('arquivo JSON recebe alterações localizadas sem reordenar ou normalizar entradas vizinhas', () => {
  const raw = '{\r\n "sourceBook" : "JO",\r\n "verses" : {"2":{"text":"β","segments":[]}}\r\n}\r\n';
  let changed = setValue(raw, ['verses', '1'], { text: 'ἀρχῇ', segments: [] });
  assert.ok(changed.includes('"2":{"text":"β","segments":[]}'));
  assert.ok(changed.includes('\r\n'));
  changed = setValue(changed, ['verses', '1', 'segments'], [{ start: 0, text: 'ἀρχῇ', tokens: [1] }]);
  assert.equal(JSON.parse(changed).verses[1].segments[0].text, 'ἀρχῇ');
});

test('aprovação parcial é visível como pendência no renderizador real', () => {
  const f = fixture();
  try {
    f.edit(rows => { choose(rows).decisao = 'APROVAR'; });
    importReview({ root: f.root, file: f.csv, apply: true });
    const vm = require('node:vm'), { createRequire } = require('node:module');
    const filename = path.resolve('src/lib/bible-alignment.js');
    const sandbox = { module: { exports: {} }, __dirname: path.join(f.root, 'src/lib'), require: createRequire(filename) };
    vm.runInNewContext(fs.readFileSync(filename, 'utf8'), sandbox, { filename });
    const render = sandbox.module.exports.createRenderer();
    assert.match(render('Palavra Deus', 'jo', 2, 1), /bible-original/);
    assert.equal(render.records.get('jo 2:1').pending.length, 2);
  } finally { f.remove(); }
});

test('edição de trecho e tokens permite aprovar expressão de vários originais', () => {
  const f = fixture();
  try {
    f.edit(rows => { const row = choose(rows); row.decisao = 'APROVAR'; row.trecho_pt = 'Palavra Deus'; row.tokens_gregos = '1,2'; row.observacao = 'Expressão conferida.'; });
    importReview({ root: f.root, file: f.csv, apply: true });
    const entry = JSON.parse(fs.readFileSync(f.target, 'utf8')).verses[1];
    assert.equal(entry.segments.length, 1);
    assert.deepEqual(entry.segments[0].tokens, [1, 2]);
    assert.equal(entry.segments[0].reviewNote, 'Expressão conferida.');
    assert.equal(entry.pendingReview, undefined);
  } finally { f.remove(); }
});

test('linha sem candidato pode virar vínculo e a geração futura mantém revisão parcial no escopo', () => {
  const f = fixture();
  try {
    f.edit(rows => { const row = rows.find(row => row.referencia === 'jo 2:2' && row.tipo === 'PORTUGUES_SEM_CANDIDATO'); row.decisao = 'APROVAR'; row.tipo = 'VINCULO'; row.tokens_gregos = '1'; });
    importReview({ root: f.root, file: f.csv, apply: true });
    assert.deepEqual(JSON.parse(fs.readFileSync(f.target, 'utf8')).verses[2].segments[0].tokens, [1]);
    const result = generate({ root: f.root, book: 'jo', chapter: 2 });
    assert.equal(result.summary.totals.skippedApproved, 0);
    const document = JSON.parse(fs.readFileSync(path.join(result.output, 'jo/2.json'), 'utf8'));
    assert.ok(document.verses[2].relations.some(item => item.text === 'Outra' && item.status === 'APROVADA'));
  } finally { f.remove(); }
});

test('PENDENTE não retira vínculos existentes e rejeição de proposta não cria arquivo aprovado', () => {
  const f = fixture(true);
  try {
    const before = fs.readFileSync(f.target, 'utf8');
    f.edit(rows => { rows.find(row => row.referencia === 'jo 2:2' && row.tipo === 'VINCULO').decisao = 'PENDENTE'; choose(rows).decisao = 'REJEITAR'; });
    const result = importReview({ root: f.root, file: f.csv, apply: true });
    assert.equal(result.changed, false);
    assert.equal(fs.readFileSync(f.target, 'utf8'), before);
    const receipt = JSON.parse(fs.readFileSync(result.receipt, 'utf8'));
    assert.equal(receipt.decisions.length, 2);
  } finally { f.remove(); }
});

test('erro no recibo é identificado antes de alterar aprovados', () => {
  const f = fixture();
  try {
    f.edit(rows => { choose(rows).decisao = 'APROVAR'; });
    const hash = crypto.createHash('sha256').update(fs.readFileSync(f.csv, 'utf8')).digest('hex').slice(0, 12);
    fs.mkdirSync(f.csv.replace(/\.csv$/u, '') + `.import-${hash}.json`);
    assert.throws(() => importReview({ root: f.root, file: f.csv, apply: true }), /Recibo/);
    assert.equal(fs.existsSync(f.target), false);
  } finally { f.remove(); }
});

test('arquivo em separador vírgula continua importável após exportação por outra planilha', () => {
  const f = fixture();
  try {
    const rows = f.rows(); choose(rows).decisao = 'APROVAR';
    const lines = [COLUMNS, ...rows.map(row => COLUMNS.map(column => row[column]))];
    fs.writeFileSync(f.csv, lines.map(row => row.map(value => '"' + String(value).replaceAll('"', '""') + '"').join(',')).join('\r\n'));
    assert.equal(importReview({ root: f.root, file: f.csv }).approved, 1);
  } finally { f.remove(); }
});

test('marcação interna impede aprovar vínculo, mas permite registrar rejeição sem publicação', () => {
  const f = fixture();
  try {
    const source = path.join(f.root, 'src/biblia/nt/joao/2.liquid');
    fs.writeFileSync(source, fs.readFileSync(source, 'utf8').replace('Palavra Deus', 'Palavra <em>Deus</em>'));
    generate({ root: f.root, book: 'jo', chapter: 2, includeApproved: true });
    f.csv = exportReview({ root: f.root, book: 'jo', chapter: 2, outDir: path.join(f.root, 'reports/marked') }).files[0];
    f.edit(rows => { const row = rows.find(row => row.referencia === 'jo 2:1'); row.decisao = 'APROVAR'; row.tipo = 'VINCULO'; row.trecho_pt = 'Palavra'; row.inicio_pt = '0'; row.tokens_gregos = '1'; });
    assert.throws(() => importReview({ root: f.root, file: f.csv, apply: true }), /marcação interna/);
    assert.equal(fs.existsSync(f.target), false);
    f.edit(rows => { rows.find(row => row.decisao === 'APROVAR').decisao = 'REJEITAR'; });
    assert.equal(importReview({ root: f.root, file: f.csv, apply: true }).changed, false);
  } finally { f.remove(); }
});
