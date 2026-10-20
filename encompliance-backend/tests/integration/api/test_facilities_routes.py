"""
Facilities Routes Integration Tests
-----------------------------------
Comprehensive tests for facility management endpoints including:
- Facility CRUD operations
- Facility invitations
- Team member management
- Facility settings
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import patch, MagicMock

from app import main
from app.database import get_db
from app.models.user import User, UserRole
from app.models.facility import Facility
from app.models.facility_invitation import FacilityInvitation
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
    """Create a test user (facility admin)"""
    user = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Admin User",
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
def test_facility(db: Session, test_user: User):
    """Create a test facility"""
    facility = Facility(
        facility_name="Test Facility",
        facility_type="daycare",
        state="CA",
        admin_user_id=test_user.id,
        stripe_customer_id="cus_test123"
    )
    db.add(facility)
    db.commit()
    db.refresh(facility)
    
    # Link user to facility
    test_user.facility_id = facility.id
    db.commit()
    
    return facility


@pytest.fixture
def auth_token(test_user: User):
    """Create an auth token for test user"""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def auth_headers(auth_token: str):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestFacilityManagement:
    """Test facility management endpoints"""
    
    def test_get_facilities_success(self, db: Session, test_user: User, test_facility: Facility, auth_headers: dict):
        """Test successful retrieval of facilities"""
        response = client.get(
            "/api/v1/facilities",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_facility_by_id_success(self, db: Session, test_user: User, test_facility: Facility, auth_headers: dict):
        """Test successful retrieval of specific facility"""
        response = client.get(
            f"/api/v1/facilities/{test_facility.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_facility.id
    
    def test_get_facility_not_found(self, db: Session, test_user: User, auth_headers: dict):
        """Test retrieval of non-existent facility"""
        response = client.get(
            "/api/v1/facilities/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_create_facility_success(self, db: Session, test_user: User, auth_headers: dict):
        """Test successful creation of facility"""
        facility_data = {
            "facility_name": "New Facility",
            "facility_type": "residential",
            "state": "NY"
        }
        
        response = client.post(
            "/api/v1/facilities",
            headers=auth_headers,
            json=facility_data
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["facility_name"] == facility_data["facility_name"]
    
    def test_update_facility_success(self, db: Session, test_user: User, test_facility: Facility, auth_headers: dict):
        """Test successful update of facility"""
        update_data = {
            "facility_name": "Updated Facility Name"
        }
        
        response = client.put(
            f"/api/v1/facilities/{test_facility.id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["facility_name"] == update_data["facility_name"]
    
    def test_delete_facility_success(self, db: Session, test_user: User, test_facility: Facility, auth_headers: dict):
        """Test successful deletion of facility"""
        response = client.delete(
            f"/api/v1/facilities/{test_facility.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204]
    
    def test_facilities_unauthorized(self, db: Session):
        """Test facilities endpoint without authentication"""
        response = client.get("/api/v1/facilities")
        
        assert response.status_code == 401


class TestFacilityInvitations:
    """Test facility invitation endpoints"""
    
    def test_create_facility_invitation_success(self, db: Session, test_user: User, test_facility: Facility, auth_headers: dict):
        """Test successful creation of facility invitation"""
        invitation_data = {
            "email": "invitee@example.com",
            "role": "team_member"
        }
        
        response = client.post(
            f"/api/v1/facilities/{test_facility.id}/invitations",
            headers=auth_headers,
            json=invitation_data
        )
        
        assert response.status_code in [200, 201]
    
    def test_get_facility_invitations_success(self, db: Session, test_user: User, test_facility: Facility, auth_headers: dict):
        """Test successful retrieval of facility invitations"""
        response = client.get(
            f"/api/v1/facilities/{test_facility.id}/invitations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_facility_invitations_unauthorized(self, db: Session, test_facility: Facility):
        """Test facility invitations without authentication"""
        response = client.get(f"/api/v1/facilities/{test_facility.id}/invitations")
        
        assert response.status_code == 401

