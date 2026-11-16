const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const FILE = path.resolve(__dirname, '../_data/lxx/supplement-beta.json');

function loadBetaSupplement() {
  if (!fs.existsSync(FILE)) return null;
  return JSON.parse(fs.readFileSync(FILE, 'utf8'));
}

function forBook(supplement, bookId, sourceText) {
  if (!supplement) return () => null;
  const hash = crypto.createHash('sha256').update(sourceText).digest('hex');
  if (supplement.books[bookId] !== hash) {
    console.warn(`[LXX beta] ${bookId}: JSON alterado; regenere as auditorias e o suplemento. Enriquecimento beta suspenso para este livro.`);
    return () => null;
  }
  return (chapter, verse, position, form) => {
    const index = supplement.occurrences[`${bookId}:${chapter}:${verse}:${position}`];
    if (index === undefined) return null;
    const entry = supplement.entries[index];
    if (!entry || entry.forma !== form) return null;
    // Nenhum identificador externo é exposto como Strong ou como verbete.
    return Object.fromEntries(['pt', 'traducao', 'transliteracao', 'morfologia', 'abrev_morf']
      .filter(field => typeof entry[field] === 'string').map(field => [field, entry[field]]));
  };
}

module.exports = { loadBetaSupplement, forBook };
