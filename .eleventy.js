const { execSync } = require('child_process')
const generateDictionary = require('./tools/dictionary/generate');
const { createRenderer } = require('./src/lib/bible-alignment');
const { scan, report } = require('./tools/bible-alignment');
const { createGlobalRenderer } = require('./src/lib/bible-global-renderer');
const fs = require('node:fs');
const path = require('node:path');
//const { EleventyHtmlBasePlugin } = require("@11ty/eleventy");

module.exports = function(eleventyConfig) {
  generateDictionary();
  const useVerseOverrides = process.env.BEREIA_VERSE_OVERRIDES === '1' || JSON.parse(fs.readFileSync(path.join(__dirname, 'src/tooltip-relations.json'), 'utf8')).useVerseOverrides === true;
  let renderAlignedVerse = createRenderer();
  let globalRenderer;
  eleventyConfig.addWatchTarget('src/tooltip-relations.json', { resetConfig: true });
  eleventyConfig.addWatchTarget('src/biblia/nt/**/*.txt', { resetConfig: true });
  eleventyConfig.addTransform('bible-global-tooltips', function(content, outputPath) {
    if (!outputPath?.endsWith('.html') || !/[/\\]biblia[/\\]/u.test(outputPath)) return content;
    globalRenderer ||= createGlobalRenderer({ approvedRenderer: renderAlignedVerse });
    return globalRenderer.transform(content);
  });
  eleventyConfig.addWatchTarget('src/alinhamentos/', { resetConfig: true });
  eleventyConfig.on('eleventy.before', () => { renderAlignedVerse = useVerseOverrides ? scan(createRenderer()) : createRenderer(); globalRenderer = undefined; });
  eleventyConfig.on('eleventy.after', () => {
    const result = report(renderAlignedVerse);
    if (globalRenderer) {
      const globalReport = globalRenderer.report();
      const filename = path.join(__dirname, 'reports/bible-global-tooltips.json');
      fs.mkdirSync(path.dirname(filename), { recursive: true });
      fs.writeFileSync(filename, JSON.stringify(globalReport, null, 2) + '\n');
      console.log(`Tooltips globais: ${globalReport.totals.tooltips} trechos em ${globalReport.totals.versesWithAutomaticTooltips} versículos.`);
    }
    if (result.pendingVerses) console.warn(`Tooltips: ${result.pendingVerses} versículo(s) com pendências; consulte reports/bible-alignment.json.`);
  });
  eleventyConfig.addWatchTarget('src/_data/nt/dict_lex_nt-lxx_greek-pt.json');
  eleventyConfig.addWatchTarget('src/interlinear/at/*.json');
  eleventyConfig.on('eleventy.beforeWatch', () => generateDictionary());
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

    return `<span id="${abbreviation}_${chapterNumber}-${number}" class="verse"><span class="verse-number">${number}</span><span class="verse-text ${redletter}">${useVerseOverrides ? renderAlignedVerse(content.trim(), abbreviation.toLowerCase(), chapterNumber, number) : content.trim()}</span></span>`;
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
	eleventyConfig.on('eleventy.after', () => {
		execSync('npx pagefind --site _site --output-subdir biblia/pagefind --glob "**/*.html"', {
			encoding: 'utf-8'
		});
	});

	eleventyConfig.addFilter("addZeros", function(value) {
		return String(value).padStart(4, "0");
  });

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
