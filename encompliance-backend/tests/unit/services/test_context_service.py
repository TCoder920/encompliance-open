"""
Context Service Unit Tests
-------------------------
Tests for context service methods
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.services.context_service import ContextService
from app.models.user import User


class TestContextService:
    """Test ContextService methods"""
    
    @pytest.mark.asyncio
    async def test_get_user_calendar_events_success(self, db: Session):
        """Test successful calendar events retrieval"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            email=f"test_{unique_id}@example.com",
            username=f"testuser_{unique_id}",
            subscription_status="pro"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        events_storage = {
            "event1": {
                "id": 1,
                "user_id": user.id,
                "title": "Test Event",
                "start": datetime.now().isoformat(),
                "end": (datetime.now() + timedelta(hours=1)).isoformat(),
                "description": "Test description"
            }
        }
        
        result = await ContextService.get_user_calendar_events(
            user_id=user.id,
            user_subscription_status="pro",
            db=db,
            calendar_events_storage=events_storage
        )
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_user_calendar_events_free_user(self, db: Session):
        """Test calendar events for free user (should return empty)"""
        result = await ContextService.get_user_calendar_events(
            user_id=1,
            user_subscription_status="free",
            db=db
        )
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_user_notes_success(self, db: Session):
        """Test successful notes retrieval"""
        with patch('app.services.context_service.NoteService.get_notes') as mock_get_notes:
            mock_get_notes.return_value = {
                "notes": [
                    MagicMock(title="Note 1", content="Content 1"),
                    MagicMock(title="Note 2", content="Content 2")
                ],
                "total": 2
            }
            
            result = await ContextService.get_user_notes(
                user_id=1,
                user_subscription_status="pro",
                db=db
            )
            
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_full_user_context_success(self, db: Session):
        """Test successful full user context retrieval"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            email=f"test_{unique_id}@example.com",
            username=f"testuser_{unique_id}",
            subscription_status="pro"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        with patch('app.services.context_service.ContextService.get_user_calendar_events') as mock_calendar, \
             patch('app.services.context_service.ContextService.get_user_notes') as mock_notes, \
             patch('app.services.context_service.TrainingContextService.get_user_training_context') as mock_training:
            
            mock_calendar.return_value = []
            mock_notes.return_value = []
            mock_training.return_value = ""
            
            result = await ContextService.get_full_user_context(
                db=db,
                user_id=user.id,
                user_subscription_status="pro"
            )
            
            assert isinstance(result, str)
    
    def test_format_context_for_ai(self):
        """Test context formatting for AI"""
        events = [
            {"title": "Event 1", "start": "2024-01-01T10:00:00", "description": "Desc 1"},
            {"title": "Event 2", "start": "2024-01-02T11:00:00", "description": "Desc 2"}
        ]
        
        notes = [
            MagicMock(title="Note 1", content="Content 1"),
            MagicMock(title="Note 2", content="Content 2")
        ]
        
        result = ContextService.format_context_for_ai(events, notes)
        
        assert isinstance(result, str)
        assert "Event 1" in result or "Note 1" in result
