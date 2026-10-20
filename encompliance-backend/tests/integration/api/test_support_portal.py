"""
Support Portal Integration Tests
---------------------------------
Comprehensive tests for customer support portal functionality including:
- Ticket CRUD operations
- Ticket comments, assignment, escalation, resolution
- Analytics with date filtering
- Customer context and history timeline
- Agent management operations
- WebSocket notifications
"""

import os
# Force tests to use a local SQLite database before any app imports occur.
TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_app.db"))
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

# CRITICAL: Import all models BEFORE importing app.database or app.main
# This ensures Base.metadata has all tables registered before the engine is created
import app.models  # noqa: F401

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
import json

from app.support_portal_main import support_portal_app
from app.database import SupportPortalBase, support_portal_engine, get_support_portal_db, get_db
from app.models.support_portal_account import SupportPortalAccount
from app.models.support_ticket import (
    SupportTicket,
    SupportTicketComment,
    SupportAgentProfile,
    TicketStatus,
    TicketPriority,
    TicketCategory,
    SupportTier,
    CommenterType,
)
from app.models.user import User
from app.models.facility import Facility
from app.models.subscription import Subscription
from app.auth.support_portal_auth_utils import create_access_token, get_password_hash
from app.database import Base, engine, SessionLocal

# Create test client for support portal
client = TestClient(support_portal_app)


@pytest.fixture(scope="function")
def support_db_session():
    """Create a clean support portal database session for testing."""
    # Create an in-memory SQLite database for testing
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables in the test database
    SupportPortalBase.metadata.create_all(test_engine)
    
    # Create a session factory bound to the engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create a session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Dispose the engine to close all connections
        test_engine.dispose()


@pytest.fixture(scope="function")
def user_db_session():
    """Create a clean user database session for testing."""
    # Import all models to ensure they're registered
    import app.models  # noqa: F401
    
    # Create an in-memory SQLite database for testing
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables in the test database
    Base.metadata.create_all(test_engine)
    
    # Create a session factory bound to the engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create a session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Dispose the engine to close all connections
        test_engine.dispose()


@pytest.fixture
def support_db(support_db_session):
    """Override get_support_portal_db dependency."""
    def override_get_support_portal_db():
        try:
            yield support_db_session
        finally:
            pass
    
    support_portal_app.dependency_overrides[get_support_portal_db] = override_get_support_portal_db
    yield support_db_session
    support_portal_app.dependency_overrides.pop(get_support_portal_db, None)


@pytest.fixture
def user_db(user_db_session):
    """Override get_db dependency."""
    def override_get_db():
        try:
            yield user_db_session
        finally:
            pass
    
    support_portal_app.dependency_overrides[get_db] = override_get_db
    yield user_db_session
    support_portal_app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def support_account_beginner(support_db: Session):
    """Create a beginner support account."""
    account = SupportPortalAccount(
        username="beginner_agent",
        email="beginner@support.com",
        hashed_password=get_password_hash("testpass123"),
        roles=["support_agent"],
    )
    support_db.add(account)
    support_db.commit()
    support_db.refresh(account)
    return account


@pytest.fixture
def support_account_senior(support_db: Session):
    """Create a senior support account."""
    account = SupportPortalAccount(
        username="senior_agent",
        email="senior@support.com",
        hashed_password=get_password_hash("testpass123"),
        roles=["support_admin"],
    )
    support_db.add(account)
    support_db.commit()
    support_db.refresh(account)
    return account


@pytest.fixture
def support_agent_profile(support_db: Session, support_account_beginner):
    """Create a support agent profile."""
    profile = SupportAgentProfile(
        account_id=support_account_beginner.id,
        support_tier=SupportTier.BEGINNER,
        specialization_tags=["billing"],
        max_concurrent_tickets=5,
        is_active=True,
    )
    support_db.add(profile)
    support_db.commit()
    support_db.refresh(profile)
    return profile


