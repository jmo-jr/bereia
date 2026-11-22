const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { Liquid } = require('liquidjs');
const { loadBetaSupplement, forBook } = require('../src/lib/lxx-beta');

test('suplemento beta é por ocorrência, preserva a forma e não expõe Strong', async () => {
  const data = loadBetaSupplement();
  const [key, index] = Object.entries(data.occurrences).find(([, i]) => data.entries[i].pt === 'sebo');
  const [book, chapter, verse, position] = key.split(':');
  const sourceText = fs.readFileSync(path.resolve(__dirname, '../src/interlinear/at', `${book}.json`), 'utf8');
  const get = forBook(data, book, sourceText);
  const fields = get(chapter, verse, position, data.entries[index].forma);
  assert.equal(fields.pt, 'sebo');
  assert.equal(fields.strongs, undefined);
  assert.equal(fields.verbete, undefined);
  assert.equal(get(chapter, verse, position, 'outra forma'), null);
  const originalWarn = console.warn;
  try {
    console.warn = () => {};
    assert.equal(forBook(data, book, sourceText + '\n')(chapter, verse, position, data.entries[index].forma), null);
  } finally { console.warn = originalWarn; }
  const engine = new Liquid({ extname: '.liquid', root: path.resolve(__dirname, '../src/_includes') });
  const html = await engine.renderFile('interlinearChapter.liquid', {
    entry: { lxx: true, bookName: 'Teste', chapter: { number: 1, pericopes: [{ id: 'p1', title: '', verses: [
      { number: 1, tokens: [{ lemma: data.entries[index].forma, ...fields }] },
    ] }] } },
  });
  assert.match(html, /sebo/);
  assert.match(html, /stear/);
  assert.match(html, /class="strongs tooltip" href="#" target="_blank" data-strong=""[^>]*>&nbsp;<\/a>/);
  assert.doesNotMatch(html, /data-strong="G|strongs\/greek\//);
});

test('totais do suplemento conferem com a aplicação registrada', () => {
  const data = loadBetaSupplement();
  const report = require('../tools/relatorios/lxx-beta-aplicacao.json');
  const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  assert.equal(data.entries.length, report.entries.length);
  const counts = { translated_occurrences: 0, untranslated_occurrences: 0 };
  for (const index of Object.values(data.occurrences)) {
    const entry = data.entries[index];
    assert.ok(entry.transliteracao);
    assert.equal(entry.strongs, undefined);
    counts[entry.pt ? 'translated_occurrences' : 'untranslated_occurrences']++;
  }
  assert.equal(counts.translated_occurrences, report.counts.translated_occurrences);
  assert.equal(counts.untranslated_occurrences, report.counts.untranslated_occurrences);
  for (const source of report.source_hashes) {
    assert.equal(hash(path.resolve(__dirname, '../src/interlinear/at', source.book)), source.converted_sha256);
  }
});
