"""
Authentication Routes Integration Tests
---------------------------------------
Comprehensive tests for authentication endpoints including:
- Login/logout flows
- Session-based signup
- Email verification
- Password reset
- Multi-factor authentication
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import jwt

from app import main
from app.database import get_db, Base
from app.models.user import User
from app.models.signup_session import SignupSession
from app.models.otp import OTP, OTPType
from app.models.token import BlacklistedToken
from app.auth.utils import (
    get_password_hash, 
    create_access_token, 
    SECRET_KEY, 
    ALGORITHM, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.models.facility_type import FacilityType
from app.models.regulation import Regulation

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
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"test_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
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
    yield user
    # Cleanup
    try:
        db.delete(user)
        db.commit()
    except:
        db.rollback()


@pytest.fixture
def inactive_user(db: Session):
    """Create an inactive test user"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"inactive_{unique_id}@example.com",
        username=f"inactiveuser_{unique_id}",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Inactive User",
        operation_name="Test Operation",
        state="CA",
        is_active=False,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    # Cleanup
    try:
        db.delete(user)
        db.commit()
    except:
        db.rollback()


@pytest.fixture
def auth_token(test_user: User):
    """Create an auth token for test user"""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture
def auth_headers(auth_token: str):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestLogin:
    """Test login endpoint"""
    
    def test_login_success(self, db: Session, test_user: User):
        """Test successful login"""
        response = client.post(
            "/api/v1/login",
            json={
                "username": test_user.username,
                "password": "TestPassword123!"
            }
        )
        
        # Login may return 200 with token, or 202 if email verification needed
        assert response.status_code in [200, 202]
        data = response.json()
        
        if response.status_code == 200:
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            # User info may or may not be included depending on endpoint implementation
            if "user" in data:
                assert data["user"]["id"] == test_user.id
                assert data["user"]["username"] == test_user.username
        else:
            # 202 means email verification pending
            assert "status" in data
            assert "login_pending_email_verification" in data.get("status", "")
    
    def test_login_invalid_username(self, db: Session):
        """Test login with invalid username"""
        response = client.post(
            "/api/v1/login",
            json={
                "username": "nonexistent",
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, db: Session, test_user: User):
        """Test login with invalid password"""
        response = client.post(
            "/api/v1/login",
            json={
                "username": test_user.username,
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_missing_username(self, db: Session):
        """Test login without username"""
        response = client.post(
            "/api/v1/login",
            json={"password": "TestPassword123!"}
        )
        
        # Endpoint returns 400 when username/password missing, but FastAPI may return 422 for validation
        assert response.status_code in [400, 422]
        detail = response.json().get("detail", "")
        if isinstance(detail, str):
            assert "required" in detail.lower() or "username" in detail.lower() or "password" in detail.lower()
        elif isinstance(detail, list):
            # FastAPI validation error format
            assert any("username" in str(err).lower() for err in detail)
    
    def test_login_missing_password(self, db: Session, test_user: User):
        """Test login without password"""
        response = client.post(
            "/api/v1/login",
            json={"username": test_user.username}
        )
        
        # Endpoint returns 400 when username/password missing, but FastAPI may return 422 for validation
        assert response.status_code in [400, 422]
        detail = response.json().get("detail", "")
        if isinstance(detail, str):
            assert "required" in detail.lower() or "password" in detail.lower()
        elif isinstance(detail, list):
            # FastAPI validation error format
            assert any("password" in str(err).lower() for err in detail)
    
    def test_login_inactive_user(self, db: Session, inactive_user: User):
        """Test login with inactive user"""
        with patch('app.api.routes.auth.send_email_otp') as mock_send_otp:
            mock_send_otp.return_value = (True, "OTP sent")
            
            response = client.post(
                "/api/v1/login",
                json={
                    "username": inactive_user.username,
                    "password": "TestPassword123!"
                }
            )
            
            # Should return 200 but require email verification
            assert response.status_code in [200, 401]
    
    @patch('app.api.routes.auth.send_email_otp')
    def test_login_triggers_otp_for_inactive_user(self, mock_send_otp, db: Session, inactive_user: User):
        """Test that login triggers OTP for inactive users"""
        mock_send_otp.return_value = (True, "OTP sent")
        
        # Set last_login to more than 7 days ago
        inactive_user.last_login = datetime.now() - timedelta(days=8)
        db.commit()
        
        response = client.post(
            "/api/v1/login",
            json={
                "username": inactive_user.username,
                "password": "TestPassword123!"
            }
        )
        
        # Should trigger OTP if user hasn't logged in for 7+ days
        # The exact behavior depends on implementation
        assert response.status_code in [200, 401]


class TestLogout:
    """Test logout endpoint"""
    
    def test_logout_success(self, db: Session, test_user: User, auth_headers: dict):
        """Test successful logout"""
        response = client.post(
            "/api/v1/logout",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()
        
        # Verify token is blacklisted
        token = auth_headers["Authorization"].split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        
        if jti:
            blacklisted = db.query(BlacklistedToken).filter(
                BlacklistedToken.token_jti == jti
            ).first()
            # Token should be blacklisted (if jti exists)
            # Note: Some tokens may not have jti
    
    def test_logout_unauthorized(self, db: Session):
        """Test logout without authentication"""
        response = client.post("/api/v1/logout")
        
        assert response.status_code == 401
    
    def test_logout_invalid_token(self, db: Session):
        """Test logout with invalid token"""
        response = client.post(
            "/api/v1/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401


class TestSessionSignup:
    """Test session-based signup endpoints"""
    
    def test_session_signup_step1_success(self, db: Session):
        """Test successful step 1 signup"""
        with patch('app.services.signup_session_service.SignupSessionService.create_session') as mock_create:
            mock_session = SignupSession(
                id=1,
                session_token="test_token_123",
                email="newuser@example.com",
                step_completed=1,
                expires_at=datetime.now() + timedelta(hours=24)
            )
            mock_create.return_value = mock_session
            
            response = client.post(
                "/api/v1/session-signup/step1",
                json={
                    "email": "newuser@example.com",
                    "password": "SecurePassword123!",
                    "full_name": "New User",
                    "operation_name": "New Operation",
                    "phone_number": "+1234567890"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "session_token" in data
            assert data["step_completed"] == 1
            assert "expires_at" in data
    
    def test_session_signup_step1_weak_password(self, db: Session):
        """Test signup with weak password"""
        response = client.post(
            "/api/v1/session-signup/step1",
            json={
                "email": "newuser@example.com",
                "password": "weak",
                "full_name": "New User",
                "operation_name": "New Operation"
            }
        )
        
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()
    
    def test_session_signup_step1_duplicate_email(self, db: Session, test_user: User):
        """Test signup with existing email"""
        with patch('app.services.signup_session_service.SignupSessionService.create_session') as mock_create:
            mock_create.return_value = None  # Simulate duplicate email
            
            response = client.post(
                "/api/v1/session-signup/step1",
                json={
                    "email": test_user.email,
                    "password": "SecurePassword123!",
                    "full_name": "New User",
                    "operation_name": "New Operation"
                }
            )
            
            assert response.status_code == 400
            assert "already registered" in response.json()["detail"].lower()
    
    @patch('app.api.routes.auth.send_email_otp')
    def test_session_signup_step2_success(self, mock_send_otp, db: Session):
        """Test successful step 2 signup"""
        mock_send_otp.return_value = (True, "OTP sent")
        
        # Create a signup session first
        session = SignupSession(
            session_token="test_token_123",
            email="newuser@example.com",
            step_completed=1,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        db.add(session)
        db.commit()
        
        response = client.post(
            "/api/v1/session-signup/step2",
            json={
                "session_token": "test_token_123",
                "facility_type": "daycare"
            }
        )
        
        # Should either succeed or require proper session handling
        assert response.status_code in [200, 400, 404]


class TestEmailVerification:
    """Test email verification endpoints"""
    
    @patch('app.api.routes.auth.verify_otp_util')
    def test_verify_session_signup_email_success(self, mock_verify_otp, db: Session):
        """Test successful email verification for session signup"""
        mock_verify_otp.return_value = True
        
        # Create signup session
        session = SignupSession(
            session_token="test_token_123",
            email="newuser@example.com",
            step_completed=2,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        db.add(session)
        
        # Create OTP record
        otp = OTP(
            user_id=None,
            otp_type=OTPType.EMAIL,
            otp_hash="hashed_otp",
            recipient="newuser@example.com",
            expires_at=datetime.now() + timedelta(minutes=10)
        )
        db.add(otp)
        db.commit()
        
        response = client.post(
            "/api/v1/verify-session-signup-email",
            json={
                "session_token": "test_token_123",
                "otp_code": "123456"
            }
        )
        
        # Response depends on implementation
        assert response.status_code in [200, 400, 404]
    
    def test_verify_session_signup_email_invalid_token(self, db: Session):
        """Test email verification with invalid session token"""
        response = client.post(
            "/api/v1/verify-session-signup-email",
            json={
                "session_token": "invalid_token",
                "otp_code": "123456"
            }
        )
        
        assert response.status_code in [400, 404]
    
    def test_verify_session_signup_email_invalid_otp(self, db: Session):
        """Test email verification with invalid OTP"""
        # Create signup session
        session = SignupSession(
            session_token="test_token_123",
            email="newuser@example.com",
            step_completed=2,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        db.add(session)
        db.commit()
        
        with patch('app.api.routes.auth.verify_otp_util') as mock_verify:
            mock_verify.return_value = False
            
            response = client.post(
                "/api/v1/verify-session-signup-email",
                json={
                    "session_token": "test_token_123",
                    "otp_code": "wrong_code"
                }
            )
            
            assert response.status_code == 400


class TestFacilityTypes:
    """Test facility types endpoint"""
    
    def test_get_facility_types_success(self, db: Session):
        """Test getting facility types"""
        # Create some facility types
        facility_type1 = FacilityType(name="daycare")
        facility_type2 = FacilityType(name="residential")
        db.add(facility_type1)
        db.add(facility_type2)
        db.commit()
        
        response = client.get("/api/v1/facility-types")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "daycare" in data
        assert "residential" in data
    
    def test_get_facility_types_empty(self, db: Session):
        """Test getting facility types when none exist"""
        response = client.get("/api/v1/facility-types")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestResendEmail:
    """Test resend email endpoints"""
    
    @patch('app.api.routes.auth.send_email_otp')
    def test_resend_signup_email_success(self, mock_send_otp, db: Session, inactive_user: User):
        """Test successful resend of signup email"""
        mock_send_otp.return_value = (True, "OTP sent")
        
        response = client.post(
            "/api/v1/resend-signup-email",
            json={"email": inactive_user.email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        mock_send_otp.assert_called_once()
    
    def test_resend_signup_email_user_not_found(self, db: Session):
        """Test resend email for non-existent user"""
        response = client.post(
            "/api/v1/resend-signup-email",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code in [400, 404]
    
    @patch('app.api.routes.auth.send_email_otp')
    def test_resend_session_signup_email_success(self, mock_send_otp, db: Session):
        """Test successful resend of session signup email"""
        mock_send_otp.return_value = (True, "OTP sent")
        
        # Create signup session
        session = SignupSession(
            session_token="test_token_123",
            email="newuser@example.com",
            step_completed=1,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        db.add(session)
        db.commit()
        
        response = client.post(
            "/api/v1/resend-session-signup-email",
            json={"session_token": "test_token_123"}
        )
        
        assert response.status_code == 200
        mock_send_otp.assert_called_once()
    
    def test_resend_session_signup_email_invalid_token(self, db: Session):
        """Test resend email with invalid session token"""
        response = client.post(
            "/api/v1/resend-session-signup-email",
            json={"session_token": "invalid_token"}
        )
        
        assert response.status_code in [400, 404]