@pytest.fixture
def support_token_beginner(support_account_beginner):
    """Create a JWT token for beginner agent."""
    return create_access_token(
        data={"sub": support_account_beginner.username, "roles": support_account_beginner.roles}
    )


@pytest.fixture
def support_token_senior(support_account_senior):
    """Create a JWT token for senior agent."""
    return create_access_token(
        data={"sub": support_account_senior.username, "roles": support_account_senior.roles}
    )


@pytest.fixture
def test_user(user_db: Session):
    """Create a test user in the user database."""
    user = User(
        email="customer@example.com",
        username="testcustomer",
        hashed_password="hashed_password",
        is_active=True,
        full_name="Test Customer",
        subscription_status="pro",
    )
    user_db.add(user)
    user_db.commit()
    user_db.refresh(user)
    return user


@pytest.fixture
def test_facility(user_db: Session, test_user):
    """Create a test facility."""
    facility = Facility(
        facility_name="Test Facility",
        facility_address="123 Test St",
        facility_city="Test City",
        facility_state="CA",
        facility_zip="12345",
        facility_phone="555-1234",
        facility_email="facility@example.com",
        is_active=True,
        max_users=10,
        admin_user_id=test_user.id,
    )
    user_db.add(facility)
    user_db.commit()
    user_db.refresh(facility)
    
    # Associate user with facility
    test_user.facility_id = facility.id
    user_db.commit()
    
    return facility


@pytest.fixture
def test_subscription(user_db: Session, test_facility):
    """Create a test subscription."""
    subscription = Subscription(
        facility_id=test_facility.id,
        stripe_subscription_id="sub_test_123",
        stripe_customer_id="cus_test_123",
        stripe_price_id="price_test_123",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
        seat_count=5,
        total_amount=99.99,
    )
    user_db.add(subscription)
    user_db.commit()
    user_db.refresh(subscription)
    return subscription


@pytest.fixture
def test_ticket(support_db: Session, test_user):
    """Create a test support ticket."""
    ticket = SupportTicket(
        subject="Test Ticket",
        description="This is a test ticket",
        category=TicketCategory.TECHNICAL,
        priority=TicketPriority.MEDIUM,
        support_tier_required=SupportTier.BEGINNER,
        user_id=test_user.id if test_user else None,
        facility_id=test_user.facility_id if test_user else None,
        status=TicketStatus.OPEN,
    )
    support_db.add(ticket)
    support_db.commit()
    support_db.refresh(ticket)
    return ticket


