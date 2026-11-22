const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { greekCaseKey } = require('./greek-form-lookup');
const sha = text => crypto.createHash('sha256').update(text).digest('hex');

function regularAccentPair(origin, target) {
  const a = [...String(origin).toLowerCase().normalize('NFD')];
  const b = [...String(target).toLowerCase().normalize('NFD')];
  const acute = a.join('').replaceAll('\u0300', '\u0301');
  if (['τίς', 'τί'].some(word => word.normalize('NFD') === acute)) return false;
  if (a.length !== b.length || acute !== b.join('').replaceAll('\u0300', '\u0301')) return false;
  const differences = a.map((c, i) => c !== b[i] ? i : -1).filter(i => i >= 0);
  if (differences.length !== 1 || !['\u0300', '\u0301'].includes(a[differences[0]]) || !['\u0300', '\u0301'].includes(b[differences[0]])) return false;
  if (a.some(c => !/\p{M}/u.test(c) && !(/\p{L}/u.test(c) && /\p{Script=Greek}/u.test(c)))) return false;
  const vowels = a.map((c, i) => 'αεηιουω'.includes(c) ? i : -1).filter(i => i >= 0);
  return vowels.length > 0 && differences[0] > vowels.at(-1);
}

function targetSignature(entry) {
  return sha(JSON.stringify(['strongs', 'grego', 'abrev_morf'].map(field => entry[field] ?? null)));
}

function validateAliasEvidence(manifest, root = path.resolve(__dirname, '../..')) {
  const validBooks = new Set();
  for (const [book, files] of Object.entries(manifest?.evidencia_por_livro || {})) {
    const paths = Object.keys(files);
    if (paths.length !== 2 || !paths.some(p => p.startsWith('src/interlinear/nt/')) || !paths.some(p => p.startsWith('tools/tmnt/with-parsing/'))) continue;
    if (paths.every(relative => {
      const absolute = path.resolve(root, relative);
      if (!absolute.startsWith(path.resolve(root) + path.sep)) return false;
      try { return sha(fs.readFileSync(absolute)) === files[relative]; } catch { return false; }
    })) validBooks.add(book);
  }
  return validBooks;
}

function referenceFor(context) {
  if (context.corpus !== 'nt' || !/^[A-Z0-9]+$/.test(context.bookId || '')) return null;
  const numbers = [context.chapterNumber, context.verseNumber, context.tokenPosition].map(Number);
  if (!numbers.every(n => Number.isSafeInteger(n) && n > 0)) return null;
  return `${context.bookId} ${numbers[0]}:${numbers[1]}#${numbers[2]}`;
}

function buildAccentAliasIndex(dict, formIndex, policy = null) {
  const controlled = new Set(), rules = new Map();
  const manifest = policy?.manifest;
  const validBooks = policy?.validBooks || new Set();
  if (manifest) {
    if (manifest.schema_version !== 1 || manifest.regra !== 'agudo_grave_final_contextual_v1') throw new Error('Manifesto de aliases de acento não reconhecido.');
    for (const form of manifest.origens_controladas) controlled.add(greekCaseKey(form));
    for (const alias of manifest.aliases) {
      const target = alias.destino, entry = dict[target.grego], refs = formIndex[target.grego] || [];
      const valid = regularAccentPair(alias.origem, target.grego) && entry && entry.strongs === target.strongs &&
        targetSignature(entry) === target.assinatura && refs.length === 1 &&
        refs[0].strongs === target.strongs && refs[0].flexao === target.flexao;
      for (const reference of alias.referencias) {
        const key = greekCaseKey(alias.origem) + '|' + reference;
        if (rules.has(key)) throw new Error('Mais de um alias para a mesma ocorrência.');
        rules.set(key, { alias, entry, valid });
      }
    }
  }
  return {
    resolve(form, context = {}) {
      const key = greekCaseKey(form);
      if (!controlled.has(key)) return { estado: 'fora_escopo' };
      const reference = referenceFor(context);
      if (!reference || !validBooks.has(context.bookId)) return { estado: 'pendente', motivo: 'referencia_ou_fonte_nao_validada' };
      const selected = rules.get(key + '|' + reference);
      if (!selected) return { estado: 'pendente', motivo: 'ocorrencia_sem_equivalencia_validada' };
      if (!selected.valid) return { estado: 'pendente', motivo: 'destino_desatualizado' };
      return { estado: 'resolvido', alias: selected.alias, entrada: selected.entry, referencia: reference };
    }
  };
}

module.exports = { regularAccentPair, targetSignature, validateAliasEvidence, buildAccentAliasIndex, referenceFor };
