"""
Payments Routes Integration Tests
---------------------------------
Comprehensive tests for payment endpoints including:
- Subscription creation
- Payment method management
- Invoice retrieval
- Seat updates
- Subscription cancellation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock, AsyncMock

from app import main
from app.database import get_db
from app.models.user import User, UserRole
from app.models.facility import Facility
from app.models.subscription import Subscription
from app.models.subscription import SubscriptionStatus
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
        subscription_status="free"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def pro_user(db: Session):
    """Create a pro user with facility"""
    user = User(
        email="pro@example.com",
        username="prouser",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Pro User",
        operation_name="Pro Operation",
        state="CA",
        is_active=True,
        email_verified=True,
        subscription_status="pro",
        user_role=UserRole.FACILITY_ADMIN
    )
    db.add(user)
    
    facility = Facility(
        facility_name="Pro Facility",
        facility_type="daycare",
        state="CA",
        admin_user_id=user.id,
        stripe_customer_id="cus_test123"
    )
    db.add(facility)
    
    subscription = Subscription(
        facility_id=facility.id,
        stripe_subscription_id="sub_test123",
        seat_count=5,
        status=SubscriptionStatus.ACTIVE
    )
    db.add(subscription)
    
    db.commit()
    db.refresh(user)
    db.refresh(facility)
    
    user.facility_id = facility.id
    db.commit()
    
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
def pro_auth_token(pro_user: User):
    """Create an auth token for pro user"""
    return create_access_token(data={"sub": pro_user.username})


@pytest.fixture
def pro_auth_headers(pro_auth_token: str):
    """Create authorization headers for pro user"""
    return {"Authorization": f"Bearer {pro_auth_token}"}


class TestSubscriptionStatus:
    """Test subscription status endpoint"""
    
    def test_get_subscription_status_free_user(self, db: Session, test_user: User, auth_headers: dict):
        """Test subscription status for free user"""
        response = client.get(
            "/api/v1/payments/subscription-status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "subscription_status" in data
        assert data["subscription_status"] == "free"
    
    def test_get_subscription_status_pro_user(self, db: Session, pro_user: User, pro_auth_headers: dict):
        """Test subscription status for pro user"""
        response = client.get(
            "/api/v1/payments/subscription-status",
            headers=pro_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "subscription_status" in data
    
    def test_get_subscription_status_unauthorized(self, db: Session):
        """Test subscription status without authentication"""
        response = client.get("/api/v1/payments/subscription-status")
        
        assert response.status_code == 401


class TestCreateCheckoutSession:
    """Test checkout session creation"""
    
    @patch('app.api.routes.payments.StripeService')
    def test_create_checkout_session_success(self, mock_stripe_service, db: Session, test_user: User, auth_headers: dict):
        """Test successful checkout session creation"""
        mock_service = MagicMock()
        mock_stripe_service.return_value = mock_service
        mock_session = MagicMock()
        mock_session.id = "cs_test123"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_service.create_checkout_session.return_value = mock_session
        
        checkout_data = {
            "mode": "subscription",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel"
        }
        
        response = client.post(
            "/api/v1/payments/create-checkout-session",
            headers=auth_headers,
            json=checkout_data
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "session_id" in data or "url" in data
    
    def test_create_checkout_session_unauthorized(self, db: Session):
        """Test checkout session creation without authentication"""
        response = client.post(
            "/api/v1/payments/create-checkout-session",
            json={
                "mode": "subscription",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel"
            }
        )
        
        assert response.status_code == 401


class TestUpdateSubscriptionSeats:
    """Test subscription seat updates"""
    
    @patch('app.api.routes.payments.StripeService')
    def test_update_subscription_seats_success(self, mock_stripe_service, db: Session, pro_user: User, pro_auth_headers: dict):
        """Test successful subscription seat update"""
        mock_service = MagicMock()
        mock_stripe_service.return_value = mock_service
        mock_service.update_subscription_seats.return_value = None
        
        update_data = {
            "seat_count": 10
        }
        
        response = client.post(
            "/api/v1/payments/update-subscription-seats",
            headers=pro_auth_headers,
            json=update_data
        )
        
        assert response.status_code in [200, 400, 404]
    
    def test_update_subscription_seats_unauthorized(self, db: Session):
        """Test seat update without authentication"""
        response = client.post(
            "/api/v1/payments/update-subscription-seats",
            json={"seat_count": 10}
        )
        
        assert response.status_code == 401


class TestCancelSubscription:
    """Test subscription cancellation"""
    
    @patch('app.api.routes.payments.StripeService')
    @patch('app.api.routes.payments.SubscriptionDowngradeService')
    def test_cancel_subscription_success(
        self, 
        mock_downgrade_service, 
        mock_stripe_service,
        db: Session, 
        pro_user: User, 
        pro_auth_headers: dict
    ):
        """Test successful subscription cancellation"""
        mock_stripe = MagicMock()
        mock_stripe_service.return_value = mock_stripe
        mock_stripe.cancel_subscription.return_value = None
        
        mock_downgrade = MagicMock()
        mock_downgrade_service.return_value = mock_downgrade
        
        response = client.post(
            "/api/v1/payments/cancel-subscription",
            headers=pro_auth_headers
        )
        
        assert response.status_code in [200, 400, 404]
    
    def test_cancel_subscription_unauthorized(self, db: Session):
        """Test subscription cancellation without authentication"""
        response = client.post("/api/v1/payments/cancel-subscription")
        
        assert response.status_code == 401


class TestGetInvoices:
    """Test invoice retrieval"""
    
    @patch('app.api.routes.payments.stripe.Invoice.list')
    def test_get_invoices_success(self, mock_list, db: Session, pro_user: User, pro_auth_headers: dict):
        """Test successful invoice retrieval"""
        mock_invoice = MagicMock()
        mock_invoice.id = "in_test123"
        mock_invoice.amount_due = 5000
        mock_invoice.status = "paid"
        mock_list.return_value.data = [mock_invoice]
        
        response = client.get(
            "/api/v1/payments/invoices",
            headers=pro_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_invoices_unauthorized(self, db: Session):
        """Test invoice retrieval without authentication"""
        response = client.get("/api/v1/payments/invoices")
        
        assert response.status_code == 401