class TestSupportPortalAuthentication:
    """Test support portal authentication endpoints."""
    
    def test_login_success(self, support_db: Session, support_account_beginner):
        """Test successful login."""
        response = client.post(
            "/auth/token",
            data={
                "username": support_account_beginner.username,
                "password": "testpass123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_failure_invalid_credentials(self, support_db: Session, support_account_beginner):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/token",
            data={
                "username": support_account_beginner.username,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
    
    def test_get_current_account(self, support_token_beginner, support_account_beginner):
        """Test getting current account info."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == support_account_beginner.username
        assert data["email"] == support_account_beginner.email


class TestTicketCRUD:
    """Test ticket CRUD operations."""
    
    def test_create_ticket(self, support_db: Session, support_token_beginner, test_user):
        """Test creating a new ticket."""
        with patch("app.api.routes.support_tickets.broadcast_ticket_event", new_callable=AsyncMock):
            response = client.post(
                "/api/v1/support/tickets",
                headers={"Authorization": f"Bearer {support_token_beginner}"},
                json={
                    "subject": "New Test Ticket",
                    "description": "This is a new test ticket",
                    "category": "technical",
                    "priority": "medium",
                    "facility_id": test_user.facility_id if test_user else None,
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["subject"] == "New Test Ticket"
            assert data["status"] == "open"
            assert "ticket_number" in data
    
    def test_list_tickets(self, support_db: Session, support_token_beginner, test_ticket):
        """Test listing tickets."""
        response = client.get(
            "/api/v1/support/tickets",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_list_tickets_with_filters(self, support_db: Session, support_token_beginner, test_ticket):
        """Test listing tickets with filters."""
        response = client.get(
            "/api/v1/support/tickets",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
            params={
                "status_filter": "open",
                "priority_filter": "medium",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_ticket(self, support_db: Session, support_token_beginner, test_ticket):
        """Test getting a specific ticket."""
        response = client.get(
            f"/api/v1/support/tickets/{test_ticket.id}",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_ticket.id
        assert data["subject"] == test_ticket.subject
    
    def test_update_ticket(self, support_db: Session, support_token_beginner, test_ticket):
        """Test updating a ticket."""
        response = client.put(
            f"/api/v1/support/tickets/{test_ticket.id}",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
            json={
                "subject": "Updated Subject",
                "description": "Updated description",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "Updated Subject"
    
    def test_get_nonexistent_ticket(self, support_db: Session, support_token_beginner):
        """Test getting a non-existent ticket."""
        response = client.get(
            "/api/v1/support/tickets/99999",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
        )
        assert response.status_code == 404


class TestTicketComments:
    """Test ticket comment operations."""
    
    def test_create_comment(self, support_db: Session, support_token_beginner, test_ticket):
        """Test adding a comment to a ticket."""
        with patch("app.api.routes.support_tickets.broadcast_ticket_event", new_callable=AsyncMock):
            with patch("app.api.routes.support_tickets.SupportTicketNotificationService.notify_ticket_comment", new_callable=AsyncMock):
                response = client.post(
                    f"/api/v1/support/tickets/{test_ticket.id}/comments",
                    headers={"Authorization": f"Bearer {support_token_beginner}"},
                    json={
                        "comment_text": "This is a test comment",
                        "is_internal": False,
                    },
                )
                assert response.status_code == 201
                data = response.json()
                assert data["comment_text"] == "This is a test comment"
                assert data["commenter_type"] == "support"
    
    def test_list_comments(self, support_db: Session, support_token_beginner, test_ticket):
        """Test listing comments for a ticket."""
        # First create a comment
        with patch("app.api.routes.support_tickets.broadcast_ticket_event", new_callable=AsyncMock):
            with patch("app.api.routes.support_tickets.SupportTicketNotificationService.notify_ticket_comment", new_callable=AsyncMock):
                client.post(
                    f"/api/v1/support/tickets/{test_ticket.id}/comments",
                    headers={"Authorization": f"Bearer {support_token_beginner}"},
                    json={
                        "comment_text": "Test comment",
                        "is_internal": False,
                    },
                )
        
        # Then list comments
        response = client.get(
            f"/api/v1/support/tickets/{test_ticket.id}/comments",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestTicketAssignment:
    """Test ticket assignment operations."""
    
    def test_assign_ticket(self, support_db: Session, support_token_beginner, support_account_beginner, support_agent_profile, test_ticket):
        """Test assigning a ticket to an agent."""
        with patch("app.api.routes.support_tickets.broadcast_ticket_event", new_callable=AsyncMock):
            with patch("app.api.routes.support_tickets.SupportTicketNotificationService.notify_ticket_assigned", new_callable=AsyncMock):
                response = client.post(
                    f"/api/v1/support/tickets/{test_ticket.id}/assign",
                    headers={"Authorization": f"Bearer {support_token_beginner}"},
                    json={
                        "assigned_to_account_id": support_account_beginner.id,
                    },
                )
                assert response.status_code == 200
                data = response.json()
                assert data["assigned_to_account_id"] == support_account_beginner.id
                assert data["status"] == "in_progress"
    
    def test_assign_ticket_invalid_agent(self, support_db: Session, support_token_beginner, test_ticket):
        """Test assigning a ticket to an invalid agent."""
        response = client.post(
            f"/api/v1/support/tickets/{test_ticket.id}/assign",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
            json={
                "assigned_to_account_id": 99999,
            },
        )
        assert response.status_code == 400


class TestTicketEscalation:
    """Test ticket escalation operations."""
    
    def test_escalate_ticket(self, support_db: Session, support_token_beginner, test_ticket):
        """Test escalating a ticket."""
        with patch("app.api.routes.support_tickets.broadcast_ticket_event", new_callable=AsyncMock):
            with patch("app.api.routes.support_tickets.SupportTicketNotificationService.notify_ticket_escalated", new_callable=AsyncMock):
                response = client.post(
                    f"/api/v1/support/tickets/{test_ticket.id}/escalate",
                    headers={"Authorization": f"Bearer {support_token_beginner}"},
                    json={
                        "target_tier": "senior",
                        "escalation_reason": "Complex issue requiring senior support",
                    },
                )
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "escalated"
                assert data["support_tier_required"] == "senior"
                assert data["escalation_reason"] == "Complex issue requiring senior support"
    
    def test_escalate_ticket_same_tier(self, support_db: Session, support_token_beginner, test_ticket):
        """Test escalating a ticket to the same tier (should fail)."""
        response = client.post(
            f"/api/v1/support/tickets/{test_ticket.id}/escalate",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
            json={
                "target_tier": "beginner",
                "escalation_reason": "Test",
            },
        )
        assert response.status_code == 400


class TestTicketResolution:
    """Test ticket resolution operations."""
    
    def test_resolve_ticket(self, support_db: Session, support_token_beginner, test_ticket):
        """Test resolving a ticket."""
        with patch("app.api.routes.support_tickets.broadcast_ticket_event", new_callable=AsyncMock):
            with patch("app.api.routes.support_tickets.SupportTicketNotificationService.notify_ticket_resolved", new_callable=AsyncMock):
                response = client.post(
                    f"/api/v1/support/tickets/{test_ticket.id}/resolve",
                    headers={"Authorization": f"Bearer {support_token_beginner}"},
                    json={
                        "internal_notes": "Issue resolved successfully",
                    },
                )
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "resolved"
                assert data["resolved_at"] is not None


class TestAnalytics:
    """Test analytics endpoints."""
    
    def test_get_analytics(self, support_db: Session, support_token_beginner, test_ticket):
        """Test getting analytics."""
        response = client.get(
            "/api/v1/support/analytics",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_tickets" in data
        assert "open_tickets" in data
        assert "resolved_tickets" in data
        assert "tickets_by_priority" in data
        assert "tickets_by_category" in data
    
    def test_get_analytics_with_date_filter(self, support_db: Session, support_token_beginner, test_ticket):
        """Test getting analytics with date filtering."""
        date_from = (datetime.utcnow() - timedelta(days=7)).isoformat()
        date_to = datetime.utcnow().isoformat()
        
        response = client.get(
            "/api/v1/support/analytics",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
            params={
                "date_from": date_from,
                "date_to": date_to,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_tickets" in data


class TestCustomerContext:
    """Test customer context endpoints."""
    
    def test_get_customer_context(self, support_db: Session, support_token_beginner, test_ticket, test_user, test_facility, test_subscription, support_account_beginner):
        """Test getting customer context for a ticket."""
        # Update ticket to have user_id
        test_ticket.user_id = test_user.id
        test_ticket.facility_id = test_facility.id
        test_ticket.assigned_to_account_id = support_account_beginner.id
        support_db.commit()
        
        response = client.get(
            f"/api/v1/support/tickets/{test_ticket.id}/customer-context",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "facility" in data
        assert "subscription" in data
        assert data["user"]["email"] == test_user.email
        assert data["facility"]["facility_name"] == test_facility.facility_name
    
    def test_get_customer_history(self, support_db: Session, support_token_beginner, test_ticket, test_user, support_account_beginner):
        """Test getting customer ticket history."""
        # Update ticket to have user_id
        test_ticket.user_id = test_user.id
        test_ticket.assigned_to_account_id = support_account_beginner.id
        support_db.commit()
        
        response = client.get(
            f"/api/v1/support/tickets/{test_ticket.id}/customer-history",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the ticket creation event
        assert len(data) >= 1
        assert any(event["type"] == "ticket_created" for event in data)


class TestAgentManagement:
    """Test agent management operations."""
    
    def test_list_agents(self, support_db: Session, support_token_beginner, support_agent_profile):
        """Test listing all agents."""
        response = client.get(
            "/api/v1/support/agents",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_create_agent_profile(self, support_db: Session, support_token_senior, support_account_beginner):
        """Test creating an agent profile (requires senior role)."""
        response = client.post(
            "/api/v1/support/agents",
            headers={"Authorization": f"Bearer {support_token_senior}"},
            json={
                "account_id": support_account_beginner.id,
                "support_tier": "mid",
                "specialization_tags": ["technical", "billing"],
                "max_concurrent_tickets": 10,
                "is_active": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["support_tier"] == "mid"
        assert data["account_id"] == support_account_beginner.id
    
    def test_create_agent_profile_insufficient_permissions(self, support_db: Session, support_token_beginner, support_account_beginner):
        """Test creating an agent profile without sufficient permissions."""
        response = client.post(
            "/api/v1/support/agents",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
            json={
                "account_id": support_account_beginner.id,
                "support_tier": "mid",
                "specialization_tags": ["technical"],
                "max_concurrent_tickets": 10,
                "is_active": True,
            },
        )
        # Should fail because beginner doesn't have permission
        assert response.status_code == 403
    
    def test_update_agent_profile(self, support_db: Session, support_token_beginner, support_agent_profile):
        """Test updating an agent profile."""
        response = client.put(
            f"/api/v1/support/agents/{support_agent_profile.id}",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
            json={
                "support_tier": "mid",
                "max_concurrent_tickets": 15,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["support_tier"] == "mid"
        assert data["max_concurrent_tickets"] == 15


class TestWebSocketNotifications:
    """Test WebSocket notification functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, support_db: Session, support_token_beginner, support_account_beginner):
        """Test WebSocket connection establishment."""
        # Note: TestClient doesn't support WebSocket testing well
        # This is a placeholder for actual WebSocket tests
        # In a real scenario, you'd use a WebSocket test client
        pass
    
    def test_websocket_authentication_required(self):
        """Test that WebSocket requires authentication."""
        # WebSocket endpoint should require token
        # This would need a WebSocket test client to properly test
        pass


class TestTierPermissions:
    """Test tier-based permission system."""
    
    def test_beginner_cannot_handle_high_priority(self, support_db: Session, support_token_beginner, test_user):
        """Test that beginner agents cannot handle high priority tickets."""
        # Create a high priority ticket requiring senior tier
        ticket = SupportTicket(
            subject="High Priority Ticket",
            description="This requires senior support",
            category=TicketCategory.TECHNICAL,
            priority=TicketPriority.HIGH,
            support_tier_required=SupportTier.SENIOR,
            user_id=test_user.id if test_user else None,
            status=TicketStatus.OPEN,
        )
        support_db.add(ticket)
        support_db.commit()
        support_db.refresh(ticket)
        
        # Beginner should not be able to view this ticket
        response = client.get(
            f"/api/v1/support/tickets/{ticket.id}",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
        )
        assert response.status_code == 403
    
    def test_beginner_can_handle_low_priority(self, support_db: Session, support_token_beginner, test_user):
        """Test that beginner agents can handle low priority tickets."""
        # Create a low priority ticket
        ticket = SupportTicket(
            subject="Low Priority Ticket",
            description="This can be handled by beginner",
            category=TicketCategory.TECHNICAL,
            priority=TicketPriority.LOW,
            support_tier_required=SupportTier.BEGINNER,
            user_id=test_user.id if test_user else None,
            status=TicketStatus.OPEN,
        )
        support_db.add(ticket)
        support_db.commit()
        support_db.refresh(ticket)
        
        # Beginner should be able to view this ticket
        response = client.get(
            f"/api/v1/support/tickets/{ticket.id}",
            headers={"Authorization": f"Bearer {support_token_beginner}"},
        )
        assert response.status_code == 200

