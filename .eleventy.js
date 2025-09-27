const { execSync } = require('child_process')
//const { EleventyHtmlBasePlugin } = require("@11ty/eleventy");

module.exports = function(eleventyConfig) {

  eleventyConfig.addPassthroughCopy('src/css');
  eleventyConfig.addPassthroughCopy('src/img');

  // Habilita o plugin que adiciona utilitários para URLs com pathPrefix
  //eleventyConfig.addPlugin(EleventyHtmlBasePlugin);

	//PageFind search
	eleventyConfig.on('eleventy.after', () => {
    execSync(`npx pagefind --site _site/biblia --output-subdir pagefind --glob \"**/*.html\"`, { encoding: 'utf-8' })
  })

  return {
    // ajuste para o prefixo do site hospedado (terminar com "/")
    pathPrefix: "/nt-interlinear/",
    dir: {
      input: "src",
      includes: "_includes",
      output: "_site"
    }
  };
};