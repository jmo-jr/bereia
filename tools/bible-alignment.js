const fs = require('node:fs');
const path = require('node:path');
const { createRenderer } = require('../src/lib/bible-alignment');
const root = path.resolve(__dirname, '..');

function scan(render = createRenderer()) {
  const found = new Set();
  function walk(directory) {
    for (const item of fs.readdirSync(directory, { withFileTypes: true })) {
      const file = path.join(directory, item.name);
      if (item.isDirectory()) { walk(file); continue; }
      if (!file.endsWith('.liquid')) continue;
      const source = fs.readFileSync(file, 'utf8');
      const book = /^bookAbbrev:\s*["']?([a-z0-9]+)["']?\s*$/mi.exec(source)?.[1].toLowerCase();
      const chapter = Number(/^bookChapter:\s*(\d+)\s*$/m.exec(source)?.[1]);
      if (!book || !chapter) continue;
      for (const match of source.matchAll(/\{%\s*verse\s+bookAbbrev\s+bookChapter\s+(\d+)(?:\s+[^%]*)?\s*%\}([\s\S]*?)\{%\s*endverse\s*%\}/g)) {
        const verse = Number(match[1]);
        found.add(`${book} ${chapter}:${verse}`);
        render(match[2].trim(), book, chapter, verse);
      }
    }
  }
  walk(path.join(root, 'src/biblia'));
  function alignments(directory) {
    for (const item of fs.readdirSync(directory, { withFileTypes: true })) {
      const file = path.join(directory, item.name);
      if (item.isDirectory()) { alignments(file); continue; }
      if (!file.endsWith('.json')) continue;
      const book = path.basename(path.dirname(file)), chapter = path.basename(file, '.json');
      const data = JSON.parse(fs.readFileSync(file, 'utf8'));
      for (const verse of Object.keys(data.verses)) {
        const reference = `${book} ${chapter}:${verse}`;
        if (!found.has(reference)) render.records.set(reference, { reference, status: 'pendente', rendered: 0,
          pending: [{ reason: 'Versículo aprovado não encontrado nos templates; conferir remoção ou formato do shortcode.' }] });
      }
    }
  }
  alignments(path.join(root, 'src/alinhamentos'));
  return render;
}

function report(render, filename = process.env.BEREIA_BIBLE_ALIGNMENT_REPORT || path.join(root, 'reports/bible-alignment.json')) {
  const verses = [...render.records.values()].sort((a, b) => a.reference.localeCompare(b.reference, 'pt-BR', { numeric: true }));
  const result = { version: 1, scope: 'Somente versículos com alinhamento aprovado; capítulos sem alinhamento não recebem vínculos automáticos.',
    pendingVerses: verses.filter(verse => verse.pending.length).length,
    lexicalWarnings: verses.reduce((count, verse) => count + (verse.lexicalWarnings?.length || 0), 0), verses };
  fs.mkdirSync(path.dirname(filename), { recursive: true });
  const content = JSON.stringify(result, null, 2) + '\n';
  if (!fs.existsSync(filename) || fs.readFileSync(filename, 'utf8') !== content) fs.writeFileSync(filename, content);
  return result;
}
if (require.main === module) {
  const result = report(scan());
  console.log(`Alinhamento bíblico: ${result.verses.length} versículos; ${result.pendingVerses} com pendências; ${result.lexicalWarnings} avisos lexicais. Relatório: reports/bible-alignment.json`);
  if (process.argv.includes('--check') && result.pendingVerses) process.exitCode = 1;
}
module.exports = { scan, report };
