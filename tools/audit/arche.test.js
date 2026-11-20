const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');
const { createEnhanceTokenWithDict } = require('../../src/_data/nt');
const ROOT = path.resolve(__dirname, '../..');
const read = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const dictionary = read('src/_data/nt/dict_flex_nt-lxx_greek-pt.json');
const lexical = read('src/_data/nt/dict_lex_nt-lxx_greek-pt.json');

test('consulta real separa nominativo e dativo, inclusive em NFC decomposto', () => {
  const missing = [];
  const lookup = createEnhanceTokenWithDict(dictionary, { record: t => missing.push(t) });
  for (const form of ['ἀρχῇ', 'ἀρχῇ'.normalize('NFD')]) {
    const result = lookup({ lemma: form });
    assert.equal(result.lemma, form);
    assert.equal(result.grego, 'ἀρχῇ');
    assert.equal(result.strongs, '746');
    assert.equal(result.abrev_morf, 'S-DFS');
    assert.equal(result.traducao, 'no princípio, ao principado');
    assert.equal(result.pt, 'no princípio');
  }
  assert.equal(lookup({ lemma: 'ἀρχή' }).abrev_morf, 'S-NFS');
  assert.equal(lookup({ lemma: 'ἀρχή' }).pt, 'princípio');
  // O piloto não remove cobertura legada de acentos contextuais.
  assert.equal(lookup({ lemma: 'ἀρχὴ' }).abrev_morf, 'S-NFS');
  assert.deepEqual(missing, []);
});

test('cinco ocorrências do TM retornam a flexão aprovada; contagens NT/LXX são exatas', () => {
  const lookup = createEnhanceTokenWithDict(dictionary, { record() { assert.fail('Ausência inesperada'); } });
  const refs = [];
  let lxx = 0;
  for (const testament of ['nt', 'at']) {
    const directory = path.join(ROOT, 'src/interlinear', testament);
    for (const file of fs.readdirSync(directory).filter(f => f.endsWith('.json')).sort()) {
      for (const chapter of JSON.parse(fs.readFileSync(path.join(directory, file), 'utf8'))) {
        const verses = chapter.pericopes?.length ? chapter.pericopes.flatMap(p => p.verses) : chapter.verses;
        for (const verse of verses) verse.tokens.forEach((token, position) => {
          if (token.lemma.normalize('NFC') !== 'ἀρχῇ') return;
          if (testament === 'at') { lxx++; return; }
          refs.push(`${file} ${chapter.chapter}:${verse.verse}#${position + 1}`);
          assert.equal(lookup(token).abrev_morf, 'S-DFS');
          assert.equal(lookup(token).pt, 'no princípio');
        });
      }
    }
  }
  assert.deepEqual(refs, ['AT.json 11:15#19', 'FP.json 4:15#8', 'JO.json 1:1#2', 'JO.json 1:2#4', 'LC.json 20:20#18']);
  assert.equal(dictionary['ἀρχῇ'].ocorrencias, String(refs.length));
  assert.equal(dictionary['ἀρχῇ'].ocorrencias_lxx, lxx);
  const index = read('src/_data/nt/dict_form_index_nt-lxx_greek-pt.json');
  assert.deepEqual(index['ἀρχῇ'], [{ strongs: '746', flexao: 6 }]);
});

test('auditoria Python e consulta JavaScript concordam para todas as formas do inventário', () => {
  const parent = path.join(ROOT, 'reports/audit');
  fs.mkdirSync(parent, { recursive: true });
  const temporary = fs.mkdtempSync(path.join(parent, 'test-lookup-'));
  let inventory;
  try {
    execFileSync('python3', ['-B', 'tools/audit/audit_tm.py', '--output', temporary], { cwd: ROOT });
    inventory = JSON.parse(fs.readFileSync(path.join(temporary, 'inventario.json'), 'utf8'));
  } finally { fs.rmSync(temporary, { recursive: true, force: true }); }
  const lookup = createEnhanceTokenWithDict(dictionary, { record() {} });
  assert.equal(inventory.consulta_modo, 'literal_nfc_antes_do_fallback_legado');
  for (const row of inventory.formas) {
    const actual = lookup({ lemma: row.forma_tm });
    const expected = row.consulta_atual;
    for (const field of ['strongs', 'grego', 'abrev_morf', 'morfologia']) {
      assert.equal(actual[field] ?? null, expected?.[field] ?? null, `${row.forma_tm}/${field}`);
    }
  }
});

// DOM mínimo para executar o script real do painel e observar o conteúdo
// apresentado após o evento, sem substituir sua lógica de seleção.
class Element {
  constructor(tag = '') { this.tag = tag; this.children = []; this.attrs = {}; this.dataset = {}; }
  set textContent(text) { this.children = [String(text ?? '')]; }
  get textContent() { return this.children.map(c => typeof c === 'string' ? c : c.textContent).join(''); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  setAttribute(key, value) { this.attrs[key] = value; }
  getAttribute(key) { return this.attrs[key]; }
  focus() {}
  contains() { return true; }
  get classList() { return { add() {}, remove() {} }; }
  addEventListener() {}
}

async function renderDrawer(word, flexoes) {
  const drawer = new Element();
  drawer.hidden = true;
  const body = new Element(), title = new Element();
  drawer.querySelector = selector => selector === 'h1' ? title : selector === '.drawer-body' ? body : new Element();
  const greek = new Element(); greek.textContent = word;
  const translation = new Element(); translation.textContent = 'Glosa da ocorrência';
  const token = { querySelector: selector => selector === '.greek' ? greek : selector === '.translate' ? translation : null };
  const link = new Element(); link.dataset.strong = 'G746';
  link.closest = selector => selector === '.token' ? token : link;
  const listeners = [];
  const document = {
    querySelector: () => drawer, createElement: tag => new Element(tag), createTextNode: text => String(text),
    addEventListener: (name, callback) => { if (name === 'click') listeners.push(callback); },
  };
  vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'src/assets/js/strong-drawer.js'), 'utf8'), {
    document, Node: Element, console: { log() {} },
    fetch: async () => ({ ok: true, json: async () => ({ verbetes: { G746: { ...lexical['746'], flexoes, hebraico: [] } } }) }),
  });
  for (const callback of listeners) await callback({ target: link, button: 0, preventDefault() {} });
  return body;
}

test('painel apresenta apenas o dativo, preservando todas as análises NFC da mesma forma', async () => {
  const body = await renderDrawer('ἀρχῇ'.normalize('NFD'), lexical['746'].flexoes);
  assert.equal(body.children.filter(c => c.tag === 'h2').length, 1);
  assert.match(body.textContent, /Dativo/);
  assert.doesNotMatch(body.textContent, /Nominativo|Acusativo|Genitivo/);
  assert.match(body.textContent, /5 no Texto Majoritário/);
  assert.match(body.textContent, /22 na LXX/);
  const same = { ...lexical['746'].flexoes[6], grego: 'ἀρχῇ'.normalize('NFD') };
  const multiple = await renderDrawer('ἀρχῇ', [...lexical['746'].flexoes, same]);
  assert.equal(multiple.children.filter(c => c.tag === 'h2').length, 2);
});

test('painel não atribui morfologia de candidatos por caixa ou remoção de marcas', async () => {
  for (const word of ['Ἀρχῇ', 'αρχη']) {
    const body = await renderDrawer(word, lexical['746'].flexoes);
    assert.equal(body.children.filter(c => c.tag === 'h2').length, 0);
    assert.doesNotMatch(body.textContent, /Dativo|Nominativo|Acusativo|Genitivo/);
    assert.match(body.textContent, /Glosa da ocorrência/);
  }
});
