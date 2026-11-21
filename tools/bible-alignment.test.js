const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { parseDocument } = require('htmlparser2');
const { findAll, textContent, removeElement } = require('domutils');
const { createRenderer } = require('../src/lib/bible-alignment');
const alignment = require('../src/alinhamentos/jo/1.json');
const render = createRenderer();

test('o piloto preserva o texto e distingue cada ocorrência grega', () => {
  const ids = new Set();
  for (const [verse, entry] of Object.entries(alignment.verses)) {
    const html = render(entry.text, 'jo', 1, Number(verse));
    const doc = parseDocument(html);
    const tips = findAll(node => node.attribs?.role === 'dialog', doc.children);
    assert.equal(tips.length, entry.segments.length);
    tips.forEach(tip => {
      assert.ok(!ids.has(tip.attribs.id));
      ids.add(tip.attribs.id);
      assert.ok(tip.attribs['data-pagefind-ignore'] !== undefined);
      removeElement(tip);
    });
    assert.equal(textContent(doc), entry.text);
  }
  const html = render(alignment.verses['1'].text, 'jo', 1, 1);
  assert.match(html, /original-jo-1-1-5/);
  assert.match(html, /λόγος/);
  assert.match(html, /G3056/);
  const tips = findAll(node => node.attribs?.role === 'dialog', parseDocument(html).children);
  assert.equal(textContent(findAll(node => node.attribs?.class === 'bible-original-details', [tips[4]])[0]), 'λόγος (logos)\nSubstantivo - Nominativo Masculino Singular\nG3056: palavra, discurso, mensagem, relato, razão');
});

test('expressões e contrações podem apontar para um ou vários tokens', () => {
  assert.match(render(alignment.verses['3'].text, 'jo', 1, 3), />vieram a ser<span[^>]+[^]*?ἐγένετο/);
  assert.match(render(alignment.verses['4'].text, 'jo', 1, 4), />Nela<span[^>]+[^]*?Ἐν[^]*?αὐτῷ/);
});

test('um texto alterado suspende vínculos incertos, e versos sem alinhamento são preservados', () => {
  assert.equal(render('Texto diferente', 'jo', 1, 1), 'Texto diferente');
  assert.ok(render.records.get('jo 1:1').pending.length);
  assert.equal(render('<em>Texto</em>', 'jo', 1, 6), '<em>Texto</em>');
  assert.equal(render('Texto', 'mt', 1, 1), 'Texto');
});

test('os cinco textos esperados correspondem aos capítulos publicados', () => {
  const liquid = fs.readFileSync('src/biblia/nt/joao/1.liquid', 'utf8');
  for (const [verse, entry] of Object.entries(alignment.verses)) {
    assert.ok(liquid.includes(`{% verse bookAbbrev bookChapter ${verse} %}${entry.text}{% endverse %}`));
  }
});

test('interação abre por foco, toque e mouse e fecha com Escape, fora e rolagem', () => {
  const vm = require('node:vm');
  const listeners = () => ({
    events: {},
    addEventListener(name, handler) { this.events[name] = handler; },
  });
  const closeButton = { ...listeners() };
  const tip = { contains: target => target === tip || target === closeButton, hidden: true, style: {}, getBoundingClientRect: () => ({ width: 300, height: 160 }) };
  const trigger = {
    ...listeners(),
    classList: { add() {}, remove() {} },
    setAttribute() {},
    focus() { document.activeElement = trigger; this.events.focus(); },
    querySelector: selector => selector === '.bible-original-close' ? closeButton : tip,
    contains: target => target === trigger || target === tip || target === closeButton,
    getBoundingClientRect: () => ({ left: 350, top: 100, bottom: 120 }),
  };
  const document = { ...listeners(), querySelectorAll: () => [trigger] };
  const window = { ...listeners(), innerWidth: 400, innerHeight: 300 };
  let pending;
  vm.runInNewContext(fs.readFileSync('src/assets/js/bible-original.js', 'utf8'), {
    document, window,
    setTimeout(handler) { pending = handler; return 1; },
    clearTimeout() { pending = undefined; },
  });
  trigger.events.focus();
  assert.equal(tip.hidden, false);
  assert.equal(tip.style.left, '92px');
  document.events.keydown({ key: 'Escape' });
  assert.equal(tip.hidden, true);
  trigger.events.click({ target: trigger });
  assert.equal(tip.hidden, false);
  trigger.events.focusout({ relatedTarget: closeButton });
  assert.equal(tip.hidden, false);
  closeButton.events.click({ stopPropagation() {} });
  assert.equal(tip.hidden, true);
  trigger.events.click({ target: trigger });
  document.events.pointerdown({ target: {} });
  assert.equal(tip.hidden, true);
  trigger.events.pointerenter({ pointerType: 'mouse' });
  pending();
  assert.equal(tip.hidden, false);
  window.events.scroll({ target: window });
  assert.equal(tip.hidden, true);
  trigger.events.pointerenter({ pointerType: 'touch' });
  assert.equal(tip.hidden, true);
});

