import React from 'react';
import { ExternalLink, Search } from 'lucide-react';
import { WebSearchResult } from '../utils/citationUtils';

interface Document {
  id: number;
  filename: string;
  // Add other fields if necessary based on actual structure
}

interface SourceCitationProps {
  sourceId: string; // Expected format: "doc-index" (e.g., "doc-1") or "web-search-N"
  page?: string;
  section?: string; // Keep section for potential future use
  children?: React.ReactNode;
  navigateTo: (page: string, params?: any) => void; // Function to navigate
  documents: Document[]; // Array of user documents in the order provided to AI
  webSearchResults?: WebSearchResult[]; // Array of web search results
  citationType?: 'document' | 'web_search'; // Type of citation
  searchIndex?: number; // Index for web search citations
}

/*
  Description: SourceCitation component. Displays a formatted citation for a referenced document or regulation.
  Purpose: Provides users with clear attribution and traceability for compliance information.
*/

/**
 * Component for rendering structured source citations as clickable buttons
 * that navigate to the document viewer or open external web links.
 */
const SourceCitation: React.FC<SourceCitationProps> = ({ 
  sourceId, 
  page, 
  // section, // Not used in navigation yet
  children,
  navigateTo,
  documents,
  webSearchResults = [],
  citationType = 'document',
  searchIndex
}) => {

  const handleClick = () => {
    if (citationType === 'web_search' && searchIndex !== undefined) {
      // Handle web search citation
      const resultIndex = searchIndex - 1; // Convert to 0-based index
      if (resultIndex >= 0 && resultIndex < webSearchResults.length) {
        const result = webSearchResults[resultIndex];
        // Open the URL in a new tab
        window.open(result.url, '_blank', 'noopener,noreferrer');
      } else {
        // Fallback: if we don't have the specific search result, 
        // try to provide a helpful search based on the context
        // Create a generic search URL based on common patterns
        // This is a fallback when the AI doesn't include search results in the response
        const searchQuery = encodeURIComponent('latest executive order 2025 White House presidential actions');
        const searchUrl = `https://www.google.com/search?q=${searchQuery}`;
        window.open(searchUrl, '_blank', 'noopener,noreferrer');
      }
      return;
    }

    // Handle document citation (existing logic)
    const docIndexMatch = sourceId.match(/^doc-(\d+)$/);
    if (!docIndexMatch) {
      // Silently handle invalid source ID
      return;
    }
    
    const docIndex = parseInt(docIndexMatch[1], 10);
    // Map the 1-based index from AI to 0-based array index
    const arrayIndex = docIndex - 1; 
    
    if (arrayIndex < 0 || arrayIndex >= documents.length) {
      // Silently handle out of bounds index
      return; 
    }

    const targetDocument = documents[arrayIndex];
    const documentId = targetDocument.id; // Get the actual document ID
    
    // Prepare navigation parameters
    const params: any = { documentId };
    if (page) {
      // Ensure page is a number if the viewer expects it
      const pageNumber = parseInt(page, 10);
      if (!isNaN(pageNumber)) {
        params.page = pageNumber;
      }
    }
    
    // Navigate to the document viewer page
    navigateTo('documentViewer', params); 
  };

  // Determine the display text and icon based on citation type
  const getDisplayContent = () => {
    if (citationType === 'web_search') {
      // For web search citations, prefer children prop (which contains the actual title)
      // but fall back to search result data if children is not provided
      let displayText = children as string;
      
      // If children is provided and it's not just "Web Search N", use it
      if (displayText && !displayText.match(/^Web Search \d+$/)) {
        // Children contains actual content, use it
      } else if (searchIndex !== undefined && webSearchResults.length > 0) {
        // Try to get from webSearchResults
        const resultIndex = searchIndex - 1;
        if (resultIndex >= 0 && resultIndex < webSearchResults.length) {
          const result = webSearchResults[resultIndex];
          displayText = result.title || `Web Search ${searchIndex}`;
        }
      }
      
      // Final fallback
      if (!displayText || displayText.match(/^Web Search \d+$/)) {
        displayText = `Search Result ${searchIndex || ''}`;
      }

      // Get tooltip information
      let tooltipText = 'Click to view web search result';
      if (searchIndex !== undefined && webSearchResults.length > 0) {
        const resultIndex = searchIndex - 1;
        if (resultIndex >= 0 && resultIndex < webSearchResults.length) {
          const result = webSearchResults[resultIndex];
          tooltipText = `${result.title}\n${result.url}\n${result.description}`;
        }
      } else {
        tooltipText = 'Click to search for related information';
      }

      return {
        text: displayText,
        icon: <Search size={12} />,
        title: tooltipText
      };
    }

    // Document citation
    return {
      text: children || `Source: ${sourceId.replace('doc-', '')}${page ? `, p.${page}` : ''}`,
      icon: <ExternalLink size={12} />,
      title: 'View document'
    };
  };

  const { text, icon, title } = getDisplayContent();

  // Use a button for navigation action
  return (
    <button 
      onClick={handleClick}
      className={`inline-flex items-center px-2 py-1 mx-1 rounded-md text-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
        citationType === 'web_search' 
          ? 'bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300 hover:bg-green-100 dark:hover:bg-green-800 focus:ring-green-500'
          : 'bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-800 focus:ring-blue-500'
      }`}
      type="button" // Explicitly set type to avoid form submission issues if nested
      title={title}
    >
      <span className="mr-1">{text}</span>
      {icon}
    </button>
  );
};

export default SourceCitation;
// Document type is now defined locally above
// Consider moving to a shared types file later. 