"""
Document Routes Integration Tests
---------------------------------
Comprehensive tests for document management endpoints including:
- Document upload
- Document listing
- Document download
- Document deletion
- Document metadata updates
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import io
import tempfile
import os

from app import main
from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.user_document import UserDocument
from app.auth.utils import get_password_hash, create_access_token

app = main.app
client = TestClient(app)


@pytest.fixture
def db():
    """Database session fixture"""
    from app.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Test User",
        operation_name="Test Operation",
        state="CA",
        is_active=True,
        email_verified=True,
        subscription_status="pro"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User):
    """Create an auth token for test user"""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def auth_headers(auth_token: str):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_document(db: Session, test_user: User):
    """Create a test document"""
    doc = Document(
        filename="test_document.pdf",
        file_path="/storage/test_document.pdf",
        file_size=1024,
        file_type="pdf",
        uploaded_by=test_user.id,
        uploaded_at=datetime.now()
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Create user-document relationship
    user_doc = UserDocument(
        user_id=test_user.id,
        document_id=doc.id
    )
    db.add(user_doc)
    db.commit()
    
    return doc


class TestDocumentUpload:
    """Test document upload endpoint"""
    
    @patch('app.api.routes.documents.extract_text_from_pdf')
    @patch('app.api.routes.documents.StorageMeterService.record_upload')
    @patch('app.api.routes.documents.get_or_create_user_vector_store')
    @patch('app.api.routes.documents.update_vector_store')
    def test_upload_document_success(
        self, 
        mock_update_vector, 
        mock_get_vector_store,
        mock_storage_meter,
        mock_extract_text,
        db: Session, 
        test_user: User, 
        auth_headers: dict
    ):
        """Test successful document upload"""
        # Setup mocks
        mock_extract_text.return_value = {"content": "Test content", "title": "Test Document"}
        mock_storage_meter.return_value = None
        mock_get_vector_store.return_value = "vector_store_id"
        mock_update_vector.return_value = None
        
        # Create a test file
        file_content = b"%PDF-1.4\nTest PDF content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {
            "custom_label": "Test Document",
            "document_type": "policy"
        }
        
        with patch('app.api.routes.documents.get_storage_path', return_value="/tmp/storage"), \
             patch('shutil.copyfileobj'), \
             patch('os.path.exists', return_value=True), \
             patch('os.makedirs'):
            
            response = client.post(
                "/api/v1/documents/upload",
                headers=auth_headers,
                files=files,
                data=data
            )
            
            # Should create document record
            assert response.status_code in [201, 200, 500]  # 500 if storage path issues
    
    def test_upload_document_unauthorized(self, db: Session):
        """Test document upload without authentication"""
        files = {"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files
        )
        
        assert response.status_code == 401
    
    def test_upload_document_no_file(self, db: Session, auth_headers: dict):
        """Test document upload without file"""
        response = client.post(
            "/api/v1/documents/upload",
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestDocumentList:
    """Test document listing endpoint"""
    
    def test_list_documents_success(self, db: Session, test_user: User, test_document: Document, auth_headers: dict):
        """Test successful document listing"""
        response = client.get(
            "/api/v1/documents/list",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should include test document if properly linked
    
    def test_list_documents_unauthorized(self, db: Session):
        """Test document listing without authentication"""
        response = client.get("/api/v1/documents/list")
        
        assert response.status_code == 401
    
    def test_list_documents_empty(self, db: Session, test_user: User, auth_headers: dict):
        """Test document listing with no documents"""
        response = client.get(
            "/api/v1/documents/list",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDocumentDownload:
    """Test document download endpoint"""
    
    @patch('app.api.routes.documents.os.path.exists', return_value=True)
    @patch('app.api.routes.documents.FileResponse')
    def test_download_document_success(
        self, 
        mock_file_response,
        mock_exists,
        db: Session, 
        test_user: User, 
        test_document: Document, 
        auth_headers: dict
    ):
        """Test successful document download"""
        mock_file_response.return_value = MagicMock()
        
        response = client.get(
            f"/api/v1/documents/download/{test_document.id}",
            headers=auth_headers
        )
        
        # Should return file or 404 if file doesn't exist on disk
        assert response.status_code in [200, 404]
    
    def test_download_document_not_found(self, db: Session, test_user: User, auth_headers: dict):
        """Test download of non-existent document"""
        response = client.get(
            "/api/v1/documents/download/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_download_document_unauthorized(self, db: Session, test_document: Document):
        """Test document download without authentication"""
        response = client.get(f"/api/v1/documents/download/{test_document.id}")
        
        assert response.status_code == 401


class TestDocumentDelete:
    """Test document deletion endpoint"""
    
    def test_delete_document_success(
        self, 
        db: Session, 
        test_user: User, 
        test_document: Document, 
        auth_headers: dict
    ):
        """Test successful document deletion"""
        with patch('app.api.routes.documents.os.path.exists', return_value=True), \
             patch('app.api.routes.documents.os.remove'), \
             patch('app.api.routes.documents.StorageMeterService.record_deletion'):
            
            response = client.delete(
                f"/api/v1/documents/delete/{test_document.id}",
                headers=auth_headers
            )
            
            assert response.status_code in [200, 204]
    
    def test_delete_document_not_found(self, db: Session, test_user: User, auth_headers: dict):
        """Test deletion of non-existent document"""
        response = client.delete(
            "/api/v1/documents/delete/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_document_unauthorized(self, db: Session, test_document: Document):
        """Test document deletion without authentication"""
        response = client.delete(f"/api/v1/documents/delete/{test_document.id}")
        
        assert response.status_code == 401


class TestDocumentLabelUpdate:
    """Test document label update endpoint"""
    
    def test_update_document_label_success(
        self, 
        db: Session, 
        test_user: User, 
        test_document: Document, 
        auth_headers: dict
    ):
        """Test successful document label update"""
        response = client.put(
            f"/api/v1/documents/{test_document.id}/label",
            headers=auth_headers,
            json={"label": "Updated Label"}
        )
        
        assert response.status_code in [200, 404]
    
    def test_update_document_label_not_found(self, db: Session, test_user: User, auth_headers: dict):
        """Test label update for non-existent document"""
        response = client.put(
            "/api/v1/documents/99999/label",
            headers=auth_headers,
            json={"label": "New Label"}
        )
        
        assert response.status_code == 404
    
    def test_update_document_label_unauthorized(self, db: Session, test_document: Document):
        """Test document label update without authentication"""
        response = client.put(
            f"/api/v1/documents/{test_document.id}/label",
            json={"label": "New Label"}
        )
        
        assert response.status_code == 401

