const loadAllBooks = require('./nt');
const ntBooks = require('./ntBooks.json');

const BOOK_META = ntBooks.reduce((acc, book) => {
  const permalink = book.permalink || '';
  const slug = permalink.replace(/\/+$/, '').split('/').filter(Boolean).pop() || '';
  const id = slug.toUpperCase();

  if (id) {
    acc[id] = {
      ...book,
      slug,
      id,
    };
  }

  return acc;
}, {});

module.exports = () => {
  const books = loadAllBooks();

  return Object.entries(books).flatMap(([bookId, chapters = []]) => {
    const meta = BOOK_META[bookId] || {};
    const slug = meta.slug || bookId.toLowerCase();
    const name = meta.name || bookId;
    const heading = meta.heading || name;
    const permalink = meta.permalink || `/interlinear/${slug}/`;

    return chapters.map(chapter => ({
      bookId,
      bookSlug: slug,
      bookName: name,
      bookHeading: heading,
      chapter,
      permalink,
    }));
  });
};
