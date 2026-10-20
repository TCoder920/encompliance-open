# Citation Format Documentation

## Overview

The Encompliance AI Assistant uses a structured citation format to reference specific sources, pages, and sections in compliance documentation, as well as web search results. This document explains how citations work and how to interpret them.

## Citation Formats

The system supports two types of citations:

### 1. Document Citations (Legacy Format)
For referencing uploaded PDF documents, the system supports the following citation pattern:

```
【documentIndex:pageNumber†sourceName】
```

For example: 
- `【2:15】` refers to document #2, page 15, with no explicit source name
- `【1:42†Texas Daycare Manual】` refers to document #1, page 42, from "Texas Daycare Manual"

### 2. Web Search Citations
For referencing web search results, the system uses:

```
【functions.web_search N】
```

For example:
- `【functions.web_search 1】` refers to the first web search result
- `【functions.web_search 2】` refers to the second web search result

### 3. Natural Language Citations (Preferred)
The AI is instructed to use natural language citations for document references:

- **Page references**: use **Page XX** format (bold)
- **Section references**: use `§XXX.XXX` format (code style)
- **Document titles**: use *Title of Document* format (italics)

Example: "According to the *Idaho Child Care Licensing Manual* (**Page 15**), `§101.02` specifies that..."

## How Citations Work

1. **Document Citations**: When the AI responds with a document citation in the `【】` format, the frontend application:
   - Parses the citation format
   - Extracts the document ID, page number, and optional source name
   - Renders a clickable citation component 
   - Links directly to the referenced document at the specific page

2. **Web Search Citations**: When the AI responds with a web search citation:
   - The frontend extracts web search results from the conversation
   - Parses the `【functions.web_search N】` format
   - Renders a clickable citation component with a green background
   - Opens the actual web source in a new tab when clicked

3. **Natural Language Citations**: These are displayed as formatted text without special processing.

## For Developers

The citation system consists of several components:

- `SourceCitation.tsx`: The React component that renders individual citations
- `CitationRenderer.tsx`: Custom renderer for ReactMarkdown that processes citations
- `citationUtils.ts`: Utility functions for parsing and handling citation markers

### Citation Types

The system now handles multiple citation types:

```typescript
interface Citation {
  sourceId: string;
  page?: string;
  section?: string;
  sourceName?: string;
  original: string;
  type: 'document' | 'web_search';
  searchIndex?: number; // For web search citations
}
```

### Web Search Results

Web search results are extracted from AI messages and passed to the citation renderer:

```typescript
interface WebSearchResult {
  title: string;
  url: string;
  description: string;
}
```

## For Content Authors

If you're creating content that will be processed by the AI, you don't need to use special citation formats - the AI will automatically generate proper citations when referencing documents or web search results.

## Technical Details

- **Document citation regex**: `/【(\d+):(\d+)(?:†([^】]*))?】/g`
- **Web search citation regex**: `/【functions\.web_search\s+(\d+)】/g`
- **Combined regex**: `/【(?:(\d+):(\d+)(?:†([^】]*))?|functions\.web_search\s+(\d+))】/g`
- Document IDs are mapped from indices to actual document identifiers
- Web search results are extracted from conversation messages and linked to citations
- The system handles nested citations and multiple citations in a single paragraph
- Web search citations open external links in new tabs
- Document citations navigate to the document viewer 