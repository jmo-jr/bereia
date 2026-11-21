const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { parseDocument } = require('htmlparser2');
const { findAll } = require('domutils');
const { createLexicon, propose, evaluate, words } = require('./engine');
const projectRoot = path.resolve(__dirname, '../..');
const hash = content => crypto.createHash('sha256').update(content).digest('hex');
const readJSON = filename => JSON.parse(fs.readFileSync(filename, 'utf8'));

function readApproved(root) {
  const examples = [], files = [];
  const directory = path.join(root, 'src/alinhamentos');
  if (!fs.existsSync(directory)) return { examples, files };
  for (const book of fs.readdirSync(directory).sort()) {
    const folder = path.join(directory, book);
    if (!fs.statSync(folder).isDirectory()) continue;
    for (const name of fs.readdirSync(folder).sort()) {
      if (!/^\d+\.json$/u.test(name)) continue;
      const file = path.join(folder, name), data = readJSON(file);
      files.push(file);
      for (const [verse, entry] of Object.entries(data.verses)) {
        const reference = `${book} ${Number(path.basename(name, '.json'))}:${verse}`;
        if (!Array.isArray(entry.greek) || !Array.isArray(entry.segments) || typeof entry.text !== 'string') throw Error(`${reference}: alinhamento aprovado inválido.`);
        for (const segment of entry.segments) {
          if (!Number.isSafeInteger(segment.start) || segment.start < 0 || !segment.text || entry.text.slice(segment.start, segment.start + segment.text.length) !== segment.text || !Array.isArray(segment.tokens) || !segment.tokens.length || segment.tokens.some(position => !Number.isSafeInteger(position) || position < 1 || position > entry.greek.length)) throw Error(`${reference}: segmento aprovado inválido.`);
        }
        examples.push({ reference, entry, sourceBook: data.sourceBook });
      }
    }
  }
  return { examples, files };
}

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

function safeOutput(root, directory) {
  const target = path.resolve(directory);
  let ancestor = target;
  while (!fs.existsSync(ancestor)) ancestor = path.dirname(ancestor);
  const resolved = path.join(fs.realpathSync(ancestor), path.relative(ancestor, target));
  const canonicalRoot = fs.realpathSync(root);
  for (const protectedPath of [canonicalRoot, path.join(canonicalRoot, 'src'), path.join(canonicalRoot, '.git')]) {
    const relative = path.relative(protectedPath, resolved);
    if (protectedPath === canonicalRoot ? relative === '' : relative === '' || (!relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative))) throw Error('A saída deve ficar fora de src e .git, em uma pasta de relatórios separada.');
  }
  return resolved;
}

