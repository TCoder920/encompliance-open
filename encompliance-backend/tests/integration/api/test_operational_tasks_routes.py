"""
Operational Tasks Routes Integration Tests
------------------------------------------
Comprehensive tests for operational task management endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import main
from app.database import get_db
from app.models.user import User, UserRole
from app.models.operational_task import OperationalTask, TaskStatus, TaskPriority
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
        user_role=UserRole.FACILITY_ADMIN
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_task(db: Session, test_user: User):
    """Create a test operational task"""
    task = OperationalTask(
        title="Test Task",
        description="Test description",
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        created_by=test_user.id,
        facility_id=test_user.facility_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture
def auth_token(test_user: User):
    """Create an auth token for test user"""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def auth_headers(auth_token: str):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestOperationalTasks:
    """Test operational task endpoints"""
    
    def test_get_tasks_success(self, db: Session, test_user: User, test_task: OperationalTask, auth_headers: dict):
        """Test successful tasks retrieval"""
        response = client.get(
            "/api/v1/operational-tasks/tasks",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_task_by_id_success(self, db: Session, test_user: User, test_task: OperationalTask, auth_headers: dict):
        """Test successful task retrieval by ID"""
        response = client.get(
            f"/api/v1/operational-tasks/tasks/{test_task.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_task.id
    
    def test_create_task_success(self, db: Session, test_user: User, auth_headers: dict):
        """Test successful task creation"""
        task_data = {
            "title": "New Task",
            "description": "Task description",
            "priority": "medium",
            "status": "pending"
        }
        
        response = client.post(
            "/api/v1/operational-tasks/tasks",
            headers=auth_headers,
            json=task_data
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["title"] == task_data["title"]
    
    def test_update_task_success(self, db: Session, test_user: User, test_task: OperationalTask, auth_headers: dict):
        """Test successful task update"""
        update_data = {
            "title": "Updated Task",
            "status": "in_progress"
        }
        
        response = client.put(
            f"/api/v1/operational-tasks/tasks/{test_task.id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
    
    def test_delete_task_success(self, db: Session, test_user: User, test_task: OperationalTask, auth_headers: dict):
        """Test successful task deletion"""
        response = client.delete(
            f"/api/v1/operational-tasks/tasks/{test_task.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204]
    
    def test_get_dashboard_success(self, db: Session, test_user: User, auth_headers: dict):
        """Test successful dashboard retrieval"""
        response = client.get(
            "/api/v1/operational-tasks/dashboard",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Dashboard structure may vary
    
    def test_tasks_unauthorized(self, db: Session):
        """Test tasks endpoint without authentication"""
        response = client.get("/api/v1/operational-tasks/tasks")
        
        assert response.status_code == 401

