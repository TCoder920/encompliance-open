"""
Brave Web Search Service

This module provides an async client for the Brave Web Search API, allowing the backend to perform live web searches.
It also fetches and processes actual web page content to provide comprehensive information to the LLM.
"""
import httpx
import asyncio
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

async def brave_search(query: str, count: int = 5) -> dict:
    """
    Call Brave Web Search API and return JSON.
    """
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": settings.BRAVE_API_KEY
    }
    params = {"q": query, "count": count}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

async def fetch_page_content(url: str, max_chars: int = 5000) -> Optional[str]:
    """
    Fetch and extract text content from a web page.
    
    Args:
        url: The URL to fetch
        max_chars: Maximum characters to return
        
    Returns:
        Extracted text content or None if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            # Only process HTML content
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return None
                
            # Parse HTML and extract text
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit length
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
                
            return text
            
    except Exception as e:
        logger.warning(f"Failed to fetch content from {url}: {str(e)}")
        return None

async def enhanced_web_search(query: str, count: int = 3) -> List[Dict]:
    """
    Perform web search and fetch actual content from the top results.
    
    Args:
        query: Search query
        count: Number of results to process (max 3 for performance)
        
    Returns:
        List of results with actual content
    """
    try:
        # Get search results from Brave
        search_results = await brave_search(query, count)
        
        if not search_results or 'web' not in search_results:
            return []
            
        web_results = search_results['web']
        if not web_results or 'results' not in web_results:
            return []
            
        results = web_results['results'][:count]  # Limit for performance
        enhanced_results = []
        
        # Fetch content for each result concurrently
        tasks = []
        for result in results:
            url = result.get('url', '')
            if url:
                tasks.append(fetch_page_content(url))
            else:
                tasks.append(asyncio.create_task(asyncio.sleep(0, result=None)))
        
        # Wait for all content fetching to complete
        contents = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine search results with fetched content
        for i, result in enumerate(results):
            title = result.get('title', 'No title')
            url = result.get('url', '')
            description = result.get('description', 'No description available')
            
            # Get the fetched content
            content = None
            if i < len(contents) and not isinstance(contents[i], Exception):
                content = contents[i]
            
            enhanced_result = {
                'title': title,
                'url': url,
                'description': description,
                'content': content,
                'has_content': content is not None
            }
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
        
    except Exception as e:
        logger.error(f"Error in enhanced web search: {str(e)}")
        return []

def format_enhanced_search_results(results: List[Dict]) -> str:
    """
    Format enhanced search results for the assistant, including actual content.
    
    Args:
        results: List of enhanced search results
        
    Returns:
        Formatted string with search results and content
    """
    try:
        if not results:
            return "No search results found."
        
        formatted = "Web Search Results:\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            url = result.get('url', '')
            description = result.get('description', 'No description available')
            content = result.get('content')
            has_content = result.get('has_content', False)
            
            formatted += f"{i}. **{title}**\n"
            formatted += f"   URL: {url}\n"
            formatted += f"   {description}\n"
            
            if has_content and content:
                # Add a sample of the actual content
                content_preview = content[:500] + "..." if len(content) > 500 else content
                formatted += f"   Content: {content_preview}\n"
            else:
                formatted += f"   Content: Unable to fetch full content\n"
                
            formatted += "\n"
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting enhanced search results: {str(e)}")
        return f"Error formatting search results: {str(e)}" 