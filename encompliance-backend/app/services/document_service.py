"""
Document Service Module

This module provides services for handling document management in the EnCompliance application.
It includes utilities for PDF extraction, file storage, document listing, and metadata processing.

Key functionalities:
- PDF text extraction and structure analysis
- File type and mimetype detection
- Document upload, listing, and retrieval
- User-document relationship management
- Error handling for file operations

Dependencies:
- pypdf: For PDF parsing
- sqlalchemy: For database operations
- fastapi: For dependency injection
- os, re, hashlib: For file and text processing
"""

import os
import pypdf
import traceback
import mimetypes
import shutil
import re
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from app.core.config import get_settings
from app.models.document import Document
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from fastapi import Depends
from app.models.user import User
from datetime import datetime
from app.models.regulation import Regulation
from app.models.user_document import UserDocument
from sqlalchemy import func

settings = get_settings()

# HARDCODED absolute path to storage directory - this can never be overridden
def get_storage_path():
    """
    Returns the hardcoded absolute path to the storage directory.
    This is designed to prevent any chance of files being saved in the backend.
    """
    return settings.PDF_STORAGE_PATH

# Utility function to extract text from PDF
def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extract text from a PDF file with enhanced structure prioritization.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing structured text with title, headings, and content
    """
    try:
        print(f"Extracting text from PDF: {pdf_path}")
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            error_msg = f"PDF file not found: {pdf_path}"
            print(error_msg)
            return {"error": error_msg}
        
        # Check file size
        file_size = os.path.getsize(pdf_path)
        print(f"PDF file size: {file_size} bytes")
        
        if file_size == 0:
            error_msg = f"PDF file is empty: {pdf_path}"
            print(error_msg)
            return {"error": error_msg}
        
        # Check if file is a valid PDF by reading the first few bytes
        with open(pdf_path, 'rb') as f:
            header = f.read(5)
            print(f"File header: {header}")
            if header != b'%PDF-':
                error_msg = f"File is not a valid PDF (header: {header}): {pdf_path}"
                print(error_msg)
                
                # If it's an HTML file, try to extract text from it
                if header.startswith(b'<!DOC') or header.startswith(b'<html'):
                    print(f"File appears to be HTML, attempting to extract text")
                    with open(pdf_path, 'r', encoding='utf-8', errors='ignore') as html_file:
                        html_content = html_file.read()
                        # Very basic HTML text extraction
                        text = re.sub(r'<[^>]+>', ' ', html_content)
                        text = re.sub(r'\s+', ' ', text).strip()
                        if text:
                            print(f"Extracted {len(text)} characters from HTML")
                            # Try to extract title from HTML
                            title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE)
                            title = title_match.group(1) if title_match else os.path.basename(pdf_path)
                            
                            # Try to extract headings from HTML
                            headings = []
                            for i in range(1, 7):  # h1 through h6
                                heading_matches = re.findall(f'<h{i}[^>]*>(.*?)</h{i}>', html_content, re.IGNORECASE)
                                for match in heading_matches:
                                    headings.append(f"{'#' * i} {re.sub(r'<[^>]+>', '', match)}")
                            
                            return {
                                "title": title,
                                "headings": "\n".join(headings),
                                "content": text,
                                "total_chars": len(text)
                            }
                        else:
                            return {"error": "File appears to be HTML but no text could be extracted"}
                
                return {"error": error_msg}
        
        # Create PDF reader
        print("Creating PDF reader")
        with open(pdf_path, 'rb') as file:
            try:
                reader = pypdf.PdfReader(file)
                print(f"PDF reader created successfully")
                
                # Check if PDF is encrypted
                if reader.is_encrypted:
                    print("PDF is encrypted, attempting to decrypt")
                    try:
                        reader.decrypt('')  # Try empty password
                        print("PDF decrypted successfully")
                    except Exception as e:
                        error_msg = f"Failed to decrypt PDF: {str(e)}"
                        print(error_msg)
                        return {"error": error_msg}
                
                # Get number of pages
                num_pages = len(reader.pages)
                print(f"PDF has {num_pages} pages")
                
                if num_pages == 0:
                    error_msg = "PDF has 0 pages"
                    print(error_msg)
                    return {"error": error_msg}
                
                # Extract document title from metadata if available
                title = os.path.basename(pdf_path)  # Default to filename
                try:
                    if reader.metadata and hasattr(reader.metadata, 'title') and reader.metadata.title:
                        title = reader.metadata.title
                        print(f"Extracted title from metadata: {title}")
                except:
                    print("Could not extract title from metadata")
                
                # First pass: extract all text to identify structure
                all_text = ""
                for i in range(num_pages):
                    try:
                        page = reader.pages[i]
                        page_text = page.extract_text()
                        if page_text:
                            all_text += f"\n\n=== PAGE {i+1} ===\n\n{page_text}"
                    except Exception as e:
                        print(f"Error extracting text from page {i+1}: {str(e)}")
                
                # Improved heading pattern detection
                # Look for regulation patterns
                subchapter_pattern = re.compile(r'(?:Subchapter\s+([A-Z])[\.\s]|§\s*(\d+\.\d+))', re.IGNORECASE)
                section_pattern = re.compile(r'(?:§|Sec\.?|Section)\s*(\d+\.\d+(?:\(\d+\))?)', re.IGNORECASE)
                
                # Look for standard heading patterns
                heading_pattern = re.compile(r'(?:^|\n)([A-Z][A-Z\s\d]{5,60})(?:\n|$)')
                numbered_heading_pattern = re.compile(r'(?:^|\n)(\d+\.\s+[A-Z][A-Za-z\s]{5,60})(?:\n|$)')
                
                # Find all matches
                subchapters = []
                sections = []
                headings = []
                
                for match in subchapter_pattern.finditer(all_text):
                    subchapter = match.group()
                    if subchapter not in subchapters:
                        subchapters.append(subchapter)
                
                for match in section_pattern.finditer(all_text):
                    section = match.group()
                    if section not in sections:
                        sections.append(section)
                
                for match in heading_pattern.finditer(all_text):
                    heading = match.group(1).strip()
                    if heading and 5 < len(heading) < 100 and heading not in headings:
                        headings.append(heading)
                
                for match in numbered_heading_pattern.finditer(all_text):
                    heading = match.group(1).strip()
                    if heading and heading not in headings:
                        headings.append(heading)
                
                # Try to extract TOC if available by looking for patterns like "Table of Contents"
                toc_text = ""
                toc_pattern = re.compile(r'(?:Table\s+of\s+Contents|CONTENTS|TABLE\s+OF\s+CONTENTS).*?(?=\n\n\n|\Z)', re.DOTALL)
                toc_match = toc_pattern.search(all_text)
                if toc_match:
                    toc_text = toc_match.group(0)
                    print(f"Found table of contents: {len(toc_text)} characters")
                
                # Second pass: extract content page by page
                content_blocks = []
                
                for i in range(num_pages):
                    try:
                        page = reader.pages[i]
                        page_text = page.extract_text()
                        
                        if page_text:
                            # Add page number reference
                            content_blocks.append(f"[Page {i+1}]\n{page_text}")
                    except Exception as e:
                        error_msg = f"Error extracting text from page {i+1}: {str(e)}"
                        print(error_msg)
                        content_blocks.append(f"[Error on page {i+1}: {error_msg}]")
                
                # Create structured result
                chapters_text = "\n".join(subchapters + sections)
                headings_text = "\n".join(headings)
                if toc_text:
                    if chapters_text:
                        chapters_text = f"{toc_text}\n\n{chapters_text}"
                    else:
                        chapters_text = toc_text
                
                content_text = "\n\n".join(content_blocks)
                
                result = {
                    "title": title,
                    "chapters": chapters_text,
                    "headings": headings_text,
                    "content": content_text,
                    "total_chars": len(content_text)
                }
                
                print(f"Total characters extracted: {len(content_text)}")
                print(f"Identified {len(subchapters)} subchapters, {len(sections)} sections, and {len(headings)} headings")
                
                if len(content_text) == 0:
                    # Try alternative extraction method
                    print("No text extracted, trying alternative extraction method")
                    try:
                        from pdfminer.high_level import extract_text as pdfminer_extract_text
                        alt_text = pdfminer_extract_text(pdf_path)
                        if alt_text:
                            print(f"Alternative extraction successful: {len(alt_text)} characters")
                            result = {
                                "title": title,
                                "chapters": chapters_text,
                                "headings": headings_text,
                                "content": alt_text,
                                "total_chars": len(alt_text)
                            }
                            return result
                        else:
                            print("Alternative extraction also failed")
                    except Exception as e:
                        print(f"Alternative extraction error: {str(e)}")
                        # Continue with original result
                
                return result
                
            except Exception as e:
                error_msg = f"Error reading PDF: {str(e)}"
                print(error_msg)
                print(f"Traceback: {traceback.format_exc()}")
                return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error extracting text from PDF: {str(e)}"
        print(error_msg)
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": error_msg}

# Utility function to get file mimetype
def get_file_mimetype(filename: str) -> str:
    """
    Get the MIME type for a file based on its extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        # Default to binary if type can't be determined
        return 'application/octet-stream'
    return mime_type

