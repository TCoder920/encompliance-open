"""
Policy Routes Integration Tests
-------------------------------
Comprehensive tests for policy management endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import patch, MagicMock

from app import main
from app.database import get_db
from app.models.user import User, UserRole
from app.models.policy import Policy
from app.models.policy import PolicyStatus
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
def test_policy(db: Session, test_user: User):
    """Create a test policy"""
    from datetime import datetime
    policy = Policy(
        title="Test Policy",
        description="Test policy content",
        category="compliance",
        status=PolicyStatus.ACTIVE.value,
        created_by=test_user.id,
        facility_administrator_id=test_user.id,
        effective_date=datetime.now()
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@pytest.fixture
def auth_token(test_user: User):
    """Create an auth token for test user"""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def auth_headers(auth_token: str):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestPolicyManagement:
    """Test policy management endpoints"""
    
    def test_get_policies_success(self, db: Session, test_user: User, test_policy: Policy, auth_headers: dict):
        """Test successful policies retrieval"""
        response = client.get(
            "/api/v1/policy/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_policy_by_id_success(self, db: Session, test_user: User, test_policy: Policy, auth_headers: dict):
        """Test successful policy retrieval by ID"""
        response = client.get(
            f"/api/v1/policy/{test_policy.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_policy.id
    
    def test_create_policy_success(self, db: Session, test_user: User, auth_headers: dict):
        """Test successful policy creation"""
        policy_data = {
            "title": "New Policy",
            "content": "Policy content",
            "category": "safety",
            "status": "active"
        }
        
        response = client.post(
            "/api/v1/policy/",
            headers=auth_headers,
            json=policy_data
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["title"] == policy_data["title"]
    
    def test_update_policy_success(self, db: Session, test_user: User, test_policy: Policy, auth_headers: dict):
        """Test successful policy update"""
        update_data = {
            "title": "Updated Policy",
            "content": "Updated content"
        }
        
        response = client.put(
            f"/api/v1/policy/{test_policy.id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
    
    def test_delete_policy_success(self, db: Session, test_user: User, test_policy: Policy, auth_headers: dict):
        """Test successful policy deletion"""
        response = client.delete(
            f"/api/v1/policy/{test_policy.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204]
    
    def test_get_dashboard_success(self, db: Session, test_user: User, auth_headers: dict):
        """Test successful policy dashboard retrieval"""
        response = client.get(
            "/api/v1/policy/dashboard",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_policies_unauthorized(self, db: Session):
        """Test policies endpoint without authentication"""
        response = client.get("/api/v1/policy/")
        
        assert response.status_code == 401

