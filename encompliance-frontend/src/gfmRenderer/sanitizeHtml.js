/*
  Description: Utility for sanitizing HTML content, allowing safe rendering of Markdown and GFM output.
  Purpose: Prevents XSS and ensures only safe, necessary tags and attributes are allowed in rendered HTML.
*/
const sanitizeHtml = require('sanitize-html')

function sanitize(html) {
  return sanitizeHtml(html, {
    // Allow more tags commonly used in Markdown and needed for styling/functionality
    allowedTags: sanitizeHtml.defaults.allowedTags.concat([
      'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'pre', 'code', 'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'input' // Added common markdown elements + input for task lists
    ]),
    allowedAttributes: {
      ...sanitizeHtml.defaults.allowedAttributes,
      a: ['href', 'name', 'target', 'class'],
      img: ['src', 'alt', 'title', 'width', 'height'],
      span: ['class'], // For KaTeX and potentially others
      code: ['class'], // For highlight.js (e.g., class="language-js hljs")
      pre: ['class'], // For highlight.js wrapper
      div: ['class'], // Allow classes on divs (might be used by plugins)
      p: ['class'], // Allow class for gfm-paragraph
      ul: ['class'], // Allow class for task lists
      li: ['class', 'disabled', 'checked'], // Allow attributes for task lists
      input: ['type', 'checked', 'disabled', 'class'] // Allow attributes for task list checkboxes
    },
    allowedSchemes: ['http', 'https', 'mailto', 'ftp'],
    allowedClasses: {
      '*': [ 'hljs-*', 'language-*', 'katex*', 'gfm-*', 'task-list*', 'math*' ] // Allow classes used by highlightjs, katex, task lists, etc.
    },
    // Allow style attribute for specific KaTeX elements if needed, otherwise restrict
    // allowedStyles: {
    //   'span': { 'color': [/^#(0x)?[0-9a-f]+$/i, /^rgb\(\s*\d+%?\s*,\s*\d*%?\s*,\s*\d*%?\s*\)$/] }
    // },
    // Ensure self-closing tags are handled correctly
    selfClosing: [ 'img', 'br', 'hr', 'area', 'base', 'basefont', 'input', 'link', 'meta' ]
  })
}

module.exports = sanitize 