"""
Maryland COMAR Data Extraction Service

This service handles extraction of childcare regulations from Maryland's
Code of Maryland Regulations (COMAR) system.
"""

import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urljoin, urlparse
import asyncio
import aiohttp
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class MarylandCOMARService:
    """Service for extracting childcare regulations from Maryland COMAR system"""
    
    BASE_URL = "http://mdrules.elaws.us/comar"
    COMAR_SEARCH_URL = "https://dsd.maryland.gov/pages/COMARHome.aspx"
    
    # Maryland childcare regulation subtitles with specific metadata
    CHILDCARE_SUBTITLES = {
        "13a_15": {
            "name": "Family Child Care",
            "full_title": "Code of Maryland Regulations, Title 13A: State Board of Education, Subtitle 15: Family Child Care",
            "facility_type": "Family Child Care Home",
            "last_updated": "02/05/2024"
        },
        "13a_16": {
            "name": "Child Care Centers", 
            "full_title": "Code of Maryland Regulations, Title 13A: State Board of Education, Subtitle 16: Child Care Centers",
            "facility_type": "Child Care Center",
            "last_updated": "02/05/2024"
        },
        "13a_17": {
            "name": "Child Care - Letters of Compliance",
            "full_title": "Code of Maryland Regulations, Title 13A: State Board of Education, Subtitle 17: Child Care - Letters of Compliance", 
            "facility_type": "Other Facility Type",
            "last_updated": "02/05/2024"
        },
        "13a_18": {
            "name": "Large Family Child Care Homes",
            "full_title": "Code of Maryland Regulations, Title 13A: State Board of Education, Subtitle 18: Large Family Child Care Homes",
            "facility_type": "Group/Large Child Care Home",
            "last_updated": "02/05/2024"
        }
    }
    
    def __init__(self):
        self.base_url = "https://dsd.maryland.gov"
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Maryland DSD COMAR regulation structure
        self.regulation_structure = {
            "13A.15": {
                "title": "Family Child Care",
                "facility_type": "Family Child Care",
                "chapters": [
                    "13A.15.01", "13A.15.02", "13A.15.03", "13A.15.04", "13A.15.05",
                    "13A.15.06", "13A.15.07", "13A.15.08", "13A.15.09", "13A.15.10",
                    "13A.15.11", "13A.15.12", "13A.15.13", "13A.15.14", "13A.15.15", "13A.15.16"
                ]
            },
            "13A.16": {
                "title": "Child Care Centers",
                "facility_type": "Child Care Centers",
                "chapters": [
                    "13A.16.01", "13A.16.02", "13A.16.03", "13A.16.04", "13A.16.05",
                    "13A.16.06", "13A.16.07", "13A.16.08", "13A.16.09", "13A.16.10",
                    "13A.16.11", "13A.16.12", "13A.16.13", "13A.16.14", "13A.16.15", "13A.16.16"
                ]
            },
            "13A.17": {
                "title": "Letters of Compliance",
                "facility_type": "Letters of Compliance",
                "chapters": [
                    "13A.17.01", "13A.17.02", "13A.17.03", "13A.17.04", "13A.17.05",
                    "13A.17.06", "13A.17.07", "13A.17.08", "13A.17.09", "13A.17.10",
                    "13A.17.11", "13A.17.12", "13A.17.13", "13A.17.14", "13A.17.15", "13A.17.16", "13A.17.17"
                ]
            },
            "13A.18": {
                "title": "Large Family Child Care Homes",
                "facility_type": "Large Family Child Care Homes",
                "chapters": [
                    "13A.18.01", "13A.18.02", "13A.18.03", "13A.18.04", "13A.18.05",
                    "13A.18.06", "13A.18.07", "13A.18.08", "13A.18.09", "13A.18.10",
                    "13A.18.11", "13A.18.12", "13A.18.13", "13A.18.14", "13A.18.15", "13A.18.16"
                ]
            }
        }

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            timeout=timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_regulation_metadata(self, regulation_code: str) -> Dict:
        """Get metadata for a specific regulation"""
        if regulation_code in self.regulation_structure:
            reg_info = self.regulation_structure[regulation_code]
            return {
                "title": f"MD COMAR {regulation_code} {reg_info['title']}",
                "facility_type": reg_info["facility_type"],
                "last_updated": "02/05/2024",
                "source": "Maryland Division of State Documents (DSD)",
                "regulation_code": regulation_code
            }
        return {}

    async def _fetch_chapter_sections(self, chapter: str) -> List[str]:
        """Get all section numbers for a chapter"""
        sections = []
        
        # Try to get sections from 01 to 20 for each chapter
        for section_num in range(1, 21):
            section_id = f"{chapter}.{section_num:02d}"
            sections.append(section_id)
        
        return sections

    async def _fetch_section_content(self, section: str) -> str:
        """Fetch content from a specific regulation section page"""
        try:
            # Convert section format (e.g., "13A.15.01.01" to "13A.15.01.01")
            url = f"{self.base_url}/regulations/Pages/{section}.aspx"
            
            logger.info(f"Fetching section content from: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find the main content area
                    main_content = soup.find('div', {'id': 'Main_Content'}) or soup.find('main') or soup.find('div', class_='main-content')
                    
                    if main_content:
                        # Extract text content, preserving structure
                        content = self._extract_regulation_text(main_content)
                        if content and len(content.strip()) > 50:  # Only return substantial content
                            return content
                    
                    logger.warning(f"No substantial content found for section {section}")
                    return ""
                else:
                    logger.warning(f"Failed to fetch section {section}: HTTP {response.status}")
                    return ""
                    
        except Exception as e:
            logger.error(f"Error fetching section {section}: {str(e)}")
            return ""

    def _extract_regulation_text(self, content_div) -> str:
        """Extract and format regulation text from content div"""
        if not content_div:
            return ""
        
        # Remove script and style elements
        for script in content_div(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Get text content
        text = content_div.get_text(separator='\n', strip=True)
        
        # Clean up the text
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not self._is_navigation_text(line):
                lines.append(line)
        
        return '\n'.join(lines)

    def _is_navigation_text(self, text: str) -> bool:
        """Check if text is navigation/header/footer content to exclude"""
        nav_patterns = [
            'Skip to Content',
            'Accessibility Information',
            'Home',
            'Publications to Order',
            'COMAR Online',
            'Maryland Register Online',
            'Contact Us',
            'SOS',
            'Go To Home Page',
            'Maryland Division of State Documents',
            'Site Logo',
            'Phone Number:',
            'Office Hours:',
            'Disclaimer',
            'Terms of Use',
            'Privacy Policy',
            'Copyright',
            'eLaws',
            'All rights reserved'
        ]
        
        return any(pattern in text for pattern in nav_patterns)

    async def extract_regulation_content(self, regulation_code: str) -> Tuple[str, int]:
        """Extract complete content for a regulation"""
        try:
            if regulation_code not in self.regulation_structure:
                logger.error(f"Unknown regulation code: {regulation_code}")
                return "", 0
            
            reg_info = self.regulation_structure[regulation_code]
            all_content = []
            
            # Add header
            all_content.append(f"MARYLAND CODE OF REGULATIONS (COMAR)")
            all_content.append(f"Title 13A - Maryland State Board of Education")
            all_content.append(f"Subtitle {regulation_code.split('.')[1]} - {reg_info['title']}")
            all_content.append("=" * 80)
            all_content.append("")
            
            # Process each chapter
            for chapter in reg_info["chapters"]:
                logger.info(f"Processing chapter: {chapter}")
                
                # Get sections for this chapter
                sections = await self._fetch_chapter_sections(chapter)
                
                chapter_content = []
                chapter_content.append(f"CHAPTER {chapter}")
                chapter_content.append("-" * 40)
                
                # Fetch content for each section
                for section in sections:
                    section_content = await self._fetch_section_content(section)
                    if section_content:
                        chapter_content.append(f"\nSection {section}")
                        chapter_content.append(section_content)
                        
                        # Add delay between requests
                        await asyncio.sleep(0.5)
                
                if len(chapter_content) > 2:  # More than just header
                    all_content.extend(chapter_content)
                    all_content.append("")
            
            final_content = '\n'.join(all_content)
            content_length = len(final_content)
            
            logger.info(f"Extracted {content_length} characters for {regulation_code}")
            return final_content, content_length
            
        except Exception as e:
            logger.error(f"Error extracting regulation {regulation_code}: {str(e)}")
            return "", 0

    async def get_all_regulations(self) -> Dict[str, Tuple[str, int]]:
        """Extract content for all regulations"""
        results = {}
        
        for regulation_code in self.regulation_structure.keys():
            logger.info(f"Extracting regulation: {regulation_code}")
            content, length = await self.extract_regulation_content(regulation_code)
            results[regulation_code] = (content, length)
            
            # Add delay between regulations
            await asyncio.sleep(1)
        
        return results

    # Legacy method for backward compatibility
    async def extract_childcare_regulations(self) -> List[Dict]:
        """
        Legacy method - extract regulations and return in old format
        """
        regulations = await self.get_all_regulations()
        
        result = []
        for code, (content, char_count) in regulations.items():
            if content:
                metadata = self.get_regulation_metadata(code)
                result.append({
                    "title": f"MD COMAR {code} {metadata.get('title', '')}",
                    "content": content,
                    "source_url": metadata.get('base_url', ''),
                    "facility_type": metadata.get('facility_type', ''),
                    "last_updated": "02/05/2024"
                })
        
        return result

    def extract_regulations_sync(self) -> List[Dict]:
        """Synchronous wrapper for async extraction"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.extract_childcare_regulations())
        finally:
            loop.close()

    async def _extract_from_pdf_source(
        self, 
        session: aiohttp.ClientSession, 
        subtitle_code: str, 
        subtitle_info: Dict,
        primary_url: str,
        backup_url: Optional[str] = None,
        additional_sources: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """Extract regulations from official PDF sources"""
        
        # Try primary URL first, then backup, then additional sources if available
        urls_to_try = [url for url in [primary_url, backup_url] if url]
        if additional_sources:
            urls_to_try.extend(additional_sources)
        
        all_content = []
        successful_urls = []
        
        for pdf_url in urls_to_try:
            try:
                logger.info(f"Attempting to download PDF from: {pdf_url}")
                
                async with session.get(pdf_url) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to access PDF {pdf_url}: {response.status}")
                        continue
                    
                    pdf_content = await response.read()
                    
                    # Extract text content from PDF
                    extracted_content = await self._extract_pdf_content(
                        pdf_content, subtitle_code, subtitle_info
                    )
                    
                    if extracted_content and len(extracted_content) > 500:
                        all_content.append(extracted_content)
                        successful_urls.append(pdf_url)
                        
                        # If we have substantial content (>140KB), use it
                        if len(extracted_content) > 140000:
                            return {
                                "subtitle_code": subtitle_code,
                                "title": subtitle_info["full_title"],
                                "facility_type": subtitle_info["facility_type"],
                                "content": extracted_content,
                                "source_url": pdf_url,
                                "last_accessed": datetime.now().isoformat(),
                                "last_updated": subtitle_info["last_updated"],
                                "state_territory": "Maryland",
                                "document_type": "Regulation"
                            }
                    
            except Exception as e:
                logger.error(f"Error downloading PDF from {pdf_url}: {str(e)}")
                continue
        
        # If we collected content from multiple sources, combine them
        if all_content:
            combined_content = "\n\n=== COMBINED FROM MULTIPLE SOURCES ===\n\n".join(all_content)
            return {
                "subtitle_code": subtitle_code,
                "title": subtitle_info["full_title"],
                "facility_type": subtitle_info["facility_type"],
                "content": combined_content,
                "source_url": ", ".join(successful_urls),
                "last_accessed": datetime.now().isoformat(),
                "last_updated": subtitle_info["last_updated"],
                "state_territory": "Maryland",
                "document_type": "Regulation"
            }
        
        # If all PDF sources fail, create a placeholder with source information
        logger.warning(f"Could not extract content for {subtitle_code}, creating placeholder")
        return {
            "subtitle_code": subtitle_code,
            "title": subtitle_info["full_title"],
            "facility_type": subtitle_info["facility_type"],
            "content": f"Maryland COMAR {subtitle_code.upper().replace('_', '.')} - {subtitle_info['name']}\n\n"
                      f"This regulation governs {subtitle_info['facility_type'].lower()} operations in Maryland.\n\n"
                      f"For the complete regulation text, please visit:\n"
                      f"- Maryland Public Schools: https://marylandpublicschools.org/\n"
                      f"- Maryland State Child Care Association: https://mscca.org/\n"
                      f"- Official COMAR website: http://mdrules.elaws.us/comar/{subtitle_code}\n\n"
                      f"Last Updated: {subtitle_info['last_updated']}",
            "source_url": primary_url or f"http://mdrules.elaws.us/comar/{subtitle_code}",
            "last_accessed": datetime.now().isoformat(),
            "last_updated": subtitle_info["last_updated"],
            "state_territory": "Maryland",
            "document_type": "Regulation"
        }
    
    async def _extract_pdf_content(
        self, 
        pdf_content: bytes, 
        subtitle_code: str, 
        subtitle_info: Dict
    ) -> Optional[str]:
        """Extract text content from PDF bytes"""
        
        try:
            import io
            import pypdf
            
            # Create a PDF reader from bytes
            pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_content))
            
            extracted_text = []
            subtitle_pattern = subtitle_code.upper().replace('_', '.')
            
            # Extract text from all pages
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and len(page_text.strip()) > 50:
                        # Look for content related to our specific subtitle
                        if subtitle_pattern in page_text or subtitle_info['name'].upper() in page_text.upper():
                            extracted_text.append(f"--- Page {page_num + 1} ---\n{page_text}\n")
                        elif not extracted_text and any(keyword in page_text.upper() for keyword in ['CHILD CARE', 'CHILDCARE', 'COMAR']):
                            # Include general childcare content if we haven't found specific content yet
                            extracted_text.append(f"--- Page {page_num + 1} ---\n{page_text}\n")
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                    continue
            
            if extracted_text:
                combined_text = "\n".join(extracted_text)
                # Clean up the text
                cleaned_text = self._clean_pdf_text(combined_text)
                return cleaned_text
            else:
                logger.warning(f"No relevant content found in PDF for {subtitle_code}")
                return None
                
        except ImportError:
            logger.error("pypdf not available for PDF extraction")
            return None
        except Exception as e:
            logger.error(f"Error extracting PDF content: {str(e)}")
            return None
    
    def _clean_pdf_text(self, text: str) -> str:
        """Clean and format PDF extracted text"""
        
        # Remove excessive whitespace and normalize line breaks
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Remove excessive spaces
                line = re.sub(r'\s+', ' ', line)
                cleaned_lines.append(line)
        
        # Join lines and add proper spacing
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Fix common PDF extraction issues
        cleaned_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned_text)  # Add space between camelCase
        cleaned_text = re.sub(r'(\.)([A-Z])', r'\1 \2', cleaned_text)     # Add space after periods
        cleaned_text = re.sub(r'\n+', '\n\n', cleaned_text)              # Normalize paragraph breaks
        
        return cleaned_text.strip() 