const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { phrases, canonicalGreek, normalizePortuguese } = require('./bible-proposals/lexical');
const ROOT = path.resolve(__dirname, '..');
const SOURCE = 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json';
const OUTPUT = 'reports/bible-reverse-index.json';
const digest = text => crypto.createHash('sha256').update(text).digest('hex');

function buildIndex(dictionary, sourceHash) {
  if (!dictionary || typeof dictionary !== 'object' || Array.isArray(dictionary)) throw Error('O dicionário deve ser um objeto de entradas gregas.');
  const terms = new Map(), pending = [];
  let indexedEntries = 0, references = 0;
  for (const [dictionaryKey, entry] of Object.entries(dictionary)) {
    let indexed = false;
    for (const field of ['pt', 'traducao']) {
      const value = entry?.[field];
      if (typeof value !== 'string' || !value.trim()) {
        pending.push({ dictionaryKey, field, value: value ?? null, reason: 'Campo ausente, vazio ou não textual.' });
        continue;
      }
      if (/[()[\]{}]/u.test(value)) {
        pending.push({ dictionaryKey, field, value, reason: 'Notação gramatical, complemento ou colchetes: não expandido automaticamente.' });
        continue;
      }
      const accepted = new Set(phrases(value));
      for (const part of [...new Set(value.split(/[,;/]/u).map(text => text.trim()).filter(Boolean))]) {
        if (!accepted.has(part)) {
          pending.push({ dictionaryKey, field, value: part, reason: 'Trecho não reconhecido como expressão portuguesa simples; requer revisão.' });
          continue;
        }
        const term = normalizePortuguese(part);
        if (!terms.has(term)) terms.set(term, []);
        terms.get(term).push({ dictionaryKey, field, text: part });
        references++;
        indexed = true;
      }
    }
    if (indexed) indexedEntries++;
  }
  return {
    version: 1,
    purpose: 'Índice lexical reverso. Resultados são candidatos, não vínculos por ocorrência aprovados.',
    source: { file: SOURCE, sha256: sourceHash },
    normalization: 'Português: NFC, minúsculas e espaços uniformizados; acentos, hífens e expressões preservados. Sem lematização ou escolha contextual.',
    statistics: { dictionaryEntries: Object.keys(dictionary).length, indexedEntries, terms: terms.size, references, pending: pending.length },
    terms: Object.fromEntries([...terms.entries()].sort(([a], [b]) => a.localeCompare(b, 'pt-BR'))),
    pending,
  };
}

function readSource(root = ROOT) {
  const raw = fs.readFileSync(path.join(root, SOURCE), 'utf8');
  return { raw, hash: digest(raw), dictionary: JSON.parse(raw) };
}

function generateIndex({ root = ROOT, check = false } = {}) {
  const source = readSource(root);
  const index = buildIndex(source.dictionary, source.hash);
  const content = JSON.stringify(index, null, 2) + '\n';
  const directory = path.join(root, 'reports'), filename = path.join(root, OUTPUT);
  // This command has a fixed report destination, never an approved/source path.
  if ((fs.existsSync(directory) && fs.lstatSync(directory).isSymbolicLink()) ||
      (fs.existsSync(filename) && fs.lstatSync(filename).isSymbolicLink())) throw Error('O destino do índice não pode ser link simbólico.');
  const current = fs.existsSync(filename) && fs.readFileSync(filename, 'utf8') === content;
  if (!check && !current) {
    fs.mkdirSync(directory, { recursive: true });
    fs.writeFileSync(filename, content);
  }
  return { index, filename, current: Boolean(current), changed: !current };
}

