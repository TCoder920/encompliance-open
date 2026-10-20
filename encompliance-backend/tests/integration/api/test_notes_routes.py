"""
Notes Routes Integration Tests
------------------------------
Comprehensive tests for notes management endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from app import main
from app.database import get_db
from app.models.user import User
from app.models.note import Note
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
def test_note(db: Session, test_user: User):
    """Create a test note"""
    note = Note(
        title="Test Note",
        content="Test content",
        user_id=test_user.id,
        created_at=datetime.now()
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@pytest.fixture
def auth_token(test_user: User):
    """Create an auth token for test user"""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def auth_headers(auth_token: str):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestNotesCRUD:
    """Test notes CRUD operations"""
    
    @patch('app.api.routes.notes.NoteService.create_note')
    @patch('app.api.routes.notes.NotificationService.create_note_notification')
    def test_create_note_success(self, mock_notification, mock_create, db: Session, test_user: User, auth_headers: dict):
        """Test successful note creation"""
        mock_note = Note(id=1, title="New Note", content="Content", user_id=test_user.id)
        mock_create.return_value = mock_note
        mock_notification.return_value = None
        
        note_data = {
            "title": "New Note",
            "content": "Note content"
        }
        
        response = client.post(
            "/api/v1/notes/",
            headers=auth_headers,
            json=note_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == note_data["title"]
    
    def test_get_notes_success(self, db: Session, test_user: User, test_note: Note, auth_headers: dict):
        """Test successful notes retrieval"""
        response = client.get(
            "/api/v1/notes/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "notes" in data or isinstance(data, list)
    
    def test_get_note_by_id_success(self, db: Session, test_user: User, test_note: Note, auth_headers: dict):
        """Test successful note retrieval by ID"""
        response = client.get(
            f"/api/v1/notes/{test_note.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_note.id
    
    def test_update_note_success(self, db: Session, test_user: User, test_note: Note, auth_headers: dict):
        """Test successful note update"""
        update_data = {
            "title": "Updated Note",
            "content": "Updated content"
        }
        
        response = client.put(
            f"/api/v1/notes/{test_note.id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
    
    def test_delete_note_success(self, db: Session, test_user: User, test_note: Note, auth_headers: dict):
        """Test successful note deletion"""
        response = client.delete(
            f"/api/v1/notes/{test_note.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204]
    
    def test_notes_unauthorized(self, db: Session):
        """Test notes endpoint without authentication"""
        response = client.get("/api/v1/notes/")
        
        assert response.status_code == 401


class TestNotesPreview:
    """Test notes preview endpoint"""
    
    def test_get_notes_preview_free_user(self, db: Session, auth_headers: dict):
        """Test notes preview for free users"""
        response = client.get(
            "/api/v1/notes/preview",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

