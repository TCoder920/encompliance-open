/*
  Description: Utility for syntax highlighting code blocks using highlight.js.
  Purpose: Enhances readability of code snippets in rendered Markdown by applying language-specific syntax highlighting.
*/
const hljs = require('highlight.js')

function highlightCode(str, lang) {
  if (lang && hljs.getLanguage(lang)) {
    try {
      return hljs.highlight(str, { language: lang }).value
    } catch (_) {
      return '' // Return empty string on error
    }
  }
  return '' // Return empty string if language not supported or not provided
}

module.exports = highlightCode 