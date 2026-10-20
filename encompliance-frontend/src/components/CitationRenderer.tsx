/*
  Description: CitationRenderer component. Renders legal or regulatory citations in a standardized format within the application.
  Purpose: Ensures consistent and accessible display of citations for compliance references.
*/
import React from 'react';
import { Components } from 'react-markdown';
import SourceCitation from './SourceCitation';
import { extractCitations, Citation, WebSearchResult } from '../utils/citationUtils';

// Define Document type locally (consider moving to shared types file)
interface Document {
  id: number;
  filename: string;
  // Add other fields if necessary
}

// Define the type for the navigateTo function
type NavigateToFunction = (page: string, params?: any) => void;

/**
 * Custom ReactMarkdown components factory that handles citations in the text.
 * Requires navigateTo function and the list of documents for context.
 */
export const createCitationRenderer = (
  navigateTo: NavigateToFunction,
  documents: Document[] = [], // Use locally defined Document type
  webSearchResults: WebSearchResult[] = [] // Add web search results
): Components => {

  // Custom text renderer to find and replace citation markers
  const renderText = (props: { children?: React.ReactNode }): React.ReactNode => {
    const text = props.children;

    if (typeof text !== 'string') {
      return <>{text}</>; // Return non-string children as is
    }

    // Extract all citations from the text
    const citations = extractCitations(text);
    if (citations.length === 0) {
      // No citations found, return the original text
      return text;
    }

    // Split the text into segments based on citation positions
    const segments: React.ReactNode[] = [];
    let lastIndex = 0;

    citations.forEach((citation, i) => {
      // Add text before citation
      const startIndex = text.indexOf(citation.original, lastIndex);
      if (startIndex === -1) {
        // Don't log errors, just handle gracefully
        return; 
      }
      if (startIndex > lastIndex) {
        segments.push(text.substring(lastIndex, startIndex));
      }

      // Add citation component, passing necessary props based on citation type
      if (citation.type === 'web_search') {
        segments.push(
          <SourceCitation
            key={`citation-${i}`}
            sourceId={citation.sourceId}
            navigateTo={navigateTo}
            documents={documents}
            webSearchResults={webSearchResults}
            citationType="web_search"
            searchIndex={citation.searchIndex}
          >
            {/* Display web search result title if available */}
            {citation.searchIndex && webSearchResults.length > 0 && citation.searchIndex <= webSearchResults.length
              ? webSearchResults[citation.searchIndex - 1]?.title || `Web Search ${citation.searchIndex}`
              : `Web Search ${citation.searchIndex || ''}`
            }
          </SourceCitation>
        );
      } else {
        // Document citation
        segments.push(
          <SourceCitation
            key={`citation-${i}`}
            sourceId={citation.sourceId}
            page={citation.page}
            navigateTo={navigateTo}
            documents={documents}
            citationType="document"
          >
            {/* Use sourceName if available, otherwise format nicely */}
            {citation.sourceName ? citation.sourceName : `Source ${citation.sourceId.replace('doc-', '')}`}
          </SourceCitation>
        );
      }

      lastIndex = startIndex + citation.original.length;
    });

    // Add any remaining text after the last citation
    if (lastIndex < text.length) {
      segments.push(text.substring(lastIndex));
    }

    // Return the array of segments (text and components)
    return segments;
  };

  // Return the components object for ReactMarkdown
  return {
    p: (props: any) => {
      // Process children of the paragraph
      const processedChildren = React.Children.map(props.children, child => {
        if (typeof child === 'string') {
          return renderText({ children: child });
        }
        return child;
      });
      return <p className="mb-2">{processedChildren}</p>;
    },
    // Keep other customizations
    ul: (props: any) => <ul className="mb-3 list-disc pl-5" {...props} />,
    ol: (props: any) => <ol className="mb-3 list-decimal pl-5" {...props} />,
    li: (props: any) => <li className="mb-1" {...props} />,
    table: (props: any) => (
      <div className="overflow-x-auto mb-3">
        <table style={{ border: '1px solid #9ca3af' }} className="table-auto border-collapse" {...props} />
      </div>
    ),
    th: (props: any) => <th style={{ border: '1px solid #d1d5db', padding: '0.5rem' }} {...props} />,
    td: (props: any) => <td style={{ border: '1px solid #d1d5db', padding: '0.5rem' }} {...props} />,
    pre: (props: any) => <pre className="overflow-x-auto bg-gray-100 dark:bg-gray-800 p-2 rounded mb-3" {...props} />,
  };
};

export default createCitationRenderer; 