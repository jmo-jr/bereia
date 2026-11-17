module.exports = {
  pagination: {
    before: (ntChapters, data) => [...ntChapters, ...data.atChapterPages],
  },
  eleventyComputed: {
    lxx: data => Boolean(data.entry?.lxx),
  },
};
