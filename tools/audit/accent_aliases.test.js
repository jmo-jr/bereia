const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const { regularAccentPair, targetSignature, validateAliasEvidence } = require('../../src/lib/greek-accent-aliases');
const { createEnhanceTokenWithDict } = require('../../src/_data/nt');
const root = path.resolve(__dirname, '../..');
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));

function fixture() {
  const entry = { strongs: '2570', grego: 'καλός', abrev_morf: 'Adj-NMS', morfologia: 'Adjetivo - Nominativo Masculino Singular', pt: 'bom' };
  const dict = { 'καλός': entry }, index = { 'καλός': [{ strongs: '2570', flexao: 0 }] };
  const manifest = { schema_version: 1, regra: 'agudo_grave_final_contextual_v1', origens_controladas: ['καλὸς'],
    aliases: [{ id: 'alias-test', origem: 'καλὸς', destino: { strongs: '2570', flexao: 0, grego: 'καλός', assinatura: targetSignature(entry) },
      ocorrencias_forma_tm: 2, referencias: ['MT 1:1#1'] }] };
  const context = { corpus: 'nt', bookId: 'MT', chapterNumber: 1, verseNumber: 1, tokenPosition: 1 };
  const policy = { manifest, validBooks: new Set(['MT']) };
  return { entry, dict, index, manifest, context, policy };
}

test('somente agudo/grave final; interrogativos, elisão e demais marcas ficam fora', () => {
  assert(regularAccentPair('Καλὸς'.normalize('NFD'), 'καλός'));
  for (const [a, b] of [['τὶς', 'τίς'], ['τὶ', 'τί'], ['τὶνος', 'τίνος'], ['ἀρχῇ', 'ἀρχή'], ['γάμων', 'γαμῶν'], ['νὺχθ᾽', 'νύχθ᾽']]) {
    assert.equal(regularAccentPair(a, b), false, a);
  }
});

test('o alias requer a referência e preserva a grafia; contexto diferente não usa fallback', () => {
  const f = fixture();
  const lookup = createEnhanceTokenWithDict(f.dict, { record() {} }, [], f.index, f.policy);
  const token = { lemma: 'καλὸς' };
  const result = lookup(token, f.context);
  assert.equal(result.lemma, token.lemma);
  assert.equal(result.grego, 'καλός');
  assert.equal(result.pt, 'bom');
  assert.equal(result.alias_dicionario.referencia, 'MT 1:1#1');
  assert.equal(result.ocorrencias_forma_tm, 2);
  for (const context of [{}, { ...f.context, verseNumber: 2 }, { ...f.context, corpus: 'lxx' }]) {
    const pending = lookup(token, context);
    assert.equal(pending.consulta_dicionario, 'alias_acento_pendente');
    assert.equal(pending.pt, undefined);
  }
});

test('literal tem prioridade; mudanças de glosa propagam e análise alterada bloqueia', () => {
  const f = fixture(); f.entry.pt = 'revisado';
  let lookup = createEnhanceTokenWithDict(f.dict, { record() {} }, [], f.index, f.policy);
  assert.equal(lookup({ lemma: 'καλὸς' }, f.context).pt, 'revisado');
  f.entry.abrev_morf = 'Adj-AMS';
  lookup = createEnhanceTokenWithDict(f.dict, { record() {} }, [], f.index, f.policy);
  assert.equal(lookup({ lemma: 'καλὸς' }, f.context).motivo_dicionario, 'destino_desatualizado');
  f.dict['καλὸς'] = { strongs: '999', grego: 'καλὸς', pt: 'entrada direta' };
  lookup = createEnhanceTokenWithDict(f.dict, { record() {} }, [], f.index, f.policy);
  assert.equal(lookup({ lemma: 'καλὸς' }, f.context).pt, 'entrada direta');
});

test('evidência alterada invalida o livro, sem afetar o texto', () => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-alias-'));
  try {
    const paths = ['src/interlinear/nt/MT.json', 'tools/tmnt/with-parsing/MAT.csv'];
    const hashes = {};
    for (const p of paths) { fs.mkdirSync(path.dirname(path.join(temporary, p)), { recursive: true }); fs.writeFileSync(path.join(temporary, p), 'original'); hashes[p] = crypto.createHash('sha256').update('original').digest('hex'); }
    const manifest = { evidencia_por_livro: { MT: hashes } };
    assert(validateAliasEvidence(manifest, temporary).has('MT'));
    fs.writeFileSync(path.join(temporary, paths[0]), 'alterado');
    assert(!validateAliasEvidence(manifest, temporary).has('MT'));
  } finally { fs.rmSync(temporary, { recursive: true, force: true }); }
});

test('lista real: cada ocorrência comprovada resolve, demais origens ficam pendentes', () => {
  const manifest = read('src/_data/nt/greek_accent_aliases.json');
  const dict = read('src/_data/nt/dict_flex_nt-lxx_greek-pt.json');
  const index = read('src/_data/nt/dict_form_index_nt-lxx_greek-pt.json');
  const policy = { manifest, validBooks: validateAliasEvidence(manifest, root) };
  const lookup = createEnhanceTokenWithDict(dict, { record() {} }, [], index, policy);
  const direct = new Set(Object.keys(dict).map(f => f.toLowerCase().normalize('NFC')));
  for (const alias of manifest.aliases) for (const reference of alias.referencias) {
    const [bookId, position] = reference.split(' ');
    const [cv, tokenPosition] = position.split('#');
    const [chapterNumber, verseNumber] = cv.split(':');
    const result = lookup({ lemma: alias.origem }, { corpus: 'nt', bookId, chapterNumber, verseNumber, tokenPosition });
    if (direct.has(alias.origem.toLowerCase().normalize('NFC'))) continue;
    assert.equal(result.consulta_dicionario, 'alias_agudo_grave', reference);
    assert.equal(result.grego, alias.destino.grego, reference);
    assert.equal(result.strongs, alias.destino.strongs, reference);
    assert.equal(result.lemma, alias.origem);
  }
});

test('HTML mantém a grafia do TM e transmite somente o destino validado ao painel', async () => {
  const { Liquid } = require('liquidjs');
  const f = fixture();
  const token = createEnhanceTokenWithDict(f.dict, { record() {} }, [], f.index, f.policy)({ lemma: 'καλὸς' }, f.context);
  const engine = new Liquid({ root: path.join(root, 'src/_includes'), extname: '.liquid' });
  engine.registerFilter('addZeros', value => String(value).padStart(4, '0'));
  const html = await engine.renderFile('interlinearChapter.liquid', {
    entry: { bookName: 'Teste', chapter: { number: 1, pericopes: [{ id: 'P001', verses: [{ number: 1, tokens: [token] }] }] } },
  });
  assert.match(html, /data-dictionary-form="καλός"/);
  assert.match(html, /class="greek tooltip"[^>]*>καλὸς<\/span>/);
  assert.match(html, /class="translate">bom<\/span>/);
});
