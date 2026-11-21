const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { encode, parse } = require('./csv');
const { setValue } = require('./json-patch');
const { readChapters, safeOutput } = require('../bible-proposals/generate');
const { words } = require('../bible-proposals/lexical');
const { reconcile } = require('../../src/lib/bible-reconcile');
const ROOT = path.resolve(__dirname, '../..');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const json = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const key = item => JSON.stringify([item.start, item.text, item.tokens]);
const COLUMNS = ['decisao', 'referencia', 'tipo', 'trecho_pt', 'inicio_pt', 'tokens_gregos', 'formas_gregas', 'observacao', 'situacao_original', 'id', 'conflitos', 'justificativa_original', 'evidencias', 'texto_versiculo', 'grego_versiculo'];
const EDITABLE = new Set(['decisao', 'tipo', 'trecho_pt', 'inicio_pt', 'tokens_gregos', 'observacao']);
const snapshotFile = csv => csv.replace(/\.csv$/iu, '') + '.review.json';
function relativeFile(root, name) {
  if (path.isAbsolute(name) || name.split(/[\\/]/u).includes('..')) throw Error('Caminho inválido no arquivo de revisão.');
  return path.join(root, name);
}
function stamp(root, filename) {
  const name = path.relative(root, filename);
  relativeFile(root, name);
  if (fs.existsSync(filename) && fs.lstatSync(filename).isSymbolicLink()) throw Error(`Fonte por link simbólico não permitida: ${name}.`);
  return { file: name, sha256: fs.existsSync(filename) ? hash(fs.readFileSync(filename)) : null };
}
function liveChapter(root, book, chapter) {
  const inventory = readChapters(root, { book, chapter });
  const result = inventory.chapters[0];
  if (!result) throw Error(inventory.missing[0]?.reason || 'Capítulo atual não encontrado.');
  return result;
}
function rowFor(record, verse) {
  return { decisao: '', referencia: record.reference, tipo: record.type, trecho_pt: record.text ?? '', inicio_pt: record.start ?? '',
    tokens_gregos: record.tokens.join(','), formas_gregas: record.tokens.map(position => `${position}:${verse.greek[position - 1]}`).join(' | '),
    observacao: '', situacao_original: record.status, id: record.id, conflitos: (record.conflicts || []).join(','),
    justificativa_original: record.reason || '', evidencias: JSON.stringify(record.evidence || []), texto_versiculo: verse.text,
    grego_versiculo: verse.greek.map((form, index) => `${index + 1}:${form}`).join(' | ') };
}

