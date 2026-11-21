const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const { buildIndex, lookup, generateIndex, lookupFile, readSource } = require('./bible-reverse-index');
const dictionary = {
  'λόγος': { grego: 'λόγος', pt: 'palavra', traducao: 'palavra, declaração, discurso', strongs: '3056' },
  'λόγου': { grego: 'λόγου', pt: 'palavra', traducao: 'de palavra', strongs: '3056' },
  'ῥῆμα': { grego: 'ῥῆμα', pt: 'declaração', traducao: 'dito' },
  'διά': { grego: 'διά', pt: 'por meio de', traducao: 'por meio de; através de' },
};
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const source = { dictionary, hash: hash(JSON.stringify(dictionary)) };

test('índice guarda referências aos campos, sem duplicar metadados ou alterar o dicionário', () => {
  const original = JSON.stringify(dictionary);
  const index = buildIndex(dictionary, source.hash);
  assert.equal(JSON.stringify(dictionary), original);
  assert.equal(index.terms.palavra.length, 3);
  assert.deepEqual(index.terms.palavra[0], { dictionaryKey: 'λόγος', field: 'pt', text: 'palavra' });
  assert.equal(index.terms.palavra[0].morfologia, undefined);
  assert.equal(index.statistics.dictionaryEntries, 4);
});

test('consultas mantêm acentos e expressões completas, normalizando caixa e espaços', () => {
  const data = { ...dictionary, 'α': { pt: 'é', traducao: 'e' }, 'β': { pt: 'É', traducao: 'é' } };
  const snapshot = { dictionary: data, hash: 'hash' };
  const index = buildIndex(data, snapshot.hash);
  assert.equal(lookup(index, snapshot, ' POR   MEIO DE ').matches.length, 1);
  assert.equal(lookup(index, snapshot, 'por').matches.length, 0);
  assert.equal(lookup(index, snapshot, 'e').matches.length, 1);
  assert.equal(lookup(index, snapshot, 'é').matches.length, 2);
  assert.equal(lookup(index, snapshot, 'declaracao').matches.length, 0);
});

test('filtro de versículo preserva todas as ocorrências repetidas e os dados originais', () => {
  const result = lookup(buildIndex(dictionary, source.hash), source, 'Palavra', ['λόγος', 'καὶ', 'λόγος', 'λόγον']);
  assert.equal(result.status, 'CANDIDATOS_LEXICAIS_NAO_APROVADOS');
  assert.equal(result.matches.length, 1);
  assert.deepEqual(result.matches[0].greekOccurrences, [{ position: 1, form: 'λόγος' }, { position: 3, form: 'λόγος' }]);
  assert.equal(result.matches[0].data, dictionary['λόγος']);
  assert.equal(result.matches[0].references.length, 2);
});

test('formas gregas com diacríticos diferentes não são confundidas por aproximação', () => {
  const data = { 'ἀρχή': { pt: 'princípio' } };
  const snapshot = { dictionary: data, hash: 'hash' };
  const index = buildIndex(data, snapshot.hash);
  assert.equal(lookup(index, snapshot, 'princípio', ['ἀρχῇ']).matches.length, 0);
  assert.equal(lookup(index, snapshot, 'princípio', ['ἀρχὴ']).matches.length, 1);
});

test('notações e dados insuficientes ficam explicitamente pendentes, sem expandir análises', () => {
  const data = { 'α': { pt: 'eu/ele(a) era', traducao: 'palavra, nota: explicação' }, 'β': { pt: '', traducao: 4 } };
  const index = buildIndex(data, 'hash');
  assert.ok(index.terms.palavra);
  assert.equal(index.terms.eu, undefined);
  assert.equal(index.pending.length, 4);
  assert.equal(index.pending[0].value, 'eu/ele(a) era');
  assert.ok(index.pending.every(item => item.reason));
});

test('índice desatualizado ou com referência inconsistente não é usado silenciosamente', () => {
  const index = buildIndex(dictionary, source.hash);
  assert.throws(() => lookup(index, { ...source, hash: 'outro' }, 'palavra'), /desatualizado/);
  index.terms.palavra[0].field = 'morfologia';
  assert.throws(() => lookup(index, source, 'palavra'), /inconsistente/);
  assert.throws(() => lookup(index, source, ''), /Informe/);
});

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-reverse-index-'));
  const filename = path.join(root, 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json');
  fs.mkdirSync(path.dirname(filename), { recursive: true });
  fs.writeFileSync(filename, JSON.stringify(dictionary, null, 2) + '\n');
  const greek = path.join(root, 'src/interlinear/nt/JO.json');
  fs.mkdirSync(path.dirname(greek), { recursive: true });
  fs.writeFileSync(greek, JSON.stringify([{ chapter: 1, pericopes: [{ verses: [{ verse: 1, tokens: [{ lemma: 'λόγος' }, { lemma: 'λόγος' }] }] }] }]));
  return { root, filename, remove() { fs.rmSync(root, { recursive: true }); } };
}

test('geração é determinística e --check não escreve arquivos', () => {
  const f = fixture();
  try {
    const before = fs.readFileSync(f.filename, 'utf8');
    const missing = generateIndex({ root: f.root, check: true });
    assert.equal(missing.current, false);
    assert.equal(fs.existsSync(path.join(f.root, 'reports')), false);
    generateIndex({ root: f.root });
    const report = fs.readFileSync(path.join(f.root, 'reports/bible-reverse-index.json'), 'utf8');
    assert.equal(generateIndex({ root: f.root, check: true }).current, true);
    assert.equal(generateIndex({ root: f.root }).changed, false);
    assert.equal(fs.readFileSync(path.join(f.root, 'reports/bible-reverse-index.json'), 'utf8'), report);
    assert.equal(fs.readFileSync(f.filename, 'utf8'), before);
    fs.appendFileSync(f.filename, ' ');
    assert.equal(generateIndex({ root: f.root, check: true }).current, false);
    assert.throws(() => lookupFile({ root: f.root, query: 'palavra' }), /desatualizado/);
  } finally { f.remove(); }
});

test('consulta em arquivo valida a referência bíblica e não cria relações aprovadas', () => {
  const f = fixture();
  try {
    assert.throws(() => lookupFile({ root: f.root, query: 'palavra' }), /ainda não gerado/);
    generateIndex({ root: f.root });
    const result = lookupFile({ root: f.root, query: 'palavra', book: 'jo', chapter: 1, verse: 1 });
    assert.equal(result.matches[0].greekOccurrences.length, 2);
    assert.equal(fs.existsSync(path.join(f.root, 'src/alinhamentos')), false);
    assert.throws(() => lookupFile({ root: f.root, query: 'palavra', book: 'jo' }), /informe/);
    assert.throws(() => lookupFile({ root: f.root, query: 'palavra', book: 'jo', chapter: 1, verse: 2 }), /não encontrado/);
    assert.equal(readSource(f.root).hash, buildIndex(dictionary, readSource(f.root).hash).source.sha256);
  } finally { f.remove(); }
});

test('destino por link simbólico não pode atingir as fontes', () => {
  const f = fixture();
  try {
    fs.symlinkSync(path.join(f.root, 'src'), path.join(f.root, 'reports'), 'dir');
    assert.throws(() => generateIndex({ root: f.root }), /link simbólico/);
  } finally { f.remove(); }
});
