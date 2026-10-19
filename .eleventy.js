const { execSync } = require('child_process')
//const { EleventyHtmlBasePlugin } = require("@11ty/eleventy");

module.exports = function(eleventyConfig) {
  const escapeHtml = value => String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

  const positiveInteger = (value, label) => {
    const number = Number(value);
    if (!Number.isSafeInteger(number) || number < 1) {
      throw new Error(`Shortcode de capítulo: ${label} inválido: ${value}`);
    }
    return number;
  };

	/*
	 * {% verse bookAbbrev bookChapter 1 %}
	*/
  eleventyConfig.addPairedShortcode('verse', function(content, bookAbbrev, chapter, verseNumber, red) {
    const abbreviation = String(bookAbbrev);
    if (!/^[a-z0-9]+$/i.test(abbreviation)) {
      throw new Error(`Shortcode de versículo: abreviação inválida: ${bookAbbrev}`);
    }

    const chapterNumber = positiveInteger(chapter, 'capítulo');
    const number = positiveInteger(verseNumber, 'versículo');
		const redletter = red ? 'redletter' : '';

    return `<span id="${abbreviation}_${chapterNumber}-${number}" class="verse"><span class="verse-number">${number}</span><span class="verse-text ${redletter}">${content.trim()}</span></span>`;
  });

	/*
	 * {% tooltip "comentário/#referencia" true/null %}
	*/
	eleventyConfig.addPairedShortcode('tooltip', function(content, comment, type) {
    const simpleTooltip = `<span class="tooltip" title="${comment}">${content.trim()}</span>`;
		const dataTooltip = `<span class="tooltip" data-tooltip-content="${comment}">${content.trim()}</span>`;

		const toolTip = type ? simpleTooltip : dataTooltip;

    return toolTip;
  });

	/*
	 * {% pericope "titulo", "ref concordância" %}
	*/
  eleventyConfig.addPairedShortcode('pericope', function(content, title, concordance = '') {
    const paragraphs = content
      .trim()
      .split(/\n\s*\n/)
      .filter(paragraph => paragraph.trim())
      .map(paragraph => `<p>${paragraph.trim()}</p>`) /* Criar o parágrafo */
      .join('\n');

    return `<h4 class="pericope title">${escapeHtml(title)}<small class="pericope concordance">${escapeHtml(concordance)}</small></h4><div class="pericope text">${paragraphs}</div>`;
  });

  eleventyConfig.addPassthroughCopy('src/css');
  eleventyConfig.addPassthroughCopy('src/img');
	eleventyConfig.addPassthroughCopy("src/assets");
	eleventyConfig.addPassthroughCopy("src/manifest.json");
	eleventyConfig.addPassthroughCopy("src/assets/icons");
	eleventyConfig.addPassthroughCopy("src/service-worker.js");

	//PageFind search
	// eleventyConfig.on('eleventy.after', () => {
  //   execSync(`npx pagefind --site _site/biblia --output-subdir pagefind --glob \"**/*.html\"`, { encoding: 'utf-8' })
  // })

  return {
    // ajuste para o prefixo do site hospedado (terminar com "/")
    pathPrefix: "/",
    dir: {
      input: "src",
      includes: "_includes",
      output: "_site"
    }
  };
};