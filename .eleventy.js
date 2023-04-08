const { EleventyHtmlBasePlugin } = require("@11ty/eleventy");

module.exports = function(eleventyConfig) {

  eleventyConfig.addPassthroughCopy('src/css')
  
  return {
    dir: {
      input: "src",
      output: "docs"
    },
    passthroughFileCopy: true,
    pathPrefix: "/nt-interlinear"
  }

  eleventyConfig.addPlugin(EleventyHtmlBasePlugin)
}