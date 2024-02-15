//const { EleventyHtmlBasePlugin } = require("@11ty/eleventy");

module.exports = function(eleventyConfig) {

  eleventyConfig.addPassthroughCopy('src/css');

  // eleventyConfig.addPlugin(EleventyHtmlBasePlugin,
  // {
  //   baseHref: eleventyConfig.pathPrefix,
  //   extensions: "html",
  //   filters: {
  //     base: "htmlBaseUrl",
  //     html: "transformWithHtmlBase",
  //     pathPrefix: "addPathPrefixToUrl",
  //   },
  // });
  
  return {
    dir: {
      input: "src",
      output: "docs"
    },
    passthroughFileCopy: true,
    pathPrefix: "/nt-interlinear/"
  }
}