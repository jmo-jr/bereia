const fs = require('node:fs');
const path = require('node:path');

// URLs editoriais podem diferir dos nomes dos JSONs de origem.
const SOURCE_IDS = { 'jó': 'jo', '1re': '1rs', '2re': '2rs', ed: '1esd', ne: '2esd', et: 'est' };

module.exports = () => {
  const directory = path.join(__dirname, '../interlinear/at');
  if (!fs.existsSync(directory)) return [];
  // Leitura nova também permite atualizar os metadados no modo watch.
  // A subpasta evita que o Eleventy una o JSON à lista global atBooks deste JS.
  const metadata = JSON.parse(fs.readFileSync(path.join(__dirname, 'lxx/atBooks.json'), 'utf8'));
  const files = fs.readdirSync(directory).filter(file => file.endsWith('.json'));
  const available = new Set(files.map(file => path.basename(file, '.json')));
  const ntSlugs = new Set(require('./ntBooks.json').map(book => book.permalink.split('/').filter(Boolean).pop()));
  const seenIds = new Set();
  const seenSlugs = new Set();
  const books = metadata.flatMap(book => {
    const match = /^\/interlinear\/([^/]+)\/$/u.exec(book.permalink || '');
    if (!match) throw new Error(`Permalink inválido em atBooks.json: ${book.permalink}`);
    const slug = match[1];
    const id = book.id || (available.has(slug) ? slug : SOURCE_IDS[slug] || slug);
    if (seenIds.has(id) || seenSlugs.has(slug)) throw new Error(`Livro ou endereço duplicado em atBooks.json: ${slug}`);
    seenIds.add(id);
    seenSlugs.add(slug);
    if (ntSlugs.has(slug)) throw new Error(`Endereço da LXX em conflito com o NT: ${slug}`);
    if (!available.has(id)) return [];
    const chapters = JSON.parse(fs.readFileSync(path.join(directory, `${id}.json`), 'utf8'));
    return [{ ...book, id, slug, chapters: chapters.length,
      chapterNumbers: chapters.map(chapter => chapter.chapter) }];
  });
  const missing = [...available].filter(id => !seenIds.has(id));
  if (missing.length) throw new Error(`Livros sem metadados em atBooks.json: ${missing.join(', ')}`);
  return books;
};
