"""
LLM Service Unit Tests
----------------------
Tests for LLM service functionality including:
- Thread management
- Assistant creation
- Response generation
- Context integration
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.orm import Session

from app.services.llm_service import (
    get_thread_id_for_conversation,
    get_llm_response
)
from app.models.user import User
from app.models.thread_map import ThreadMap


class TestThreadManagement:
    """Test thread management functions"""
    
    @pytest.mark.asyncio
    async def test_get_thread_id_existing(self, db: Session):
        """Test getting existing thread ID"""
        user = User(id=1, username="testuser")
        db.add(user)
        
        thread_map = ThreadMap(conversation_id=1, user_id=1, thread_id="thread_123")
        db.add(thread_map)
        db.commit()
        
        thread_id = await get_thread_id_for_conversation(1, 1, db)
        
        assert thread_id == "thread_123"
    
    @pytest.mark.asyncio
    async def test_get_thread_id_not_found(self, db: Session):
        """Test getting thread ID when not found"""
        user = User(id=1, username="testuser")
        db.add(user)
        db.commit()
        
        thread_id = await get_thread_id_for_conversation(999, 1, db)
        
        assert thread_id is None
    
    @pytest.mark.asyncio
    async def test_get_thread_id_different_user(self, db: Session):
        """Test getting thread ID for different user (should return None)"""
        user1 = User(id=1, username="user1")
        user2 = User(id=2, username="user2")
        db.add(user1)
        db.add(user2)
        
        thread_map = ThreadMap(conversation_id=1, user_id=1, thread_id="thread_123")
        db.add(thread_map)
        db.commit()
        
        # User 2 trying to access user 1's thread
        thread_id = await get_thread_id_for_conversation(1, 2, db)
        
        assert thread_id is None


class TestLLMResponse:
    """Test LLM response generation"""
    
    @pytest.mark.asyncio
    @patch('app.services.llm_service.settings.OPENAI_API_KEY', 'test_key')
    @patch('app.services.llm_service.get_user_assistant_id')
    @patch('app.services.llm_service.openai_client')
    async def test_get_llm_response_no_api_key(self, mock_client, mock_get_assistant, db: Session):
        """Test LLM response when API key is missing"""
        with patch('app.services.llm_service.settings.OPENAI_API_KEY', None):
            result = await get_llm_response(
                prompt="Test prompt",
                operation_type="daycare",
                db=db,
                current_user_id=1,
                stream=False
            )
            
            assert "error" in result.lower() or "not configured" in result.lower()
    
    @pytest.mark.asyncio
    @patch('app.services.llm_service.settings.OPENAI_API_KEY', 'test_key')
    @patch('app.services.llm_service.get_user_assistant_id')
    @patch('app.services.llm_service.ContextService.get_full_user_context')
    @patch('app.services.llm_service.openai_client')
    async def test_get_llm_response_with_context(
        self, 
        mock_client, 
        mock_context, 
        mock_get_assistant,
        db: Session
    ):
        """Test LLM response with user context"""
        user = User(id=1, username="testuser", subscription_status="pro", openai_assistant_id="asst_123")
        db.add(user)
        db.commit()
        
        mock_get_assistant.return_value = "asst_123"
        mock_context.return_value = "User has 3 calendar events"
        
        # Mock OpenAI response
        mock_thread = MagicMock()
        mock_run = MagicMock()
        mock_run.status = "completed"
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=MagicMock(value="Test response"))]
        mock_thread.messages.data = [mock_message]
        mock_client.beta.threads.runs.create_and_stream.return_value = [mock_run]
        mock_client.beta.threads.messages.list.return_value = mock_thread
        
        result = await get_llm_response(
            prompt="Test prompt",
            operation_type="daycare",
            db=db,
            current_user_id=1,
            stream=False
        )
        
        # Should process response
        assert result is not None
    
    @pytest.mark.asyncio
    @patch('app.services.llm_service.settings.OPENAI_API_KEY', 'test_key')
    @patch('app.services.llm_service.get_user_assistant_id')
    async def test_get_llm_response_no_assistant(self, mock_get_assistant, db: Session):
        """Test LLM response when user has no assistant"""
        user = User(id=1, username="testuser", subscription_status="pro")
        db.add(user)
        db.commit()
        
        mock_get_assistant.return_value = None
        
        result = await get_llm_response(
            prompt="Test prompt",
            operation_type="daycare",
            db=db,
            current_user_id=1,
            stream=False
        )
        
        assert "error" in result.lower() or "no assistant" in result.lower()

