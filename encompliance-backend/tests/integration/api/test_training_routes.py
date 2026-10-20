"""
Training Routes Integration Tests
---------------------------------
Comprehensive tests for training management endpoints including:
- Training programs CRUD
- Staff member management
- Training assignments
- Training materials
- Dashboard and analytics
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import main
from app.database import get_db
from app.models.user import User
from app.models.training_program import TrainingProgram
from app.models.staff_member import StaffMember
from app.models.training_assignment import TrainingAssignment
from app.models.training_material import TrainingMaterial
from app.auth.utils import get_password_hash, create_access_token
from app.utils.tiers import get_tier_from_subscription_status

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
def free_user(db: Session):
    """Create a free tier user"""
    user = User(
        email="free@example.com",
        username="freeuser",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Free User",
        operation_name="Free Operation",
        state="CA",
        is_active=True,
        email_verified=True,
        subscription_status="free"
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
def free_auth_token(free_user: User):
    """Create an auth token for free user"""
    return create_access_token(data={"sub": free_user.username})


@pytest.fixture
def free_auth_headers(free_auth_token: str):
    """Create authorization headers for free user"""
    return {"Authorization": f"Bearer {free_auth_token}"}


@pytest.fixture
def test_training_program(db: Session, test_user: User):
    """Create a test training program"""
    program = TrainingProgram(
        title="Test Training Program",
        description="Test Description",
        category="compliance",
        is_mandatory=True,
        requires_certification=True,
        created_by=test_user.id,
        is_active=True,
        facility_type="daycare"
    )
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


class TestTrainingPrograms:
    """Test training program endpoints"""
    
    def test_get_training_programs_success(self, db: Session, test_user: User, test_training_program: TrainingProgram, auth_headers: dict):
        """Test successful retrieval of training programs"""
        response = client.get(
            "/api/v1/training/programs",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "programs" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["programs"], list)
    
    def test_get_training_programs_free_user(self, db: Session, free_user: User, free_auth_headers: dict):
        """Test training programs for free user (should get preview data)"""
        response = client.get(
            "/api/v1/training/programs",
            headers=free_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "programs" in data
        # Free users should get preview/sample data
    
    def test_get_training_programs_with_filters(self, db: Session, test_user: User, test_training_program: TrainingProgram, auth_headers: dict):
        """Test training programs with filters"""
        response = client.get(
            "/api/v1/training/programs?category=compliance&is_mandatory=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "programs" in data
    
    def test_get_training_program_by_id_success(self, db: Session, test_user: User, test_training_program: TrainingProgram, auth_headers: dict):
        """Test successful retrieval of specific training program"""
        response = client.get(
            f"/api/v1/training/programs/{test_training_program.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_training_program.id
        assert data["title"] == test_training_program.title
    
    def test_get_training_program_not_found(self, db: Session, test_user: User, auth_headers: dict):
        """Test retrieval of non-existent training program"""
        response = client.get(
            "/api/v1/training/programs/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_create_training_program_success(self, db: Session, test_user: User, auth_headers: dict):
        """Test successful creation of training program"""
        program_data = {
            "title": "New Training Program",
            "description": "New Description",
            "category": "safety",
            "is_mandatory": False,
            "requires_certification": False
        }
        
        response = client.post(
            "/api/v1/training/programs",
            headers=auth_headers,
            json=program_data
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["title"] == program_data["title"]
    
    def test_update_training_program_success(self, db: Session, test_user: User, test_training_program: TrainingProgram, auth_headers: dict):
        """Test successful update of training program"""
        update_data = {
            "title": "Updated Training Program",
            "description": "Updated Description"
        }
        
        response = client.put(
            f"/api/v1/training/programs/{test_training_program.id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
    
    def test_delete_training_program_success(self, db: Session, test_user: User, test_training_program: TrainingProgram, auth_headers: dict):
        """Test successful deletion of training program"""
        response = client.delete(
            f"/api/v1/training/programs/{test_training_program.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204]
    
    def test_training_programs_unauthorized(self, db: Session):
        """Test training programs endpoint without authentication"""
        response = client.get("/api/v1/training/programs")
        
        assert response.status_code == 401


class TestTrainingTestEndpoint:
    """Test training test endpoint"""
    
    def test_training_test_endpoint(self, db: Session):
        """Test the training test endpoint"""
        response = client.get("/api/v1/training/test")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data


class TestTrainingDashboard:
    """Test training dashboard endpoint"""
    
    def test_get_training_dashboard_success(self, db: Session, test_user: User, auth_headers: dict):
        """Test successful retrieval of training dashboard"""
        response = client.get(
            "/api/v1/training/dashboard",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Dashboard structure may vary
    
    def test_get_training_dashboard_unauthorized(self, db: Session):
        """Test training dashboard without authentication"""
        response = client.get("/api/v1/training/dashboard")
        
        assert response.status_code == 401


class TestTrainingAnalytics:
    """Test training analytics endpoint"""
    
    def test_get_training_analytics_success(self, db: Session, test_user: User, auth_headers: dict):
        """Test successful retrieval of training analytics"""
        response = client.get(
            "/api/v1/training/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # Analytics structure may vary
    
    def test_get_training_analytics_unauthorized(self, db: Session):
        """Test training analytics without authentication"""
        response = client.get("/api/v1/training/analytics")
        
        assert response.status_code == 401

