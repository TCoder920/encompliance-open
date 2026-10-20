"""
Note Service Unit Tests
-----------------------
Tests for note service business logic
"""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.note_service import NoteService
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate


class TestNoteService:
    """Test NoteService methods"""
    
    @pytest.mark.asyncio
    async def test_create_note_success(self, db: Session):
        """Test successful note creation"""
        note_data = NoteCreate(
            title="Test Note",
            content="Test content",
            is_pinned=False,
            is_archived=False
        )
        
        note = await NoteService.create_note(db, note_data, user_id=1)
        
        assert note.title == note_data.title
        assert note.content == note_data.content
        assert note.user_id == 1
    
    @pytest.mark.asyncio
    async def test_get_notes_success(self, db: Session):
        """Test successful notes retrieval"""
        # Create test notes
        note1 = Note(title="Note 1", content="Content 1", user_id=1)
        note2 = Note(title="Note 2", content="Content 2", user_id=1)
        db.add(note1)
        db.add(note2)
        db.commit()
        
        result = await NoteService.get_notes(db, user_id=1)
        
        assert "notes" in result
        assert "total" in result
        assert result["total"] >= 2
    
    @pytest.mark.asyncio
    async def test_get_notes_with_search(self, db: Session):
        """Test notes retrieval with search"""
        note = Note(title="Searchable Note", content="Search content", user_id=1)
        db.add(note)
        db.commit()
        
        result = await NoteService.get_notes(db, user_id=1, search="Searchable")
        
        assert "notes" in result
        assert len(result["notes"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_note_by_id_success(self, db: Session):
        """Test successful note retrieval by ID"""
        note = Note(title="Test Note", content="Content", user_id=1)
        db.add(note)
        db.commit()
        db.refresh(note)
        
        result = await NoteService.get_note(db, note.id, user_id=1)
        
        assert result is not None
        assert result.id == note.id
    
    @pytest.mark.asyncio
    async def test_get_note_not_found(self, db: Session):
        """Test note retrieval when not found"""
        result = await NoteService.get_note(db, note_id=99999, user_id=1)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_note_success(self, db: Session):
        """Test successful note update"""
        note = Note(title="Original", content="Original content", user_id=1)
        db.add(note)
        db.commit()
        db.refresh(note)
        
        update_data = NoteUpdate(title="Updated", content="Updated content")
        
        result = await NoteService.update_note(db, note.id, update_data, user_id=1)
        
        assert result is not None
        assert result.title == "Updated"
    
    @pytest.mark.asyncio
    async def test_delete_note_success(self, db: Session):
        """Test successful note deletion"""
        note = Note(title="To Delete", content="Content", user_id=1)
        db.add(note)
        db.commit()
        db.refresh(note)
        
        result = await NoteService.delete_note(db, note.id, user_id=1)
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_archive_note_success(self, db: Session):
        """Test successful note archiving"""
        note = Note(title="To Archive", content="Content", user_id=1, is_archived=False)
        db.add(note)
        db.commit()
        db.refresh(note)
        
        result = await NoteService.archive_note(db, note.id, user_id=1)
        
        assert result is not None
        assert result.is_archived == True
    
    @pytest.mark.asyncio
    async def test_pin_note_success(self, db: Session):
        """Test successful note pinning"""
        note = Note(title="To Pin", content="Content", user_id=1, is_pinned=False)
        db.add(note)
        db.commit()
        db.refresh(note)
        
        result = await NoteService.pin_note(db, note.id, user_id=1)
        
        assert result is not None
        assert result.is_pinned == True