function generate(options = {}) {
  const root = options.root || projectRoot;
  const output = safeOutput(root, options.out || path.join(root, 'reports/bible-alignment-proposals'));
  const dictionaryFile = path.join(root, 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json');
  const dictionary = readJSON(dictionaryFile);
  const approved = readApproved(root), inventory = readChapters(root, options);
  const approvedByRef = new Map(approved.examples.map(example => [example.reference, example]));
  const lexicon = createLexicon(dictionary, approved.examples);
  const inputs = [...new Set([path.join(root, 'src/_data/ntBooks.json'), dictionaryFile, ...approved.files, ...inventory.files, ...[__filename, path.join(__dirname, 'engine.js')].filter(file => file.startsWith(root + path.sep))])].sort().map(file => ({ file: path.relative(root, file), sha256: hash(fs.readFileSync(file)) }));
  const inputDigest = hash(JSON.stringify(inputs));
  const summary = { version: 1, status: 'PROPOSTAS_NAO_APROVADAS', inputDigest, options: { book: options.book || null, chapter: options.chapter || null, includeApproved: Boolean(options.includeApproved), evaluate: Boolean(options.evaluate) },
    sources: inputs, chapters: [], missing: inventory.missing, totals: { chapters: 0, unavailableChapters: inventory.missing.length, verses: 0, skippedApproved: 0, candidates: 0, uniqueCandidates: 0, ambiguousCandidates: 0, incompleteVerses: 0, missingTranslationVerses: inventory.chapters.reduce((count, chapter) => count + chapter.missingTranslations.length, 0), unmatchedPortuguese: 0, unmatchedGreek: 0 },
    evaluation: options.evaluate ? { approvedSegments: 0, candidates: 0, matchedApprovedSegments: 0, uniqueCandidates: 0, uniqueMatches: 0, excludedStaleVerses: 0 } : undefined };
  const outputs = [];
  for (const chapter of inventory.chapters) {
    const document = { version: 1, status: 'PROPOSTA_NAO_APROVADA', inputDigest, sourceBook: chapter.sourceBook, sourceFile: chapter.file, sourceFormat: chapter.format,
      book: chapter.book, chapter: chapter.chapter, missingTranslations: chapter.missingTranslations, verses: {} };
    for (const verse of chapter.verses) {
      const reference = `${chapter.book} ${chapter.chapter}:${verse.number}`, gold = approvedByRef.get(reference);
      if (gold && !options.includeApproved && !options.evaluate) { summary.totals.skippedApproved++; continue; }
      if (options.evaluate && !gold) continue;
      if (!verse.greek) {
        document.verses[verse.number] = { status: 'PROPOSTA_NAO_APROVADA', text: verse.text, greek: [], candidates: [], issues: ['Versículo grego não encontrado.'], unmatchedPortuguese: words(verse.text).map(word => ({ start: word.start, text: verse.text.slice(word.start, word.end), reason: 'Versículo grego não encontrado.' })), unmatchedGreek: [] };
      } else {
        const proposal = propose({ text: verse.text, greek: verse.greek, reference, lexicon, excludeReference: options.evaluate ? reference : undefined });
        document.verses[verse.number] = proposal;
        if (options.evaluate) {
          if (gold.entry.text !== verse.text || JSON.stringify(gold.entry.greek) !== JSON.stringify(verse.greek)) {
            proposal.issues.push('Referência aprovada difere do texto ou grego atual; excluída da avaliação.'); summary.evaluation.excludedStaleVerses++;
          } else {
            proposal.evaluation = evaluate(proposal, gold.entry);
            for (const [key, value] of Object.entries(proposal.evaluation)) summary.evaluation[key] += value;
          }
        }
      }
      const proposal = document.verses[verse.number];
      proposal.issues.push(...(verse.sourceIssues || []));
      summary.totals.verses++;
      summary.totals.candidates += proposal.candidates.length;
      summary.totals.uniqueCandidates += proposal.candidates.filter(candidate => candidate.review === 'CANDIDATO_UNICO').length;
      summary.totals.ambiguousCandidates += proposal.candidates.filter(candidate => candidate.review === 'AMBIGUO').length;
      summary.totals.incompleteVerses += proposal.issues.length ? 1 : 0;
      summary.totals.unmatchedPortuguese += proposal.unmatchedPortuguese.length;
      summary.totals.unmatchedGreek += proposal.unmatchedGreek.length;
    }
    if (!Object.keys(document.verses).length) continue;
    const filename = `${chapter.book}/${chapter.chapter}.json`;
    summary.chapters.push({ file: filename, sourceFile: chapter.file, verses: Object.keys(document.verses).length });
    outputs.push([filename, document]);
  }
  summary.totals.chapters = outputs.length;
  // Compute everything before writing. Proposals have no "segments" field and
  // cannot be mistaken for approved renderer input.
  const planned = [...outputs, ['summary.json', summary]];
  for (const [filename] of planned) {
    const destination = path.join(output, filename);
    // Reject existing symlinked book folders as well as symlinked output roots.
    safeOutput(root, path.dirname(destination));
    if (fs.existsSync(destination) && fs.lstatSync(destination).isSymbolicLink()) throw Error(`Saída é link simbólico: ${destination}`);
  }
  for (const [filename, document] of planned) {
    const destination = path.join(output, filename);
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    const content = JSON.stringify(document, null, 2) + '\n';
    if (!fs.existsSync(destination) || fs.readFileSync(destination, 'utf8') !== content) fs.writeFileSync(destination, content);
  }
  return { summary, output };
}

function argumentsFrom(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index++) {
    const arg = argv[index];
    if (arg === '--include-approved') options.includeApproved = true;
    else if (arg === '--evaluate') options.evaluate = true;
    else if (['--book', '--chapter', '--out'].includes(arg)) {
      const value = argv[++index];
      if (!value || value.startsWith('--')) throw Error(`Falta o valor de ${arg}.`);
      options[arg.slice(2)] = arg === '--chapter' ? Number(value) : arg === '--book' ? value.toLowerCase() : value;
    } else if (arg === '--help') options.help = true;
    else throw Error(`Opção desconhecida: ${arg}`);
  }
  if (options.chapter !== undefined && (!options.book || !Number.isSafeInteger(options.chapter) || options.chapter < 1)) throw Error('--chapter requer --book e um inteiro positivo.');
  return options;
}
if (require.main === module) {
  try {
    const options = argumentsFrom(process.argv.slice(2));
    if (options.help) console.log('Uso: npm run bible:propose -- [--book jo] [--chapter 2] [--include-approved] [--evaluate] [--out reports/pasta]');
    else {
      const { summary, output } = generate(options);
      console.log(JSON.stringify({ output, ...summary.totals, evaluation: summary.evaluation }, null, 2));
    }
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = { readApproved, readChapters, safeOutput, generate, argumentsFrom };
