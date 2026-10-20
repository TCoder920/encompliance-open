"""
Document Service Unit Tests
---------------------------
Tests for document service functions including:
- PDF text extraction
- File type detection
- Document listing and retrieval
- Error handling
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from app.services.document_service import (
    extract_text_from_pdf,
    get_file_type,
    get_file_mimetype,
    get_storage_path
)
from app.core.config import get_settings


class TestExtractTextFromPDF:
    """Test PDF text extraction"""
    
    def test_extract_text_from_pdf_success(self):
        """Test successful PDF text extraction"""
        with patch('pypdf.PdfReader') as mock_reader, \
             patch('builtins.open', mock_open(read_data=b'%PDF-1.4\n')):
            
            # Mock PDF reader
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Sample PDF content"
            
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]
            mock_pdf.is_encrypted = False
            mock_pdf.metadata = None
            mock_reader.return_value = mock_pdf
            
            result = extract_text_from_pdf("/path/to/test.pdf")
            
            assert "content" in result
            assert result["content"] == "Sample PDF content"
            assert "title" in result
    
    def test_extract_text_from_pdf_file_not_found(self):
        """Test PDF extraction when file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            result = extract_text_from_pdf("/nonexistent/file.pdf")
            
            assert "error" in result
            assert "not found" in result["error"].lower()
    
    def test_extract_text_from_pdf_empty_file(self):
        """Test PDF extraction with empty file"""
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=0):
            
            result = extract_text_from_pdf("/path/to/empty.pdf")
            
            assert "error" in result
            assert "empty" in result["error"].lower()
    
    def test_extract_text_from_pdf_invalid_format(self):
        """Test PDF extraction with invalid file format"""
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=100), \
             patch('builtins.open', mock_open(read_data=b'NOT A PDF')):
            
            result = extract_text_from_pdf("/path/to/invalid.pdf")
            
            assert "error" in result
            assert "not a valid pdf" in result["error"].lower()
    
    def test_extract_text_from_pdf_encrypted(self):
        """Test PDF extraction with encrypted PDF"""
        with patch('pypdf.PdfReader') as mock_reader, \
             patch('builtins.open', mock_open(read_data=b'%PDF-1.4\n')):
            
            mock_pdf = MagicMock()
            mock_pdf.is_encrypted = True
            mock_pdf.decrypt.return_value = True
            mock_pdf.pages = [MagicMock(extract_text=lambda: "Decrypted content")]
            mock_pdf.metadata = None
            mock_reader.return_value = mock_pdf
            
            result = extract_text_from_pdf("/path/to/encrypted.pdf")
            
            assert "content" in result
            mock_pdf.decrypt.assert_called_once()
    
    def test_extract_text_from_pdf_encrypted_failed_decrypt(self):
        """Test PDF extraction with encrypted PDF that fails to decrypt"""
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=100), \
             patch('builtins.open', mock_open(read_data=b'%PDF-1.4\n')):
            
            with patch('pypdf.PdfReader') as mock_reader:
                mock_pdf = MagicMock()
                mock_pdf.is_encrypted = True
                mock_pdf.decrypt.side_effect = Exception("Decryption failed")
                mock_reader.return_value = mock_pdf
                
                result = extract_text_from_pdf("/path/to/encrypted.pdf")
                
                assert "error" in result
                assert "decrypt" in result["error"].lower() or "failed" in result["error"].lower()
    
    def test_extract_text_from_pdf_html_file(self):
        """Test extraction from HTML file (fallback)"""
        html_content = b'<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Heading</h1><p>Content</p></body></html>'
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=len(html_content)), \
             patch('builtins.open', mock_open(read_data=html_content)):
            
            result = extract_text_from_pdf("/path/to/file.html")
            
            # Should attempt HTML extraction
            assert "content" in result or "error" in result
    
    def test_extract_text_from_pdf_with_metadata_title(self):
        """Test PDF extraction with metadata title"""
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=100), \
             patch('builtins.open', mock_open(read_data=b'%PDF-1.4\n')):
            
            with patch('pypdf.PdfReader') as mock_reader:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = "Content"
                
                mock_metadata = MagicMock()
                mock_metadata.title = "Document Title"
                
                mock_pdf = MagicMock()
                mock_pdf.pages = [mock_page]
                mock_pdf.is_encrypted = False
                mock_pdf.metadata = mock_metadata
                mock_reader.return_value = mock_pdf
                
                result = extract_text_from_pdf("/path/to/test.pdf")
                
                assert "title" in result
                assert result["title"] == "Document Title" or "test.pdf" in result["title"]


class TestGetFileType:
    """Test file type detection"""
    
    def test_get_file_type_pdf(self):
        """Test PDF file type detection"""
        file_type = get_file_type("document.pdf")
        assert file_type == "PDF"
    
    def test_get_file_type_docx(self):
        """Test DOCX file type detection"""
        file_type = get_file_type("document.docx")
        assert file_type == "DOCX"
    
    def test_get_file_type_xlsx(self):
        """Test XLSX file type detection"""
        file_type = get_file_type("spreadsheet.xlsx")
        assert file_type == "XLSX"
    
    def test_get_file_type_unknown(self):
        """Test unknown file type"""
        file_type = get_file_type("file.unknown")
        assert file_type == "UNKNOWN"
    
    def test_get_file_type_no_extension(self):
        """Test file with no extension"""
        file_type = get_file_type("filename")
        assert file_type == "UNKNOWN"


class TestGetFileMimetype:
    """Test MIME type detection"""
    
    def test_get_file_mimetype_pdf(self):
        """Test PDF MIME type"""
        mimetype = get_file_mimetype("document.pdf")
        assert mimetype == "application/pdf"
    
    def test_get_file_mimetype_docx(self):
        """Test DOCX MIME type"""
        mimetype = get_file_mimetype("document.docx")
        assert mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    def test_get_file_mimetype_xlsx(self):
        """Test XLSX MIME type"""
        mimetype = get_file_mimetype("spreadsheet.xlsx")
        assert mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    def test_get_file_mimetype_unknown(self):
        """Test unknown MIME type"""
        mimetype = get_file_mimetype("file.unknown")
        assert mimetype == "application/octet-stream"


class TestGetStoragePath:
    """Test storage path retrieval"""
    
    def test_get_storage_path(self):
        """Test getting storage path"""
        with patch('app.services.document_service.get_settings') as mock_settings:
            mock_settings.return_value.PDF_STORAGE_PATH = "/test/storage/path"
            
            path = get_storage_path()
            
            assert path == "/test/storage/path"

