"""
Notifications Routes Integration Tests
--------------------------------------
Comprehensive tests for notification endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import patch, MagicMock

from app import main
from app.database import get_db
from app.models.user import User
from app.models.notification import Notification, NotificationType
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
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_notification(db: Session, test_user: User):
    """Create a test notification"""
    notification = Notification(
        user_id=test_user.id,
        title="Test Notification",
        message="Test message",
        notification_type=NotificationType.INFO,
        created_at=datetime.now()
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@pytest.fixture
def auth_token(test_user: User):
    """Create an auth token for test user"""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def auth_headers(auth_token: str):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestNotifications:
    """Test notification endpoints"""
    
    def test_get_notifications_success(self, db: Session, test_user: User, test_notification: Notification, auth_headers: dict):
        """Test successful notifications retrieval"""
        response = client.get(
            "/api/v1/notifications/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data or isinstance(data, list)
    
    def test_get_notification_by_id_success(self, db: Session, test_user: User, test_notification: Notification, auth_headers: dict):
        """Test successful notification retrieval by ID"""
        response = client.get(
            f"/api/v1/notifications/{test_notification.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_notification.id
    
    def test_mark_notification_as_read(self, db: Session, test_user: User, test_notification: Notification, auth_headers: dict):
        """Test marking notification as read"""
        response = client.post(
            f"/api/v1/notifications/{test_notification.id}/mark-as-read",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_mark_all_as_read(self, db: Session, test_user: User, auth_headers: dict):
        """Test marking all notifications as read"""
        response = client.post(
            "/api/v1/notifications/mark-all-as-read",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_get_unread_count(self, db: Session, test_user: User, auth_headers: dict):
        """Test getting unread notification count"""
        response = client.get(
            "/api/v1/notifications/unread-count",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, int)
    
    def test_delete_notification(self, db: Session, test_user: User, test_notification: Notification, auth_headers: dict):
        """Test notification deletion"""
        response = client.delete(
            f"/api/v1/notifications/{test_notification.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204]
    
    def test_notifications_unauthorized(self, db: Session):
        """Test notifications endpoint without authentication"""
        response = client.get("/api/v1/notifications/")
        
        assert response.status_code == 401

