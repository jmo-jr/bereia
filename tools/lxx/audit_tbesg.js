#!/usr/bin/env node
// Auditoria somente: não preenche traduções nem modifica o dicionário ou livros.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { createEnhanceTokenWithDict } = require('../../src/_data/nt');
const ROOT = path.resolve(__dirname, '../..');
const TBESG_URL = 'https://github.com/STEPBible/STEPBible-Data/tree/master/Lexicons';
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const exact = value => value.normalize('NFC').toLowerCase();
const loose = value => exact(value).normalize('NFD').replace(/\p{M}/gu, '').replaceAll('ς', 'σ');

function parseTbesg(file) {
  const rows = [];
  fs.readFileSync(file, 'utf8').split(/\r?\n/).forEach((line, index) => {
    if (!/^G\d+\t/.test(line)) return;
    const fields = line.split('\t');
    if (fields.length < 8) {
      throw new Error(`Linha TBESG inválida: ${index + 1}`);
    }
    rows.push({ line: index + 1, eStrong: fields[0], dStrong: fields[1], uStrong: fields[2],
      greek: fields[3], transliteration: fields[4], morph: fields[5], gloss: fields[6],
      meaning: fields.slice(7).join('\t') });
  });
  if (!rows.length) throw new Error('Nenhum registro TBESG reconhecido');
  return rows;
}

function audit({ tbesg, originals, output }) {
  const lexicalRows = parseTbesg(tbesg);
  const indexes = [new Map(), new Map()];
  for (const row of lexicalRows) {
    // Alternativas explícitas; não tentar extrair lemas de explicações em prosa.
    for (const form of row.greek.split(/[,/]/).map(s => s.trim()).filter(s => /^[\p{Script=Greek}\p{M}\s᾿’'-]+$/u.test(s))) {
      for (const [index, normalize] of [[indexes[0], exact], [indexes[1], loose]]) {
        const key = normalize(form);
        if (!index.has(key)) index.set(key, new Set());
        index.get(key).add(row.line);
      }
    }
  }
  const dictionary = path.join(ROOT, 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json');
  let absent;
  const enhance = createEnhanceTokenWithDict(read(dictionary), { record() { absent = true; } });
  const directory = path.join(ROOT, 'src/interlinear/at');
  const files = fs.readdirSync(directory).filter(file => file.endsWith('.json')).sort();
  const groups = new Map();
  const sourceFiles = [];
  const summary = { books: files.length, tokens: 0, missingTokens: 0, missingForms: 0,
    alignedMissingTokens: 0, alignmentFailures: 0, matches: {} };
  const forms = new Set();
  for (const file of files) {
    const convertedPath = path.join(directory, file);
    const chapters = read(convertedPath);
    const names = [...new Set(chapters.map(c => c.source_file))];
    if (names.length !== 1 || !names[0] || path.basename(names[0]) !== names[0]) throw new Error(`Origem inválida: ${file}`);
    const originalPath = path.join(originals, names[0]);
    if (!fs.existsSync(originalPath)) throw new Error(`Original ausente: ${originalPath}`);
    const sourceIndex = new Map();
    for (const row of read(originalPath)) {
      const match = /^.+ (\d+):(\d+[a-z]?)$/.exec(row.ref);
      if (!match) throw new Error(`Referência original inválida: ${row.ref}`);
      const key = `${Number(match[1])}:${match[2]}`;
      if (sourceIndex.has(key)) throw new Error(`Referência original duplicada: ${row.ref}`);
      sourceIndex.set(key, row);
    }
    sourceFiles.push({ book: file, original: names[0], original_sha256: hash(originalPath), converted_sha256: hash(convertedPath) });
    for (const chapter of chapters) for (const verse of (chapter.pericopes?.length ? chapter.pericopes.flatMap(p => p.verses) : chapter.verses || [])) {
      const original = sourceIndex.get(`${chapter.chapter}:${verse.verse}`);
      const aligned = original && original.words.length === verse.tokens.length &&
        verse.tokens.every((token, i) => token.lemma === original.words[i].surface);
      verse.tokens.forEach((token, position) => {
        summary.tokens++;
        absent = false;
        enhance(token);
        if (!absent) return;
        summary.missingTokens++;
        forms.add(token.lemma);
        const word = aligned ? original.words[position] : null;
        if (word) summary.alignedMissingTokens++; else summary.alignmentFailures++;
        const key = JSON.stringify([token.lemma, word?.lemma, word?.parsing, word?.pos]);
        if (!groups.has(key)) {
          const exactRows = word?.lemma ? [...(indexes[0].get(exact(word.lemma)) || [])] : [];
          const candidates = exactRows.length ? exactRows : word?.lemma ? [...(indexes[1].get(loose(word.lemma)) || [])] : [];
          const status = !word ? 'alignment_failed' : !word.lemma ? 'lemma_missing' : !candidates.length ? 'not_found' :
            `${exactRows.length ? 'accented' : 'unaccented'}_${candidates.length === 1 ? 'single' : 'multiple'}`;
          groups.set(key, { form: token.lemma, lemma: word?.lemma ?? null,
            parsing: word?.parsing ?? null, pos: word?.pos ?? null, status,
            candidate_lines: candidates, occurrences: 0, references: [], source_confidence: {} });
        }
        const group = groups.get(key);
        group.occurrences++;
        const confidence = word?.confidence || 'not_recorded';
        group.source_confidence[confidence] = (group.source_confidence[confidence] || 0) + 1;
        const reference = `${file.slice(0, -5)} ${chapter.chapter}:${verse.verse}`;
        if (!group.references.includes(reference)) group.references.push(reference);
      });
    }
  }
  summary.missingForms = forms.size;
  const records = [...groups.values()].sort((a, b) => b.occurrences - a.occurrences || a.form.localeCompare(b.form, 'el'));
  const used = new Set(records.flatMap(row => row.candidate_lines));
  for (const row of records) {
    summary.matches[row.status] ||= { groups: 0, occurrences: 0 };
    summary.matches[row.status].groups++;
    summary.matches[row.status].occurrences += row.occurrences;
  }
  const result = { source: { file: path.basename(tbesg), sha256: hash(tbesg), url: TBESG_URL,
    attribution: 'Tyndale House and STEPBible.org — CC BY 4.0',
    dictionary_sha256: hash(dictionary), rows: lexicalRows.length,
    missing_fields: Object.fromEntries(['greek', 'transliteration', 'morph', 'gloss'].map(field =>
      [field, lexicalRows.filter(row => !row[field].trim()).length])) },
    method: 'Somente candidatos: referência, posição e surface devem coincidir integralmente. Busca por lema primeiro em NFC/minúsculas; retirada de diacríticos somente como candidato separado. Morph da TBESG é categoria lexical; parsing pertence ao original e não foi validado. Nenhuma tradução aplicada.',
    sourceFiles, summary, lexicon: lexicalRows.filter(row => used.has(row.line)), records };
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n', 'utf8');
  return result;
}

if (require.main === module) {
  const [tbesg, originals, output = 'tools/relatorios/lxx-tbesg-cobertura.json'] = process.argv.slice(2);
  if (!tbesg || !originals) {
    console.error('Uso: node tools/lxx/audit_tbesg.js ARQUIVO_TBESG PASTA_ORIGINAIS [RELATORIO_JSON]');
    process.exitCode = 1;
  } else {
    try { console.log(JSON.stringify(audit({ tbesg, originals, output }).summary, null, 2)); }
    catch (error) { console.error(error.message); process.exitCode = 1; }
  }
}
module.exports = { parseTbesg, audit };
