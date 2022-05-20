module.exports = function(eleventyConfig) {
  eleventyConfig.addPassthroughCopy('css')
  return {
    passthroughFileCopy: true,
    dir: {
      input: "src",
      output: "docs"
    }
  }

  pathPrefix: "/nt-interlinear/"
}