test('o shortcode verse integra o alinhamento sem mudar outros versículos', () => {
  const shortcodes = new Map();
  require('../.eleventy.js')({
    addWatchTarget() {}, on() {}, addPassthroughCopy() {}, addFilter() {},
    addPairedShortcode(name, handler) { shortcodes.set(name, handler); },
  });
  const verse = shortcodes.get('verse');
  const html = verse(alignment.verses['1'].text, 'jo', 1, 1, true);
  assert.match(html, /id="jo_1-1"/);
  assert.match(html, /verse-text redletter/);
  assert.match(html, /class="bible-original"/);
  const pericope = shortcodes.get('pericope')(`${html}\n\n${verse(alignment.verses['2'].text, 'jo', 1, 2)}`, 'Título');
  const doc = parseDocument(pericope);
  const paragraphs = findAll(node => node.name === 'p', doc.children);
  assert.equal(paragraphs.length, 2);
  const first = findAll(node => node.attribs?.class?.startsWith('verse-text'), [paragraphs[0]])[0];
  findAll(node => node.attribs?.role === 'dialog', [first]).forEach(removeElement);
  assert.equal(textContent(first), alignment.verses['1'].text);
  assert.equal(verse(' Texto comum ', 'jo', 1, 6), '<span id="jo_1-6" class="verse"><span class="verse-number">6</span><span class="verse-text ">Texto comum</span></span>');
});

const { reconcile, mandatoryMatches } = require('../src/lib/bible-reconcile');
function visible(html) {
  const doc = parseDocument(html);
  findAll(node => node.attribs?.role === 'dialog', doc.children).forEach(removeElement);
  return textContent(doc);
}

test('pontuação, espaços e caixa são recalculados sem mudar o texto publicado', () => {
  const text = alignment.verses['1'].text.replace('No princípio', 'NO  princípio').replace('Palavra,', 'Palavra;');
  const html = render(text, 'jo', 1, 1);
  assert.equal(visible(html), text);
  assert.equal(render.records.get('jo 1:1').pending.length, 0);
  assert.equal(render.records.get('jo 1:1').rendered, 16);
});

test('mudança lexical suspende só os trechos inseguros e relata palavras novas', () => {
  const text = alignment.verses['3'].text.replace('vieram a ser', 'passaram a existir');
  const html = render(text, 'jo', 1, 3);
  assert.equal(visible(html), text);
  const record = render.records.get('jo 1:3');
  assert.ok(record.pending.some(item => item.text === 'vieram a ser'));
  assert.ok(record.pending.some(item => item.text === 'existir'));
  assert.ok(record.segments.some(item => item.text === 'Todas as coisas'));
  assert.ok(!record.segments.some(item => item.text === 'passaram a existir'));
});

test('equivalência explícita é reaplicada, mas não é inventada pelo dicionário', () => {
  const entry = { text: 'Eles vieram a ser livres.', segments: [{ start: 5, text: 'vieram a ser', tokens: [1], alternatives: ['passaram a existir'] }] };
  const result = reconcile(entry, 'Eles passaram a existir livres.');
  assert.equal(result.pending.length, 0);
  assert.equal(result.segments[0].status, 'equivalencia-aprovada');
  assert.equal(result.segments[0].text, 'passaram a existir');
});

