const { phrases, normalizePortuguese } = require('./bible-lexical-text');
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
    source: { file: 'src/_data/nt/dict_flex_nt-lxx_greek-pt.json', sha256: sourceHash },
    normalization: 'Português: NFC, minúsculas e espaços uniformizados; acentos, hífens e expressões preservados. Sem lematização ou escolha contextual.',
    statistics: { dictionaryEntries: Object.keys(dictionary).length, indexedEntries, terms: terms.size, references, pending: pending.length },
    terms: Object.fromEntries([...terms.entries()].sort(([a], [b]) => a.localeCompare(b, 'pt-BR'))),
    pending,
  };
}

module.exports = { buildIndex };