# Utility function to get file type
def get_file_type(filename: str) -> str:
    """
    Get the file type (extension) from a filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        File type (e.g., PDF, DOCX, XLSX)
    """
    _, ext = os.path.splitext(filename)
    if ext:
        return ext[1:].upper()  # Remove the dot and convert to uppercase
    return "UNKNOWN"

# Service function to list documents for a user
async def list_documents(db: Session, current_user_id: int) -> List[Dict]:
    """
    List all documents for the current user.
    
    Args:
        db: Database session
        current_user_id: ID of the current user
        
    Returns:
        List of document records
    """
    print(f"[DEBUG] list_documents called for user ID: {current_user_id}")
    
    # Only return documents that belong to the current user
    documents = db.query(Document).filter(
        Document.uploaded_by == current_user_id,
        Document.is_deleted == False
    ).all()
    
    print(f"[DEBUG] Found {len(documents)} documents for user {current_user_id}")
    for doc in documents:
        print(f"[DEBUG]   Document: id={doc.id}, filename={doc.filename}, uploaded_by={doc.uploaded_by}")
    
    result = [
        {
            "id": doc.id,
            "filename": doc.filename,
            "filepath": doc.filepath,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "uploaded_at": doc.uploaded_at,
            "uploaded_by": doc.uploaded_by
        }
        for doc in documents
    ]
    
    print(f"[DEBUG] Returning {len(result)} document records")
    return result

