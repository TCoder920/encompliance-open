"""
Export Routes Integration Tests
------------------------------
Comprehensive tests for export endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app import main
from app.database import get_db
from app.models.user import User, UserRole
from app.models.export_request import ExportRequest, ExportStatus, ExportFormat
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
def test_export_request(db: Session, test_user: User):
    """Create a test export request"""
    export_request = ExportRequest(
        user_id=test_user.id,
        status=ExportStatus.PENDING,
        format=ExportFormat.JSON,
        data_types=["user_profile"],
        estimated_size=1000000
    )
    db.add(export_request)
    db.commit()
    db.refresh(export_request)
    return export_request


@pytest.fixture
def auth_token(test_user: User):
    """Create an auth token for test user"""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def auth_headers(auth_token: str):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestExportQuotaStatus:
    """Test export quota status endpoint"""
    
    @patch('app.api.routes.export.ExportQuotaService.get_quota_status')
    def test_get_quota_status_success(self, mock_quota, db: Session, test_user: User, auth_headers: dict):
        """Test successful quota status retrieval"""
        mock_quota.return_value = {
            "used": 0,
            "limit": 1,
            "available": 1,
            "next_reset": "2024-01-01"
        }
        
        response = client.get(
            "/api/v1/export/quota-status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "quota" in data
        assert "subscription" in data
    
    def test_get_quota_status_unauthorized(self, db: Session):
        """Test quota status without authentication"""
        response = client.get("/api/v1/export/quota-status")
        
        assert response.status_code == 401


class TestExportEstimate:
    """Test export size estimation endpoint"""
    
    @patch('app.api.routes.export.ExportService.estimate_export_size')
    @patch('app.api.routes.export.ExportService.calculate_fee')
    def test_estimate_export_size_success(self, mock_fee, mock_estimate, db: Session, test_user: User, auth_headers: dict):
        """Test successful export size estimation"""
        mock_estimate.return_value = 1000000
        mock_fee.return_value = 0.0
        
        estimate_data = {
            "data_types": ["user_profile", "documents"]
        }
        
        response = client.post(
            "/api/v1/export/estimate",
            headers=auth_headers,
            json=estimate_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "estimated_size" in data
        assert "requires_fee" in data
    
    def test_estimate_export_unauthorized(self, db: Session):
        """Test export estimation without authentication"""
        response = client.post(
            "/api/v1/export/estimate",
            json={"data_types": ["user_profile"]}
        )
        
        assert response.status_code == 401


class TestExportInitiate:
    """Test export initiation endpoint"""
    
    @patch('app.api.routes.export.ExportService.initiate_export')
    def test_initiate_export_success(self, mock_initiate, db: Session, test_user: User, auth_headers: dict):
        """Test successful export initiation"""
        mock_initiate.return_value = {
            "export_id": "export_123",
            "status": "pending",
            "estimated_size": 1000000
        }
        
        export_data = {
            "format": "json",
            "data_types": ["user_profile"]
        }
        
        response = client.post(
            "/api/v1/export/initiate",
            headers=auth_headers,
            json=export_data
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "export_id" in data or "id" in data
    
    def test_initiate_export_unauthorized(self, db: Session):
        """Test export initiation without authentication"""
        response = client.post(
            "/api/v1/export/initiate",
            json={"format": "json", "data_types": ["user_profile"]}
        )
        
        assert response.status_code == 401


class TestExportStatus:
    """Test export status endpoint"""
    
    @patch('app.api.routes.export.ExportService.get_export_status')
    def test_get_export_status_success(self, mock_status, db: Session, test_user: User, test_export_request: ExportRequest, auth_headers: dict):
        """Test successful export status retrieval"""
        mock_status.return_value = {
            "id": str(test_export_request.id),
            "status": "pending",
            "progress_percentage": 0
        }
        
        response = client.get(
            f"/api/v1/export/status/{test_export_request.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_get_export_status_unauthorized(self, db: Session, test_export_request: ExportRequest):
        """Test export status without authentication"""
        response = client.get(f"/api/v1/export/status/{test_export_request.id}")
        
        assert response.status_code == 401