function exportReview({ root = ROOT, book, chapter, sourceDir = path.join(root, 'reports/bible-occurrence-relations'), outDir = path.join(root, 'reports/bible-review') } = {}) {
  const summary = json(path.join(sourceDir, 'summary.json'));
  if (summary.version !== 2 || summary.type !== 'RELACOES_POR_OCORRENCIA') throw Error('São necessárias relações por ocorrência da versão 2.');
  const selected = summary.chapters.filter(item => (!book || item.file.startsWith(book + '/')) && (!chapter || Number(path.basename(item.file, '.json')) === chapter));
  if (!selected.length) throw Error('Nenhum capítulo desse escopo consta no resumo. Gere as relações com bible:propose.');
  const output = safeOutput(root, outDir), planned = [];
  for (const selectedChapter of selected) {
    const relationFile = relativeFile(sourceDir, selectedChapter.file), document = json(relationFile);
    const current = liveChapter(root, document.book, document.chapter);
    const dictionary = path.join(root, 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json');
    if (hash(fs.readFileSync(dictionary)) !== summary.reverseIndex?.dictionaryHash) throw Error('Dicionário mudou desde a geração das relações. Atualize o índice e gere uma nova rodada.');
    const currentVerses = new Map(current.verses.map(verse => [String(verse.number), verse]));
    const rows = [], records = {}, ids = new Set();
    for (const [number, verse] of Object.entries(document.verses)) {
      const live = currentVerses.get(number);
      if (!live || live.text !== verse.text || JSON.stringify(live.greek) !== JSON.stringify(verse.greek)) throw Error(`${document.book} ${document.chapter}:${number}: texto ou grego mudou; gere novas relações.`);
      for (const record of [...verse.relations, ...verse.notes]) {
        if (ids.has(record.id) || record.reference !== `${document.book} ${document.chapter}:${number}`) throw Error('Identificador de relação duplicado ou referência inválida.');
        ids.add(record.id);
        const row = rowFor(record, verse);
        rows.push(row); records[record.id] = { row: Object.fromEntries(Object.entries(row).map(([name, value]) => [name, String(value)])), record, verse: number };
      }
    }
    const approvedFile = path.join(root, 'src/alinhamentos', document.book, `${document.chapter}.json`);
    const snapshot = { version: 1, book: document.book, chapter: document.chapter, sourceBook: document.sourceBook, sourceFormat: current.format,
      snapshots: [stamp(root, path.join(root, current.file)), stamp(root, path.join(root, 'src/interlinear/nt', `${document.sourceBook}.json`)), stamp(root, dictionary), stamp(root, relationFile), stamp(root, approvedFile)],
      verses: Object.fromEntries(Object.entries(document.verses).map(([number, verse]) => [number, { text: verse.text, greek: verse.greek }])), records };
    const csv = path.join(output, document.book, `${document.chapter}.csv`);
    const csvContent = encode([COLUMNS, ...rows.map(row => COLUMNS.map(column => row[column]))]);
    planned.push([csv, csvContent], [snapshotFile(csv), JSON.stringify(snapshot, null, 2) + '\n']);
  }
  for (const [filename, content] of planned) {
    safeOutput(root, path.dirname(filename));
    if (fs.existsSync(filename) && (fs.lstatSync(filename).isSymbolicLink() || fs.readFileSync(filename, 'utf8') !== content)) throw Error(`Revisão existente preservada: ${filename}. Use --out com outra pasta.`);
  }
  for (const [filename, content] of planned) { fs.mkdirSync(path.dirname(filename), { recursive: true }); if (!fs.existsSync(filename)) fs.writeFileSync(filename, content); }
  return { chapters: selected.length, files: planned.filter(([filename]) => filename.endsWith('.csv')).map(([filename]) => filename) };
}

function readRows(input) {
  let data;
  for (const delimiter of [';', ',']) {
    try {
      const candidate = parse(input, delimiter), header = candidate[0];
      if (header?.length === COLUMNS.length && new Set(header).size === COLUMNS.length && COLUMNS.every(name => header.includes(name))) { data = candidate; break; }
    } catch { /* Try the other common Excel CSV separator. */ }
  }
  if (!data) throw Error('Cabeçalho CSV inválido. Preserve os nomes das colunas e salve como CSV UTF-8.');
  const [header, ...rows] = data;
  return rows.map((row, index) => {
    if (row.length !== header.length) throw Error(`Linha ${index + 2}: quantidade de campos inválida.`);
    return Object.fromEntries(header.map((column, i) => [column, row[i]]));
  });
}
function positions(value) {
  if (!value.trim()) return [];
  if (!/^\s*\d+(?:[\s,]+\d+)*\s*$/u.test(value)) throw Error('tokens_gregos deve conter posições inteiras separadas por vírgula.');
  const result = value.trim().split(/[\s,]+/u).map(Number);
  if (result.some(value => !Number.isSafeInteger(value) || value < 1) || new Set(result).size !== result.length) throw Error('Posições gregas inválidas ou duplicadas.');
  return result;
}
function validateEntry(entry, reference) {
  const pt = [...entry.segments, ...(entry.unlinkedPortuguese || [])].sort((a, b) => a.start - b.start);
  let end = 0;
  for (const item of pt) {
    if (!Number.isSafeInteger(item.start) || item.start < end || !item.text || entry.text.slice(item.start, item.start + item.text.length) !== item.text) throw Error(`${reference}: trechos inválidos ou sobrepostos.`);
    end = item.start + item.text.length;
    const from = item.start, to = end;
    if (words(entry.text).some(word => (from > word.start && from < word.end) || (to > word.start && to < word.end))) throw Error(`${reference}: trecho corta uma palavra.`);
  }
  const used = new Set();
  for (const position of [...entry.segments.flatMap(segment => segment.tokens), ...(entry.untranslatedTokens || []).map(item => item.position)]) {
    if (!Number.isSafeInteger(position) || position < 1 || position > entry.greek.length || used.has(position)) throw Error(`${reference}: token grego inválido ou disputado por duas decisões aprovadas.`);
    used.add(position);
  }
  entry.pendingReview = [
    ...words(entry.text).filter(word => !pt.some(item => word.start >= item.start && word.end <= item.start + item.text.length)).map(word => ({ type: 'PORTUGUES_SEM_VINCULO', start: word.start, text: entry.text.slice(word.start, word.end), reason: 'Aguardando decisão de alinhamento.' })),
    ...entry.greek.flatMap((form, index) => used.has(index + 1) ? [] : [{ type: 'GREGO_SEM_VINCULO', tokens: [index + 1], text: form, reason: 'Aguardando decisão de alinhamento.' }]),
  ];
  return entry;
}
function rebase(existing, live, reference) {
  if (!existing) return { text: live.text, greek: live.greek, segments: [] };
  if (JSON.stringify(existing.greek) !== JSON.stringify(live.greek)) throw Error(`${reference}: sequência grega aprovada mudou; é necessária revisão específica antes de importar.`);
  const entry = JSON.parse(JSON.stringify(existing));
  if (entry.text !== live.text) {
    const result = reconcile(entry, live.text);
    entry.segments = result.segments.map(({ index, status, ...segment }) => segment);
    const notes = reconcile({ text: entry.text, segments: (entry.unlinkedPortuguese || []).map(item => ({ ...item, tokens: [] })) }, live.text);
    if (entry.unlinkedPortuguese) entry.unlinkedPortuguese = notes.segments.map(({ index, status, tokens, ...item }) => item);
    entry.text = live.text;
  }
  return entry;
}

function importReview({ root = ROOT, file, apply = false } = {}) {
  if (!file || !/\.csv$/iu.test(file)) throw Error('Informe --file com o CSV de revisão.');
  const csv = fs.readFileSync(file, 'utf8'), snapshot = json(snapshotFile(file));
  if (snapshot.version !== 1 || !/^[a-z0-9]+$/iu.test(snapshot.book) || snapshot.sourceBook !== snapshot.book.toUpperCase() || !Number.isSafeInteger(snapshot.chapter) || snapshot.chapter < 1) throw Error('Manifesto de revisão inválido.');
  for (const source of snapshot.snapshots) {
    const filename = relativeFile(root, source.file);
    const current = fs.existsSync(filename) ? hash(fs.readFileSync(filename)) : null;
    if (current !== source.sha256) throw Error(`Fonte mudou desde a exportação: ${source.file}. Preserve este CSV e exporte uma nova revisão.`);
  }
  const chapter = liveChapter(root, snapshot.book, snapshot.chapter);
  const liveVerses = new Map(chapter.verses.map(verse => [String(verse.number), verse]));
  for (const [number, original] of Object.entries(snapshot.verses)) {
    const live = liveVerses.get(number);
    if (!live || original.text !== live.text || JSON.stringify(original.greek) !== JSON.stringify(live.greek)) throw Error(`${number}: texto ou grego atual não confere com o CSV.`);
  }
  const target = path.join(root, 'src/alinhamentos', snapshot.book, `${snapshot.chapter}.json`);
  let folder = path.dirname(target);
  while (folder.startsWith(path.join(root, 'src'))) {
    if (fs.existsSync(folder) && fs.lstatSync(folder).isSymbolicLink()) throw Error('Pasta aprovada por link simbólico não permitida.');
    folder = path.dirname(folder);
  }
  if (fs.existsSync(target) && fs.lstatSync(target).isSymbolicLink()) throw Error('Arquivo aprovado por link simbólico não permitido.');
  const before = fs.existsSync(target) ? fs.readFileSync(target, 'utf8') : null;
  const approved = before ? JSON.parse(before) : { sourceBook: snapshot.sourceBook, verses: {} };
  if (approved.sourceBook !== snapshot.sourceBook) throw Error('Livro grego não confere com o arquivo aprovado.');
  const entries = new Map(), decisions = [], seen = new Set();
  for (const row of readRows(csv)) {
    if (seen.has(row.id)) throw Error(`ID duplicado no CSV: ${row.id}.`);
    seen.add(row.id);
    const original = Object.hasOwn(snapshot.records, row.id) ? snapshot.records[row.id] : undefined;
    if (!original) throw Error(`ID desconhecido no CSV: ${row.id}. Não crie ou altere ids.`);
    for (const column of COLUMNS.filter(name => !EDITABLE.has(name))) if (row[column] !== original.row[column]) throw Error(`${row.id}: coluna ${column} é de referência e foi alterada.`);
    const action = row.decisao.trim().toUpperCase();
    if (!['', 'APROVAR', 'REJEITAR', 'PENDENTE'].includes(action)) throw Error(`${row.id}: decisão inválida. Use APROVAR, REJEITAR ou PENDENTE.`);
    if (!action) {
      if ([...EDITABLE].filter(name => !['decisao', 'observacao'].includes(name)).some(column => row[column] !== original.row[column])) throw Error(`${row.id}: vínculo editado sem decisão. Indique APROVAR para importar a correção.`);
      continue;
    }
    decisions.push({ id: row.id, reference: row.referencia, action, observation: row.observacao, original: original.record, edited: { type: row.tipo, text: row.trecho_pt, start: row.inicio_pt, tokens: row.tokens_gregos } });
    if (action === 'PENDENTE') continue;
    const number = original.verse, live = snapshot.verses[number];
    if (action === 'APROVAR' && (chapter.format !== 'liquid' || /<[^>]*>|&(?:#\d+|#x[\da-f]+|\w+);/iu.test(live.text))) throw Error(`${row.referencia}: converta o capítulo para o shortcode verse sem marcação interna e reexporte antes de importar.`);
    let entry = entries.get(number);
    if (!entry) entry = rebase(approved.verses[number], live, row.referencia);
    const old = original.record;
    const existingSegment = old.type === 'VINCULO' ? entry.segments.find(segment => key(segment) === key(old)) : undefined;
    const existingPT = old.type.startsWith('PORTUGUES_') ? (entry.unlinkedPortuguese || []).find(item => item.start === old.start && item.text === old.text) : undefined;
    const existingGreek = old.type.startsWith('GREGO_') ? (entry.untranslatedTokens || []).find(item => old.tokens.length === 1 && item.position === old.tokens[0] && old.start === null) : undefined;
    if (action === 'REJEITAR' && !existingSegment && !existingPT && !existingGreek) continue;
    if (existingSegment) entry.segments = entry.segments.filter(item => item !== existingSegment);
    if (existingPT) entry.unlinkedPortuguese = entry.unlinkedPortuguese.filter(item => item !== existingPT);
    if (existingGreek) entry.untranslatedTokens = entry.untranslatedTokens.filter(item => item !== existingGreek);
    if (action === 'APROVAR') {
      const type = row.tipo.trim().toUpperCase(), tokens = positions(row.tokens_gregos);
      const start = row.inicio_pt === '' ? null : Number(row.inicio_pt);
      const text = row.trecho_pt;
      const reason = row.observacao.trim() || (original.record.status === 'APROVADA' ? original.record.reason : '');
      if (type === 'VINCULO') {
        if (!tokens.length || !Number.isSafeInteger(start) || start < 0 || !text) throw Error(`${row.id}: vínculo requer trecho, posição portuguesa e tokens gregos.`);
        const segment = existingSegment && existingSegment.text === text && JSON.stringify(existingSegment.tokens) === JSON.stringify(tokens) ? { ...existingSegment, start } : { start, text, tokens };
        if (row.observacao.trim()) segment.reviewNote = row.observacao.trim();
        entry.segments.push(segment);
      } else if (type === 'PORTUGUES_SEM_VINCULO_DIRETO') {
        if (!reason || tokens.length || !Number.isSafeInteger(start) || start < 0 || !text) throw Error(`${row.id}: ausência de vínculo português requer trecho, posição, nenhum token e justificativa.`);
        (entry.unlinkedPortuguese ||= []).push({ start, text, reason });
      } else if (type === 'GREGO_SEM_VINCULO_DIRETO') {
        if (!reason || tokens.length !== 1 || start !== null || text) throw Error(`${row.id}: ausência de vínculo grego requer um token, texto/posição portugueses vazios e justificativa.`);
        (entry.untranslatedTokens ||= []).push({ position: tokens[0], reason });
      } else throw Error(`${row.id}: para aprovar uma nota sem candidato, escolha VINCULO ou um tipo SEM_VINCULO_DIRETO com justificativa.`);
    }
    entries.set(number, entry);
  }
  for (const [number, entry] of entries) {
    entry.segments.sort((a, b) => a.start - b.start);
    validateEntry(entry, `${snapshot.book} ${snapshot.chapter}:${number}`);
    if (!entry.pendingReview.length && !Object.hasOwn(approved.verses[number] || {}, 'pendingReview')) delete entry.pendingReview;
  }
  let content = before;
  if (before) {
    for (const [number, entry] of entries) {
      if (!Object.hasOwn(approved.verses, number)) content = setValue(content, ['verses', number], entry);
      else for (const [field, value] of Object.entries(entry)) content = setValue(content, ['verses', number, field], value);
    }
  } else if (entries.size) {
    for (const [number, entry] of entries) approved.verses[number] = entry;
    content = JSON.stringify(approved, null, 2) + '\n';
  }
  const changed = content !== before;
  const result = { applied: false, file: path.relative(root, target), changed, decisions: decisions.length,
    approved: decisions.filter(item => item.action === 'APROVAR').length, rejected: decisions.filter(item => item.action === 'REJEITAR').length,
    deferred: decisions.filter(item => item.action === 'PENDENTE').length,
    verses: [...entries].map(([verse, entry]) => ({ verse: Number(verse), segments: entry.segments.length, pending: entry.pendingReview?.length || 0 })) };
  if (apply && decisions.length) {
    const receiptFile = file.replace(/\.csv$/iu, '') + `.import-${hash(csv).slice(0, 12)}.json`;
    safeOutput(root, path.dirname(receiptFile));
    if (fs.existsSync(receiptFile) && (!fs.lstatSync(receiptFile).isFile() || fs.lstatSync(receiptFile).isSymbolicLink())) throw Error('Recibo por link simbólico não permitido.');
    const receipt = { version: 1, csvHash: hash(csv), target: result.file, beforeHash: before === null ? null : hash(before), afterHash: content === null ? null : hash(content), decisions, summary: { ...result, applied: true } };
    const receiptContent = JSON.stringify(receipt, null, 2) + '\n';
    if (fs.existsSync(receiptFile) && fs.readFileSync(receiptFile, 'utf8') !== receiptContent) throw Error('Recibo existente preservado; não sobrescreva o histórico da importação.');
    for (const source of snapshot.snapshots) {
      const filename = relativeFile(root, source.file);
      if ((fs.existsSync(filename) ? hash(fs.readFileSync(filename)) : null) !== source.sha256) throw Error('Uma fonte mudou durante a validação; nenhuma aprovação foi escrita.');
    }
    // All rows and conflicts were validated before any approved file is written.
    if (changed) { fs.mkdirSync(path.dirname(target), { recursive: true }); fs.writeFileSync(target, content); }
    if (!fs.existsSync(receiptFile)) fs.writeFileSync(receiptFile, receiptContent);
    result.applied = true; result.receipt = receiptFile;
  }
  return result;
}
module.exports = { COLUMNS, exportReview, importReview, readRows, rowFor, validateEntry, snapshotFile };
