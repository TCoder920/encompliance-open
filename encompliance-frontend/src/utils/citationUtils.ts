/*
  Description: Utility functions for parsing, extracting, and preparing citations in AI-generated responses.
  Purpose: Enables structured handling and rendering of legal or document citations for compliance and traceability.
*/

/**
 * Utilities for handling and parsing citations in AI responses
 */

/**
 * Regular expression to match document citation formats like 【4:4†source】 or 【2:1】
 * Format: 【documentIndex:pageNumber†(optional source name)】
 */
const DOCUMENT_CITATION_REGEX = /【(\d+):(\d+)(?:†([^】]*))?】/g;

/**
 * Regular expression to match web search citation formats like 【functions.web_search 1】
 * Format: 【functions.web_search N】
 */
const WEB_SEARCH_CITATION_REGEX = /【functions\.web_search\s+(\d+)】/g;

/**
 * Combined regex to match all citation types
 */
const ALL_CITATIONS_REGEX = /【(?:(\d+):(\d+)(?:†([^】]*))?|functions\.web_search\s+(\d+))】/g;

/**
 * Parsed citation structure
 */
export interface Citation {
  sourceId: string;
  page?: string;
  section?: string;
  sourceName?: string;
  original: string;
  type: 'document' | 'web_search';
  searchIndex?: number; // For web search citations
}

/**
 * Web search result structure (for storing search results context)
 */
export interface WebSearchResult {
  title: string;
  url: string;
  description: string;
}

/**
 * Parse a citation from various formats
 * @param citation The citation string to parse
 * @returns Structured citation data or null if invalid
 */
export const parseCitation = (citation: string): Citation | null => {
  // Try document citation format first
  DOCUMENT_CITATION_REGEX.lastIndex = 0;
  const docMatch = DOCUMENT_CITATION_REGEX.exec(citation);
  if (docMatch) {
    const [original, docIndex, page, sourceName] = docMatch;
    return {
      sourceId: `doc-${docIndex}`,
      page,
      sourceName: sourceName || undefined,
      original,
      type: 'document'
    };
  }

  // Try web search citation format
  WEB_SEARCH_CITATION_REGEX.lastIndex = 0;
  const webMatch = WEB_SEARCH_CITATION_REGEX.exec(citation);
  if (webMatch) {
    const [original, searchIndex] = webMatch;
    return {
      sourceId: `web-search-${searchIndex}`,
      original,
      type: 'web_search',
      searchIndex: parseInt(searchIndex, 10)
    };
  }

  return null;
};

/**
 * Extract all citations from a text
 * @param text Text containing citations
 * @returns Array of parsed citations
 */
export const extractCitations = (text: string): Citation[] => {
  const citations: Citation[] = [];
  let match;
  
  // Reset regex state
  ALL_CITATIONS_REGEX.lastIndex = 0;
  
  while ((match = ALL_CITATIONS_REGEX.exec(text)) !== null) {
    const [original, docIndex, page, sourceName, searchIndex] = match;
    
    if (searchIndex) {
      // Web search citation
      citations.push({
        sourceId: `web-search-${searchIndex}`,
        original,
        type: 'web_search',
        searchIndex: parseInt(searchIndex, 10)
      });
    } else if (docIndex && page) {
      // Document citation
      citations.push({
        sourceId: `doc-${docIndex}`,
        page,
        sourceName: sourceName || undefined,
        original,
        type: 'document'
      });
    }
  }
  
  return citations;
};

/**
 * Replace citation markers in text with HTML/JSX-compatible markers
 * This function doesn't render components, just prepares text for React
 * @param text Text with citation markers
 * @returns Text with citations replaced with data attributes
 */
