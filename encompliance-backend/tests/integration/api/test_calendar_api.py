"""
Description: Integration tests for Calendar API endpoints.
Purpose: Tests the complete functionality of the Calendar API, including paywall
enforcement, CRUD operations, and AI scheduling. Ensures that Free tier users receive
appropriate 403 Forbidden responses when attempting to access premium features while
Pro and Enterprise users can access all calendar functionality.
"""

"""
Integration tests for the calendar API endpoints
Tests the calendar feature paywall and endpoint functionality
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy.orm import Session
from app.models.user import User
from app.auth.utils import create_access_token
from app.database import get_db
from typing import Dict

# Client for testing HTTP requests
client = TestClient(app)

# Create test users with different subscription tiers
@pytest.fixture
def free_user_token(db: Session) -> str:
    """Create a test free user and return a valid JWT token"""
    # Check if user already exists
    user = db.query(User).filter(User.email == "test-free@example.com").first()
    if not user:
        user = User(
            email="test-free@example.com",
            username="test-free-user",
            hashed_password="hashed_password",  # Don't need real password for tests
            is_active=True,
            subscription_status="free"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create token
    return create_access_token(data={"sub": user.username})

@pytest.fixture
def pro_user_token(db: Session) -> str:
    """Create a test pro user and return a valid JWT token"""
    # Check if user already exists
    user = db.query(User).filter(User.email == "test-pro@example.com").first()
    if not user:
        user = User(
            email="test-pro@example.com",
            username="test-pro-user",
            hashed_password="hashed_password",  # Don't need real password for tests
            is_active=True,
            subscription_status="pro"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create token
    return create_access_token(data={"sub": user.username})

@pytest.fixture
def enterprise_user_token(db: Session) -> str:
    """Create a test enterprise user and return a valid JWT token"""
    # Check if user already exists
    user = db.query(User).filter(User.email == "test-enterprise@example.com").first()
    if not user:
        user = User(
            email="test-enterprise@example.com",
            username="test-enterprise-user",
            hashed_password="hashed_password",  # Don't need real password for tests
            is_active=True,
            subscription_status="enterprise"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create token
    return create_access_token(data={"sub": user.username})

# Tests for GET /calendar/events endpoint
def test_get_events_free_user(free_user_token: str):
    """Test that free users cannot access calendar events"""
    response = client.get(
        "/api/calendar/events",
        headers={"Authorization": f"Bearer {free_user_token}"}
    )
    
    # Free users now receive preview data instead of 403
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_get_events_pro_user(pro_user_token: str):
    """Test that pro users can access calendar events"""
    response = client.get(
        "/api/calendar/events",
        headers={"Authorization": f"Bearer {pro_user_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_events_enterprise_user(enterprise_user_token: str):
    """Test that enterprise users can access calendar events"""
    response = client.get(
        "/api/calendar/events",
        headers={"Authorization": f"Bearer {enterprise_user_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Tests for POST /calendar/events endpoint
def test_create_event_free_user(free_user_token: str):
    """Test that free users cannot create calendar events"""
    event_data = {
        "title": "Test Event",
        "start": "2023-01-01T10:00:00",
        "end": "2023-01-01T11:00:00",
        "description": "Test Description",
        "location": "Test Location",
        "allDay": False
    }
    
    response = client.post(
        "/api/calendar/events",
        headers={"Authorization": f"Bearer {free_user_token}"},
        json=event_data
    )
    
    # Should return 403 Forbidden
    assert response.status_code == 403
    assert "requires a Pro or Enterprise subscription" in response.json()["detail"]

def test_create_event_pro_user(pro_user_token: str):
    """Test that pro users can create calendar events"""
    event_data = {
        "title": "Pro Test Event",
        "start": "2023-01-01T10:00:00",
        "end": "2023-01-01T11:00:00",
        "description": "Pro Test Description",
        "location": "Pro Test Location",
        "allDay": False
    }
    
    response = client.post(
        "/api/calendar/events",
        headers={"Authorization": f"Bearer {pro_user_token}"},
        json=event_data
    )
    
    # Should return 201 Created
    assert response.status_code == 201
    assert response.json()["title"] == "Pro Test Event"
    assert "id" in response.json()

# Tests for AI scheduling endpoint
def test_ai_schedule_free_user(free_user_token: str):
    """Test that free users cannot access AI scheduling"""
    request_data = {
        "prompt": "Schedule a meeting tomorrow at 10am"
    }
    
    response = client.post(
        "/api/calendar/ai-schedule",
        headers={"Authorization": f"Bearer {free_user_token}"},
        json=request_data
    )
    
    # Should return 403 Forbidden
    assert response.status_code == 403
    assert "requires a Pro or Enterprise subscription" in response.json()["detail"]

def test_ai_schedule_pro_user(pro_user_token: str, monkeypatch):
    """Test that pro users can access AI scheduling (with mocked AI response)"""
    # Mock the OpenAI response
    class MockResponse:
        class MockChoice:
            class MockMessage:
                content = """
                {
                    "title": "Meeting",
                    "start": "2023-01-02T10:00:00",
                    "end": "2023-01-02T11:00:00",
                    "description": "Scheduled meeting",
                    "location": "Office",
                    "allDay": false
                }
                """
            
            def __init__(self):
                self.message = self.MockMessage()
        
        def __init__(self):
            self.choices = [self.MockChoice()]

    # Apply the monkeypatch
    # Note: This is a simplified mock - in a real test we would need to handle the async nature of the OpenAI call
    async def mock_create(*args, **kwargs):
        return MockResponse()
    
    # Apply the monkeypatch to the module
    monkeypatch.setattr("app.api.routes.calendar.openai_client.chat.completions.create", mock_create)
    
    request_data = {
        "prompt": "Schedule a meeting tomorrow at 10am"
    }
    
    response = client.post(
        "/api/calendar/ai-schedule",
        headers={"Authorization": f"Bearer {pro_user_token}"},
        json=request_data
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    assert "event" in response.json()
    assert response.json()["event"]["title"] == "Meeting" 
