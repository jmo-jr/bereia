const { EleventyHtmlBasePlugin } = require("@11ty/eleventy");

module.exports = function(eleventyConfig) {

  eleventyConfig.addPassthroughCopy('src/css');

  // Habilita o plugin que adiciona utilitários para URLs com pathPrefix
  //eleventyConfig.addPlugin(EleventyHtmlBasePlugin);

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