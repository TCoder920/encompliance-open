/*
  Description: Utility for rendering Markdown to sanitized HTML using configured Markdown parser and sanitizer.
  Purpose: Safely converts user or AI-generated Markdown into HTML for display in the application UI.
*/
const getMarkdownParser = require('./markdownParser')
const sanitize = require('./sanitizeHtml')

function renderMarkdown(rawMarkdown) {
  if (typeof rawMarkdown !== 'string') {
    console.warn('renderMarkdown received non-string input:', rawMarkdown);
    return ''; // Return empty string for non-string input
  }
  try {
    const md = getMarkdownParser()
    const dirtyHtml = md.render(rawMarkdown.trim()) // Trim whitespace before rendering
    return sanitize(dirtyHtml)
  } catch (error) {
    console.error("Error rendering markdown:", error);
    // Fallback: return the sanitized original markdown (or just a basic error message)
    return sanitize(`<p>Error rendering content.</p><pre><code>${rawMarkdown}</code></pre>`);
  }
}

module.exports = renderMarkdown 