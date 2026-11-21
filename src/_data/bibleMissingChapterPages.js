const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const root = path.resolve(__dirname, '../..');
const escape = value => String(value).replace(/[&<>"']/gu, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
module.exports = () => {
  const { readChapters } = require('../../tools/bible-proposals/generate');
  const inventory = readChapters(root);
  const metadata = JSON.parse(fs.readFileSync(path.join(root, 'src/_data/ntBooks.json'), 'utf8'));
  const missing = inventory.chapters.filter(chapter => chapter.format === 'txt').map(chapter => {
    const meta = metadata.find(book => book.permalink.split('/').filter(Boolean).at(-1) === chapter.book);
    return { book: chapter.book, chapter: chapter.chapter, filename: path.join(root, chapter.file), bookName: meta.name,
      permalink: meta.bkpermalink + chapter.chapter + '/' };
  });
  if (!missing.length) return [];
  const parsed = JSON.parse(execFileSync(process.env.BEREIA_PYTHON || 'python3', ['-B', path.join(root, 'tools/bible-global/missing-pages.py')], { input: JSON.stringify(missing), encoding: 'utf8', maxBuffer: 20 * 1024 * 1024 }));
  const diagnostics = parsed.flatMap(chapter => chapter.warnings);
  if (diagnostics.length) console.warn(`Páginas TXT: ${diagnostics.length} avisos de marcação; consulte reports/bible-generated-pages.json.`);
  fs.mkdirSync(path.join(root, 'reports'), { recursive: true });
  fs.writeFileSync(path.join(root, 'reports/bible-generated-pages.json'), JSON.stringify({ generated: parsed.length, diagnostics }, null, 2) + '\n');
  return parsed.map(chapter => ({ ...chapter, html: chapter.pericopes.map(pericope =>
    `<h4 class="pericope title">${escape(pericope.title)}<small class="pericope concordance">${escape(pericope.concordance)}</small></h4><div class="pericope text">` +
    pericope.paragraphs.map(paragraph => '<p>' + paragraph.map(verse => `<span id="${chapter.book}_${chapter.chapter}-${verse.number}" class="verse"><span class="verse-number">${verse.number}</span><span class="verse-text">${verse.html}</span></span>`).join('\n') + '</p>').join('\n') + '</div>').join('\n') + '\n</div>' }));
};