function lookup(index, source, query, greekTokens) {
  if (index.version !== 1 || index.source?.file !== SOURCE || index.source.sha256 !== source.hash) {
    throw Error('Índice ausente ou desatualizado para este dicionário. Execute npm run bible:index.');
  }
  if (typeof query !== 'string') throw Error('Informe uma palavra ou expressão portuguesa.');
  const term = normalizePortuguese(query);
  if (!term) throw Error('Informe uma palavra ou expressão portuguesa.');
  const matches = new Map();
  for (const reference of index.terms[term] || []) {
    const dictionaryKey = reference.dictionaryKey;
    if (!Object.hasOwn(source.dictionary, dictionaryKey)) throw Error(`Referência inválida no índice: ${dictionaryKey}. Regenere o índice.`);
    if (!['pt', 'traducao'].includes(reference.field) || normalizePortuguese(reference.text) !== term || !phrases(source.dictionary[dictionaryKey][reference.field]).includes(reference.text)) {
      throw Error(`Referência lexical inconsistente no índice: ${dictionaryKey}. Regenere o índice.`);
    }
    const occurrences = greekTokens === undefined ? undefined : greekTokens.flatMap((form, position) =>
      canonicalGreek(form) === canonicalGreek(dictionaryKey) ? [{ position: position + 1, form }] : []);
    if (occurrences && !occurrences.length) continue;
    if (!matches.has(dictionaryKey)) matches.set(dictionaryKey, { dictionaryKey, references: [], ...(occurrences ? { greekOccurrences: occurrences } : {}), data: source.dictionary[dictionaryKey] });
    matches.get(dictionaryKey).references.push(reference);
  }
  return { term, status: 'CANDIDATOS_LEXICAIS_NAO_APROVADOS', filteredByVerse: greekTokens !== undefined, matches: [...matches.values()] };
}

function readIndex({ root = ROOT, source = readSource(root) } = {}) {
  const filename = path.join(root, OUTPUT);
  if (!fs.existsSync(filename)) throw Error('Índice ainda não gerado. Execute npm run bible:index.');
  const index = JSON.parse(fs.readFileSync(filename, 'utf8'));
  if (index.version !== 1 || index.source?.file !== SOURCE || index.source.sha256 !== source.hash) throw Error('Índice ausente ou desatualizado para este dicionário. Execute npm run bible:index.');
  return index;
}

function lookupFile({ root = ROOT, query, book, chapter, verse } = {}) {
  const filename = path.join(root, OUTPUT);
  if (!fs.existsSync(filename)) throw Error('Índice ainda não gerado. Execute npm run bible:index.');
  let greekTokens;
  if ([book, chapter, verse].some(value => value !== undefined)) {
    if (!/^[a-z0-9]+$/iu.test(book || '') || !Number.isSafeInteger(chapter) || chapter < 1 || !Number.isSafeInteger(verse) || verse < 1) {
      throw Error('Para filtrar a ocorrência, informe --book, --chapter e --verse com valores válidos.');
    }
    const file = path.join(root, 'src/interlinear/nt', `${book.toUpperCase()}.json`);
    if (!fs.existsSync(file)) throw Error(`Livro grego não encontrado: ${book}.`);
    const chapters = JSON.parse(fs.readFileSync(file, 'utf8'));
    const original = chapters.find(item => Number(item.chapter) === chapter)?.pericopes.flatMap(item => item.verses).find(item => Number(item.verse) === verse);
    if (!original) throw Error(`Versículo grego não encontrado: ${book} ${chapter}:${verse}.`);
    greekTokens = original.tokens.map(token => token.lemma);
  }
  return lookup(JSON.parse(fs.readFileSync(filename, 'utf8')), readSource(root), query, greekTokens);
}

function run(argv) {
  const mode = argv[0];
  if (mode === 'build' || mode === 'check') {
    if (argv.length !== 1) throw Error('Uso: npm run bible:index ou npm run bible:index:check.');
    const result = generateIndex({ check: mode === 'check' });
    console.log(JSON.stringify({ file: OUTPUT, ...result.index.statistics, current: mode === 'check' ? result.current : true }, null, 2));
    if (mode === 'check' && !result.current) process.exitCode = 1;
    return;
  }
  if (mode !== 'lookup') throw Error('Uso: bible-reverse-index.js build | check | lookup <expressão> [--book jo --chapter 1 --verse 1].');
  const options = {}, query = [];
  for (let index = 1; index < argv.length; index++) {
    const arg = argv[index];
    if (['--book', '--chapter', '--verse'].includes(arg)) {
      const value = argv[++index];
      if (!value || value.startsWith('--')) throw Error(`Falta o valor de ${arg}.`);
      options[arg.slice(2)] = arg === '--book' ? value : Number(value);
    } else if (arg.startsWith('--')) throw Error(`Opção desconhecida: ${arg}.`);
    else query.push(arg);
  }
  if (!query.length) throw Error('Informe uma palavra ou expressão portuguesa.');
  console.log(JSON.stringify(lookupFile({ ...options, query: query.join(' ') }), null, 2));
}
if (require.main === module) {
  try { run(process.argv.slice(2)); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = { normalizePortuguese, buildIndex, readSource, readIndex, generateIndex, lookup, lookupFile, run };
