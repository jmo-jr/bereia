const { execSync } = require('child_process')
//const { EleventyHtmlBasePlugin } = require("@11ty/eleventy");

module.exports = function(eleventyConfig) {

  eleventyConfig.addPassthroughCopy('src/css');
  eleventyConfig.addPassthroughCopy('src/img');
	eleventyConfig.addPassthroughCopy("src/assets");
	eleventyConfig.addPassthroughCopy("src/manifest.json");
	eleventyConfig.addPassthroughCopy("src/assets/icons");
	eleventyConfig.addPassthroughCopy("src/service-worker.js");

	//PageFind search
	eleventyConfig.on('eleventy.after', () => {
    execSync(`npx pagefind --site _site/biblia --output-subdir pagefind --glob \"**/*.html\"`, { encoding: 'utf-8' })
  })

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