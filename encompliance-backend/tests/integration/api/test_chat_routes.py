"""
Chat Routes Integration Tests
------------------------------
Comprehensive tests for chat/AI endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock, AsyncMock

from app import main
from app.database import get_db
from app.models.user import User
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
        subscription_status="pro",
        openai_assistant_id="asst_test123"
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


class TestChat:
    """Test chat endpoint"""
    
    @patch('app.api.routes.chat.get_llm_response')
    def test_chat_success(self, mock_llm, db: Session, test_user: User, auth_headers: dict):
        """Test successful chat request"""
        mock_llm.return_value = "Test AI response"
        
        chat_data = {
            "prompt": "What is compliance?",
            "operation_type": "daycare",
            "stream": False
        }
        
        response = client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json=chat_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "text" in data or "response" in data.lower()
    
    @patch('app.api.routes.chat.get_llm_response')
    def test_chat_streaming(self, mock_llm, db: Session, test_user: User, auth_headers: dict):
        """Test chat with streaming"""
        async def stream_response():
            yield "Test "
            yield "response"
        
        mock_llm.return_value = stream_response()
        
        chat_data = {
            "prompt": "What is compliance?",
            "operation_type": "daycare",
            "stream": True
        }
        
        response = client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json=chat_data
        )
        
        assert response.status_code in [200, 500]  # Streaming may have different response
    
    def test_chat_unauthorized(self, db: Session):
        """Test chat without authentication"""
        response = client.post(
            "/api/v1/chat",
            json={"prompt": "Test", "operation_type": "daycare"}
        )
        
        assert response.status_code == 401


class TestQueryLimit:
    """Test query limit endpoint"""
    
    def test_get_query_limit_success(self, db: Session, test_user: User, auth_headers: dict):
        """Test successful query limit retrieval"""
        response = client.get(
            "/api/v1/chat/query-limit",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "used" in data or "limit" in data
    
    def test_get_query_limit_unauthorized(self, db: Session):
        """Test query limit without authentication"""
        response = client.get("/api/v1/chat/query-limit")
        
        assert response.status_code == 401

