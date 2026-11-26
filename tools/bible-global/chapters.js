const fs = require('node:fs');
const path = require('node:path');
const { parseDocument } = require('htmlparser2');
const { findAll } = require('domutils');
const readJSON = filename => JSON.parse(fs.readFileSync(filename, 'utf8'));
function readChapters(root, options = {}) {
  const chapters = [], missing = [], files = [];
  const books = readJSON(path.join(root, 'src/_data/ntBooks.json'));
  const locations = new Map();
  function locateTemplates(directory) {
    for (const item of fs.readdirSync(directory, { withFileTypes: true })) {
      const filename = path.join(directory, item.name);
      if (item.isDirectory()) { locateTemplates(filename); continue; }
      if (!/^\d+\.liquid$/u.test(item.name)) continue;
      const source = fs.readFileSync(filename, 'utf8');
      const book = /^bookAbbrev:\s*["']?([a-z0-9]+)["']?\s*$/mi.exec(source)?.[1].toLowerCase();
      const chapter = Number(/^bookChapter:\s*(\d+)\s*$/m.exec(source)?.[1]);
      if (!book || !chapter) continue;
      const key = `${book}:${chapter}`;
      if (!locations.has(key)) locations.set(key, []);
      locations.get(key).push(filename);
    }
  }
  locateTemplates(path.join(root, 'src/biblia/nt'));
  if (options.book && !books.some(book => book.permalink.split('/').filter(Boolean).at(-1) === options.book)) throw Error(`Livro desconhecido: ${options.book}. Use a abreviação, por exemplo jo, mt ou 1co.`);
  for (const meta of books) {
    const book = meta.permalink.split('/').filter(Boolean).at(-1);
    if (options.book && book !== options.book) continue;
    if (options.chapter && options.chapter > meta.chapters) throw Error(`Capítulo inexistente: ${book} ${options.chapter}.`);
    const sourceBook = book.toUpperCase();
    const greekFile = path.join(root, 'src/interlinear/nt', `${sourceBook}.json`);
    if (!fs.existsSync(greekFile)) { missing.push({ book, reason: 'Livro grego não encontrado.' }); continue; }
    const greekChapters = readJSON(greekFile);
    files.push(greekFile);
    const slug = meta.bkpermalink.split('/').filter(Boolean).at(-1);
    for (let number = 1; number <= meta.chapters; number++) {
      if (options.chapter && number !== options.chapter) continue;
      const base = path.join(root, 'src/biblia/nt', slug, String(number));
      const alternatives = locations.get(`${book}:${number}`) || [];
      if (alternatives.length > 1) { missing.push({ book, chapter: number, reason: 'Mais de um template declara este livro/capítulo; revisar a origem.' }); continue; }
      const filename = alternatives[0] || (fs.existsSync(base + '.liquid') ? base + '.liquid' : fs.existsSync(base + '.txt') ? base + '.txt' : null);
      if (!filename) { missing.push({ book, chapter: number, reason: 'Tradução do capítulo não encontrada.' }); continue; }
      files.push(filename);
      try {
        const source = fs.readFileSync(filename, 'utf8'), verses = [], seen = new Set();
        let format = filename.endsWith('.txt') ? 'txt' : 'liquid';
        if (filename.endsWith('.liquid')) {
          const declaredBook = /^bookAbbrev:\s*["']?([a-z0-9]+)["']?\s*$/mi.exec(source)?.[1].toLowerCase();
          const declaredChapter = Number(/^bookChapter:\s*(\d+)\s*$/m.exec(source)?.[1]);
          if (declaredBook !== book || declaredChapter !== number) throw Error(`${filename}: metadados do capítulo não conferem com o livro.`);
          const matches = [...source.matchAll(/\{%\s*verse\s+bookAbbrev\s+bookChapter\s+(\d+)(?:\s+[^%]*)?\s*%\}([\s\S]*?)\{%\s*endverse\s*%\}/g)];
          const openings = [...source.matchAll(/\{%\s*verse\b/g)].length;
          if (matches.length !== openings) throw Error(`${filename}: shortcode verse não reconhecido; nenhum trecho pode ser omitido silenciosamente.`);
          verses.push(...matches.map(match => ({ number: Number(match[1]), text: match[2].trim() })));
          const doc = parseDocument(source, { withStartIndices: true, withEndIndices: true, decodeEntities: false });
          const legacy = findAll(node => node.name === 'span' && node.attribs?.class?.split(/\s+/u).includes('verse'), doc.children);
          for (const node of legacy) {
            const id = new RegExp(`^${book}_${number}-(\\d+)$`).exec(node.attribs.id || '');
            if (!id) throw Error(`${filename}: identificação de versículo HTML não reconhecida.`);
            const content = findAll(child => child.name === 'span' && child.attribs?.class?.split(/\s+/u).includes('verse-text'), [node]);
            if (content.length !== 1) throw Error(`${filename}: corpo do versículo HTML não reconhecido.`);
            const element = content[0];
            let endOpening = element.startIndex, quote;
            for (; endOpening < source.length; endOpening++) {
              const char = source[endOpening];
              if (quote) { if (char === quote) quote = undefined; }
              else if (char === '"' || char === "'") quote = char;
              else if (char === '>') break;
            }
            const closing = source.lastIndexOf('</span', element.endIndex);
            if (closing <= endOpening) throw Error(`${filename}: fechamento de versículo HTML inválido.`);
            verses.push({ number: Number(id[1]), text: source.slice(endOpening + 1, closing).trim() });
          }
          if (!verses.length) throw Error(`${filename}: nenhum versículo reconhecido.`);
          if (legacy.length) format = matches.length ? 'liquid-misto-html' : 'html-em-liquid';
        } else {
          let current;
          for (const line of source.split(/\r?\n/u)) {
            if (line.trim() === '--') { current = undefined; continue; }
            const match = /^(\d+)\s+(.+)$/u.exec(line);
            if (match) { current = { number: Number(match[1]), text: match[2].trim(), sourceIssues: [] }; verses.push(current); }
            else if (line.trim() && current) {
              current.text += '\n' + line;
              if (!current.sourceIssues.length) current.sourceIssues.push('TXT com continuação não numerada: conferir limites do versículo; o texto foi preservado.');
            }
          }
          if (!verses.length) throw Error(`${filename}: nenhum versículo TXT reconhecido.`);
        }
        const greekChapter = greekChapters.find(chapter => Number(chapter.chapter) === number);
        const originals = new Map((greekChapter?.pericopes || []).flatMap(pericope => pericope.verses).map(verse => [Number(verse.verse), verse.tokens.map(token => token.lemma)]));
        for (const verse of verses) {
          if (!Number.isSafeInteger(verse.number) || verse.number < 1) throw Error(`${filename}: número de versículo inválido.`);
          if (seen.has(verse.number)) throw Error(`${filename}: versículo duplicado ${verse.number}.`);
          seen.add(verse.number);
          verse.greek = originals.get(verse.number);
        }
        const missingTranslations = [...originals.keys()].filter(verse => !seen.has(verse));
        chapters.push({ book, chapter: number, sourceBook, file: path.relative(root, filename), format, verses, missingTranslations });
      } catch (error) {
        missing.push({ book, chapter: number, sourceFile: path.relative(root, filename), reason: error.message.replaceAll(root + path.sep, '') });
      }
    }
  }
  return { chapters, missing, files };
}

module.exports = { readChapters };
