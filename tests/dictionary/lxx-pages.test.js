const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const loadPages = require('../../src/_data/atChapterPages');
const { Liquid } = require('liquidjs');

test('barra lista AT e NT no interlinear e somente NT na Bíblia', async () => {
  const engine = new Liquid({ extname: '.liquid', root: path.resolve(__dirname, '../../src/_includes') });
  engine.registerFilter('url', value => value);
  const layout = fs.readFileSync(path.resolve(__dirname, '../../src/_includes/page.liquid'), 'utf8');
  const toolbar = layout.slice(layout.indexOf('{% assign interlinearBooks'), layout.indexOf('<div class="content-wrapper">'));
  const data = {
    ntBooks: [{ name: 'Mateus', permalink: '/interlinear/mt/', bkpermalink: '/biblia/mateus/', chapters: 28 }],
    atBooks: [{ name: 'Gênesis', permalink: '/interlinear/gn/', chapterNumbers: [1, 2], chapters: 2 }],
    bookChapter: 1,
  };
  for (const lxx of [{ lexico_lxx_gr_pt_heb: {} }, true]) {
    const bible = await engine.parseAndRender(toolbar, { ...data, page: { url: '/biblia/mateus/1/' }, bee: true, bookName: 'Mateus', lxx });
    assert.match(bible, /value="\/biblia\/mateus\/1"/);
    assert.doesNotMatch(bible, /Gênesis|\/interlinear\/gn\//);
  }
  const at = await engine.parseAndRender(toolbar, { ...data, page: { url: '/interlinear/gn/1/' }, bookName: 'Gênesis', entry: { lxx: true }, lxx: { global: true } });
  assert.match(at, /value="\/interlinear\/gn\/1"/);
  assert.match(at, /LXX Interlinear Analítico/);
  const nt = await engine.parseAndRender(toolbar, { ...data, page: { url: '/interlinear/mt/1/' }, bookName: 'Mateus', lxx: false });
  assert.match(nt, /value="\/interlinear\/mt\/1"/);
  assert.match(nt, /Gênesis/);
  assert.doesNotMatch(nt, /LXX Interlinear Analítico/);
});

test('apresentação da LXX conserva sufixos, omite título e links Strong ausentes', async () => {
  const engine = new Liquid({ extname: '.liquid', root: path.resolve(__dirname, '../../src/_includes') });
  const html = await engine.renderFile('interlinearChapter.liquid', {
    entry: { lxx: true, bookName: 'Exemplo', chapter: { number: 0, pericopes: [{
      id: 'P001', title: '', verses: [{ number: '1a', tokens: [{ lemma: 'Ἐν' }] }],
    }] } },
  });
  assert.match(html, /id="v1a"/);
  assert.match(html, /Ἐν/);
  assert.doesNotMatch(html, /pericope-title|strongs\/greek\/\.htm|Capítulo anterior|Próximo capítulo/);
});

test('LXX preserva todas as formas, referências e capítulos dos JSONs', () => {
  const pages = loadPages();
  const directory = path.resolve(__dirname, '../../src/interlinear/at');
  let count = 0;
  for (const file of fs.readdirSync(directory).filter(name => name.endsWith('.json'))) {
    const id = path.basename(file, '.json');
    const source = JSON.parse(fs.readFileSync(path.join(directory, file), 'utf8'));
    const actual = pages.filter(page => page.bookId === id);
    assert.equal(actual.length, source.length);
    source.forEach((chapter, index) => {
      const verses = chapter.pericopes?.length ? chapter.pericopes.flatMap(p => p.verses) : chapter.verses;
      assert.deepEqual(actual[index].chapter.verses.map(v => [v.number, v.tokens.map(t => t.lemma)]),
        verses.map(v => [v.verse, v.tokens.map(t => t.lemma)]));
      assert.equal(actual[index].chapter.source_file, chapter.source_file);
    });
    count += source.length;
  }
  assert.equal(pages.length, count);
  assert.ok(pages.length > 0);
  assert.equal(pages.find(page => page.bookId === 'jo').bookSlug, 'jó');
  assert.equal(pages.find(page => page.bookId === 'gn').previousUrl, null);
  assert.equal(pages.filter(page => page.bookId === 'gn').at(-1).nextUrl, null);
});