export const prepareCitationsForRendering = (text: string): string => {
  // Replace document citations
  let processedText = text.replace(DOCUMENT_CITATION_REGEX, (match, docIndex, page, sourceName) => {
    const citation = JSON.stringify({
      sourceId: `doc-${docIndex}`,
      page,
      sourceName: sourceName || undefined,
      type: 'document'
    }).replace(/"/g, '&quot;');
    
    return `<span class="citation-marker" data-citation="${citation}">[Source ${docIndex}:${page}]</span>`;
  });

  // Replace web search citations
  processedText = processedText.replace(WEB_SEARCH_CITATION_REGEX, (match, searchIndex) => {
    const citation = JSON.stringify({
      sourceId: `web-search-${searchIndex}`,
      type: 'web_search',
      searchIndex: parseInt(searchIndex, 10)
    }).replace(/"/g, '&quot;');
    
    return `<span class="citation-marker" data-citation="${citation}">[Web Search ${searchIndex}]</span>`;
  });

  return processedText;
};

/**
 * Create a mapping function for your document references
 * This should be customized based on your application's document system
 * @param sourceId The source ID to map
 * @returns Actual document ID or URL in your system
 */
export const mapSourceIdToDocument = (sourceId: string): string => {
  // This is a placeholder - you should implement based on your document system
  // For example, you might look up IDs in a context, database, etc.
  if (sourceId.startsWith('doc-')) {
    const index = sourceId.substring(4);
    // Map to actual document IDs or return as is
    return sourceId;
  }
  return sourceId;
};

/**
 * Extract web search results from formatted search results text
 * @param searchResultsText The formatted search results from the backend
 * @returns Array of parsed web search results
 */
export const parseWebSearchResults = (searchResultsText: string): WebSearchResult[] => {
  const results: WebSearchResult[] = [];
  
  // Parse the formatted search results
  // Expected format from backend: 
  // "1. **Title**\n   URL: url\n   description\n\n"
  // Updated pattern to handle description on separate line
  const resultPattern = /(\d+)\.\s*\*\*([^*\n]+)\*\*\s*\n\s*URL:\s*([^\n]+)\s*\n\s*([^\n]+(?:\n(?!\d+\.\s*\*\*)[^\n]*)*)/g;
  
  let match;
  while ((match = resultPattern.exec(searchResultsText)) !== null) {
    const [, index, title, url, description] = match;
    results.push({
      title: title.trim(),
      url: url.trim(),
      description: description.trim().replace(/\n/g, ' ') // Clean up multi-line descriptions
    });
  }
  
  // If the above pattern doesn't work, try a simpler line-by-line approach
  if (results.length === 0) {
    const lines = searchResultsText.split('\n');
    let currentResult: Partial<WebSearchResult> = {};
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Check for numbered title line: "1. **Title**"
      const titleMatch = line.match(/^(\d+)\.\s*\*\*([^*]+)\*\*/);
      if (titleMatch) {
        // Save previous result if complete
        if (currentResult.title && currentResult.url && currentResult.description) {
          results.push(currentResult as WebSearchResult);
        }
        // Start new result
        currentResult = { title: titleMatch[2].trim() };
        continue;
      }
      
      // Check for URL line: "URL: https://..." (may have leading whitespace)
      const urlMatch = line.match(/^\s*URL:\s*(.+)$/);
      if (urlMatch && currentResult.title) {
        currentResult.url = urlMatch[1].trim();
        
        // Look ahead for description on next non-empty line
        for (let j = i + 1; j < lines.length; j++) {
          const nextLine = lines[j].trim();
          if (nextLine && !nextLine.match(/^\d+\.\s*\*\*/) && !nextLine.startsWith('URL:')) {
            currentResult.description = nextLine;
            i = j; // Skip to this line in the main loop
            break;
          } else if (nextLine.match(/^\d+\.\s*\*\*/)) {
            // Hit the next result, stop looking
            break;
          }
        }
        
        // If we have all parts, add the result
        if (currentResult.title && currentResult.url && currentResult.description) {
          results.push(currentResult as WebSearchResult);
          currentResult = {};
        }
        continue;
      }
    }
    
    // Add the last result if complete
    if (currentResult.title && currentResult.url && currentResult.description) {
      results.push(currentResult as WebSearchResult);
    }
  }
  
  return results;
}; 