# Service function to get a specific document for a user
async def get_document(doc_id: int, db: Session, current_user_id: int) -> Optional[Dict]:
    """
    Get a document by ID, ensuring it belongs to the current user.
    
    Args:
        doc_id: ID of the document to get
        db: Database session
        current_user_id: ID of the current user
        
    Returns:
        Document record or None if not found or not owned by the user
    """
    try:
        # Fetch document from DB
        db_doc = db.query(Document).filter(Document.id == doc_id).first()
        
        if not db_doc:
            print(f"Document with ID {doc_id} not found in DB.")
            return None

        # Access check: Ensure the user owns the document or it's a regulation
        is_regulation = db.query(Regulation).filter(Regulation.document_id == doc_id).first() is not None
        if not is_regulation:
            user_doc = db.query(UserDocument).filter(
                UserDocument.document_id == doc_id,
                UserDocument.user_id == current_user_id
            ).first()
            if not user_doc:
                print(f"User {current_user_id} does not have access to document {doc_id}")
                return None

        # Construct the full file path using the secure path function
        storage_path = get_storage_path()
        file_path = os.path.join(storage_path, db_doc.file_path)
        
        print(f"Attempting to retrieve document {doc_id} from path: {file_path}")

        if not os.path.exists(file_path):
            print(f"Error: File not found at path {file_path} for document ID {doc_id}")
            # Return metadata even if file is missing, but indicate error
            return {
                "id": db_doc.id,
                "filename": db_doc.filename,
                "file_type": db_doc.file_type,
                "upload_date": db_doc.upload_date.isoformat(),
                "title": db_doc.title,
                "chapters": db_doc.chapters,
                "headings": db_doc.headings,
                "content": "Error: Document file not found.",
                "is_regulation": is_regulation
            }

        # Extract text content (metadata only for now, content extraction removed)
        # For simplicity after removing indexing, we just return metadata
        # Content extraction could be added back here if needed for direct display
        # extracted_data = extract_text_from_pdf(file_path) # Example if needed
        
        return {
            "id": db_doc.id,
            "filename": db_doc.filename,
            "file_type": db_doc.file_type,
            "upload_date": db_doc.upload_date.isoformat(),
            "title": db_doc.title, 
            "chapters": db_doc.chapters,
            "headings": db_doc.headings,
            "content": "Content retrieval is currently disabled.", # Placeholder
            "is_regulation": is_regulation
        }

    except Exception as e:
        print(f"Error getting document {doc_id}: {str(e)}")
        print(traceback.format_exc())
        return None 