test('repetições removidas não transferem vínculos por adivinhação', () => {
  const result = reconcile({ text: 'Deus Deus', segments: [{ start: 0, text: 'Deus', tokens: [1] }, { start: 5, text: 'Deus', tokens: [2] }] }, 'Deus');
  assert.equal(result.segments.length, 0);
  assert.equal(mandatoryMatches('a a', 'a').matches.size, 0);
});

test('inclusão dentro de expressão suspende o vínculo inteiro', () => {
  const result = reconcile({ text: 'por meio dela', segments: [{ start: 0, text: 'por meio', tokens: [1] }, { start: 9, text: 'dela', tokens: [2] }] }, 'por outro meio dela');
  assert.deepEqual(result.segments.map(item => item.text), ['dela']);
  assert.ok(result.pending.some(item => item.text === 'por meio'));
});

test('HTML e entidades são preservados integralmente e geram pendência', () => {
  for (const text of ['<em>No princípio</em>', 'No princípio&nbsp;era']) {
    assert.equal(render(text, 'jo', 1, 1), text);
    assert.equal(render.records.get('jo 1:1').rendered, 0);
    assert.equal(render.records.get('jo 1:1').status, 'pendente');
  }
});

test('relatório é determinístico, restrito à cobertura existente e tem modo estrito', () => {
  const os = require('node:os');
  const path = require('node:path');
  const { scan, report } = require('./bible-alignment');
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-alignment-test-'));
  try {
    const renderer = scan();
    const filename = path.join(directory, 'report.json');
    const result = report(renderer, filename);
    assert.equal(result.verses.length, 5);
    assert.equal(result.pendingVerses, 0);
    const first = fs.readFileSync(filename, 'utf8');
    report(renderer, filename);
    assert.equal(fs.readFileSync(filename, 'utf8'), first);
  } finally { fs.rmSync(directory, { recursive: true }); }
});


test('correspondências obrigatórias concordam com todos os alinhamentos ótimos em casos pequenos', () => {
  const sequences = [[]];
  for (let length = 1; length <= 3; length++) for (let bits = 0; bits < 2 ** length; bits++) {
    sequences.push(Array.from({ length }, (_, i) => bits & (1 << i) ? 'a' : 'b'));
  }
  function all(a, b, i = 0, j = 0) {
    if (i === a.length || j === b.length) return [[]];
    const choices = [...all(a, b, i + 1, j), ...all(a, b, i, j + 1)];
    if (a[i] === b[j]) choices.push(...all(a, b, i + 1, j + 1).map(rest => [[i, j], ...rest]));
    const length = Math.max(...choices.map(choice => choice.length));
    return choices.filter(choice => choice.length === length);
  }
  for (const a of sequences) for (const b of sequences) {
    const optimal = all(a, b);
    const expected = optimal[0].filter(([i, j]) => optimal.every(choice => choice.some(pair => pair[0] === i && pair[1] === j)));
    assert.deepEqual([...mandatoryMatches(a.join(' '), b.join(' ')).matches], expected);
  }
});

test('modo estrito da CLI passa para o alinhamento aprovado atual', () => {
  const os = require('node:os');
  const path = require('node:path');
  const { spawnSync } = require('node:child_process');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'bereia-alignment-cli-'));
  try {
    const run = spawnSync(process.execPath, ['tools/bible-alignment.js', '--check'], {
      encoding: 'utf8', env: { ...process.env, BEREIA_BIBLE_ALIGNMENT_REPORT: path.join(dir, 'report.json') },
    });
    assert.equal(run.status, 0, run.stderr);
    assert.equal(JSON.parse(fs.readFileSync(path.join(dir, 'report.json'), 'utf8')).pendingVerses, 0);
  } finally { fs.rmSync(dir, { recursive: true }); }
});


test('forma sem correspondência exata não herda morfologia ou transliteração de outra flexão', () => {
  const html = render(alignment.verses['1'].text, 'jo', 1, 1);
  const doc = parseDocument(html);
  const details = findAll(node => node.attribs?.class === 'bible-original-details', doc.children);
  assert.equal(textContent(details[1]), 'ἀρχῇ\nMorfologia não confirmada para esta forma\nG746: princípio, início; principado');
  assert.ok(render.records.get('jo 1:1').lexicalWarnings.some(item => item.greek === 'ἀρχῇ'));
});
