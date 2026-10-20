/*
  Description: Utility for creating a Markdown parser with GFM, emoji, task lists, and KaTeX support.
  Purpose: Provides a configured MarkdownIt instance for rendering rich, safe, and styled Markdown content in the app.
*/
const MarkdownIt = require('markdown-it')
const emoji = require('markdown-it-emoji')
const taskLists = require('markdown-it-task-lists')
const katex = require('markdown-it-katex')
const highlightCode = require('./highlightCode')

function getMarkdownParser() {
  const md = new MarkdownIt({
    html: true,        // Allow HTML tags in source
    xhtmlOut: false,     // Don't use XHTML strict closing tags (/>)
    breaks: true,        // Convert newlines in paragraphs to <br>
    langPrefix: 'language-', // CSS language prefix for fenced blocks
    linkify: true,       // Autoconvert URL-like text to links
    typographer: true,   // Enable smartypants-style substitutions (e.g., -- to —)
    quotes: '“”‘’',      // Corrected: Define quote characters
    highlight: highlightCode // Use the custom highlighter
  })

  // --- Plugins ---
  md.use(emoji)
  md.use(taskLists, { 
      enabled: true, 
      label: true, // Add label tag around checkbox/text
      labelAfter: true // Place label after checkbox
  }) 
  md.use(katex, { "throwOnError": false, "errorColor": " #cc0000" })

  // --- Custom Rules (Optional) ---
  // Add a class to paragraphs for styling
  md.renderer.rules.paragraph_open = (tokens, idx, options, env, self) => {
    // Check if the paragraph is part of a list item
    let isInList = false;
    if (idx > 0) {
      const prevToken = tokens[idx - 1];
      // Simple check: if previous token indicates list start or item start
      if (prevToken.type.includes('_list_open') || prevToken.type.includes('list_item_open')) {
        isInList = true;
      }
    }
    // Only add class if it's not inside a list item to avoid interfering with list styling
    return isInList ? '<p>' : '<p class="gfm-paragraph">';
  };
  
  // Add target="_blank" to external links
  const defaultRender = md.renderer.rules.link_open || function(tokens, idx, options, env, self) {
    return self.renderToken(tokens, idx, options);
  };
  md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
    const aIndex = tokens[idx].attrIndex('target');
    if (aIndex < 0) {
      tokens[idx].attrPush(['target', '_blank']); // Add target="_blank"
    } else {
      tokens[idx].attrs[aIndex][1] = '_blank'; // Update existing target
    }
    // Add rel="noopener noreferrer" for security
    const relIndex = tokens[idx].attrIndex('rel');
     if (relIndex < 0) {
      tokens[idx].attrPush(['rel', 'noopener noreferrer']);
    } else {
      if (!tokens[idx].attrs[relIndex][1].includes('noopener')) {
           tokens[idx].attrs[relIndex][1] += ' noopener';
      }
       if (!tokens[idx].attrs[relIndex][1].includes('noreferrer')) {
           tokens[idx].attrs[relIndex][1] += ' noreferrer';
      }
    }
    return defaultRender(tokens, idx, options, env, self);
  };

  return md
}

module.exports = getMarkdownParser 