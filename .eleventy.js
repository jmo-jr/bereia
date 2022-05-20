module.exports = function(eleventyConfig) {
  eleventyConfig.addPassthroughCopy('css')
  return {
    passthroughFileCopy: true,
    dir: {
      output: "docs"
    }
  }

  pathPrefix: "/nt-interlinear/"
}