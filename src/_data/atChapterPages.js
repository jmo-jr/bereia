const fs = require('node:fs');
const path = require('node:path');
const { createEnhanceTokenWithDict } = require('./nt');
const loadBooks = require('./atBooks');
const { loadBetaSupplement, forBook } = require('../lib/lxx-beta');

module.exports = () => {
  const dict = JSON.parse(fs.readFileSync(path.join(__dirname, 'nt/dict_flex_nt-lxx_greek-pt.json'), 'utf8'));
  const formIndex = JSON.parse(fs.readFileSync(path.join(__dirname, 'nt/dict_form_index_nt-lxx_greek-pt.json'), 'utf8'));
  const enhance = createEnhanceTokenWithDict(dict, { record() {} }, ['ocorrencias_lxx'], formIndex);
  const supplement = loadBetaSupplement();
  return loadBooks().flatMap(book => {
    const sourceText = fs.readFileSync(path.join(__dirname, '../interlinear/at', `${book.id}.json`), 'utf8');
    const source = JSON.parse(sourceText);
    const beta = forBook(supplement, book.id, sourceText);
    const seen = new Set();
    return source.map((raw, index) => {
      const number = Number(raw.chapter);
      if (!Number.isSafeInteger(number) || number < 0 || seen.has(number)) {
        throw new Error(`Capítulo inválido ou duplicado na LXX: ${book.id} ${raw.chapter}`);
      }
      seen.add(number);
      const normalizeVerses = verses => (verses || []).map(verse => ({
        ...verse,
        // Não converter para Number: a LXX pode conter versículos como 1a.
        number: verse.verse,
        tokens: (verse.tokens || []).map((token, position) => {
          const enriched = enhance(token);
          const fallback = enriched.strongs || enriched.consulta_dicionario === 'ambiguidade_caixa'
            ? null : beta(number, verse.verse, position, token.lemma);
          return { ...enriched, ...(fallback || {}), ocorrencias: enriched.ocorrencias_lxx ?? '', lemma: token.lemma };
        }),
      }));
      const pericopes = (raw.pericopes || []).map(pericope => ({
        ...pericope, verses: normalizeVerses(pericope.verses),
      }));
      return {
        bookId: book.id, bookSlug: book.slug, bookName: book.name,
        bookNameSlug: '', bookHeading: book.heading, lxx: true,
        previousUrl: index > 0 ? `${book.permalink}${source[index - 1].chapter}/` : `${book.permalink}#/`,
        nextUrl: index + 1 < source.length ? `${book.permalink}${source[index + 1].chapter}/` : `${book.permalink}#/`,
        chapter: { ...raw, number, pericopes,
          verses: pericopes.length ? pericopes.flatMap(p => p.verses) : normalizeVerses(raw.verses) },
      };
    });
  });
};
