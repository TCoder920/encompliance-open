"""
WebAuthn Authentication Tests
-----------------------------
This module tests the WebAuthn (passkey) authentication implementation for the EnCompliance system.
It tests:
- WebAuthn registration options generation
- WebAuthn registration verification
- WebAuthn authentication options generation
- WebAuthn authentication verification
- Credential management
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app
from app.models.user import User, MFAMethod
from app.models.webauthn_credential import WebAuthnCredential
from app.auth.webauthn_utils import WebAuthnManager
from app.auth.dependencies import get_current_user

client = TestClient(app)

@pytest.fixture
def mock_db_session(monkeypatch):
    """Create a mock database session."""
    from app.main import app
    from app.database import get_db
    
    mock_session = MagicMock()
    
    def mock_get_db():
        yield mock_session
    
    # Override the get_db dependency
    app.dependency_overrides[get_db] = mock_get_db
    
    yield mock_session
    
    # Clean up
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def authenticated_headers():
    """Create headers for an authenticated user."""
    # In a real test, you'd use a valid token. For this test, we'll mock the authentication.
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def mock_current_user(monkeypatch):
    """Mock the current authenticated user."""
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True
    )
    return user

@pytest.fixture(autouse=True)
def override_dependency(mock_current_user):
    """Override FastAPI dependency to bypass JWT auth in tests."""
    from app.main import app
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def mock_webauthn_manager(monkeypatch):
    """Mock the WebAuthnManager for testing."""
    # Create a mock for the WebAuthnManager
    mock_manager = MagicMock()
    
    # Mock the static methods that will be called
    monkeypatch.setattr(WebAuthnManager, "generate_registration_options_for_user", 
                        lambda db, user, credential_name, authenticator_attachment: 
                        {"challenge": "test_challenge", "rp": {"id": "localhost", "name": "EnCompliance"}})
    
    monkeypatch.setattr(WebAuthnManager, "verify_registration_response_and_save_credential",
                        lambda db, user, credential_data, credential_name, device_type:
                        WebAuthnCredential(id=1, user_id=user.id, credential_id="test_credential_id",
                                         name=credential_name, device_type=device_type, 
                                         created_at=datetime(2023, 1, 1), public_key=b"test_key", sign_count=0))
    
    monkeypatch.setattr(WebAuthnManager, "generate_authentication_options",
                        lambda db, user_id, user_verification:
                        {"challenge": "test_challenge", "rpId": "localhost"})
    
    monkeypatch.setattr(WebAuthnManager, "verify_authentication_response",
                        lambda db, user_id, credential_data:
                        (True, WebAuthnCredential(id=1, user_id=1, credential_id="test_credential_id")))
    
    return mock_manager

def test_webauthn_register_options(mock_db_session, mock_current_user, authenticated_headers, mock_webauthn_manager):
    """Test getting WebAuthn registration options."""
    # Test request
    response = client.post(
        "/api/v1/webauthn/register/options",
        headers=authenticated_headers,
        json={"credential_name": "Test Passkey"}
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "options" in data
    assert "user_id" in data
    assert data["options"]["challenge"] == "test_challenge"
    assert data["user_id"] == mock_current_user.id

def test_webauthn_register_verify(mock_db_session, mock_current_user, authenticated_headers, mock_webauthn_manager):
    """Test verifying WebAuthn registration."""
    # Test request
    response = client.post(
        "/api/v1/webauthn/register/verify",
        headers=authenticated_headers,
        json={
            "credential": {"id": "test_credential_id", "rawId": "test_raw_id", "response": {}},
            "credential_name": "Test Passkey",
            "device_type": "platform"
        }
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Passkey"
    assert "created_at" in data
    assert data["device_type"] == "platform"
    assert data["message"] == "Registration successful"

def test_webauthn_authenticate_options(mock_db_session, mock_webauthn_manager):
    """Test getting WebAuthn authentication options."""
    # Set up mock DB query
    mock_user = User(id=1, username="testuser", email="test@example.com")
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
    
    # Test request with email
    response = client.post(
        "/api/v1/webauthn/authenticate/options",
        json={"email": "test@example.com"}
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "options" in data
    assert "user_id" in data
    assert data["options"]["challenge"] == "test_challenge"
    assert data["user_id"] == 1

def test_webauthn_authenticate_verify(mock_db_session, mock_webauthn_manager):
    """Test verifying WebAuthn authentication."""
    # Set up mock DB query
    mock_user = User(id=1, username="testuser", email="test@example.com")
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
    
    # Test request
    response = client.post(
        "/api/v1/webauthn/authenticate/verify",
        json={
            "credential": {"id": "test_credential_id", "rawId": "test_raw_id", "response": {}},
            "user_id": 1
        }
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"] == 1
    assert data["username"] == "testuser"

def test_get_credentials(mock_db_session, mock_current_user, authenticated_headers):
    """Test getting user's WebAuthn credentials."""
    # Set up mock DB query chain properly
    mock_credentials = [
        WebAuthnCredential(id=1, user_id=mock_current_user.id, credential_id="cred1", name="Passkey 1", 
                         created_at=datetime(2023, 1, 1), last_used_at=datetime(2023, 1, 2), device_type="platform"),
        WebAuthnCredential(id=2, user_id=mock_current_user.id, credential_id="cred2", name="Passkey 2", 
                         created_at=datetime(2023, 1, 3), last_used_at=None, device_type="cross-platform")
    ]
    
    # Create proper query chain mock
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.all.return_value = mock_credentials
    mock_db_session.query.return_value = mock_query
    
    # Test request
    response = client.get(
        "/api/v1/webauthn/credentials",
        headers=authenticated_headers
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["name"] == "Passkey 1"
    assert data[1]["id"] == 2
    assert data[1]["name"] == "Passkey 2"
    assert "last_used_at" in data[0]
    assert data[1]["last_used_at"] is None or "last_used_at" not in data[1]

def test_delete_credential(mock_db_session, mock_current_user, authenticated_headers):
    """Test deleting a WebAuthn credential."""
    # Set up mock DB query chain properly
    mock_credential = WebAuthnCredential(
        id=1, 
        user_id=mock_current_user.id, 
        credential_id="cred1", 
        name="Passkey 1",
        device_type="platform"
    )
    
    # Mock the user's preferred_mfa_method to avoid enum issues
    mock_current_user.preferred_mfa_method = MFAMethod.NONE
    
    # Create proper query chain mocks
    # First query: find credential to delete
    mock_query1 = MagicMock()
    mock_filter1 = MagicMock()
    mock_query1.filter.return_value = mock_filter1
    mock_filter1.first.return_value = mock_credential
    
    # Second query: count remaining credentials
    mock_query2 = MagicMock()
    mock_filter2 = MagicMock()
    mock_query2.filter.return_value = mock_filter2
    mock_filter2.count.return_value = 0
    
    # Make query() return different mocks for different calls
    call_count = [0]
    def query_side_effect(model):
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_query1
        else:
            return mock_query2
    
    mock_db_session.query.side_effect = query_side_effect
    
    # Test request
    response = client.delete(
        "/api/v1/webauthn/credentials/1",
        headers=authenticated_headers
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Credential deleted successfully"
    mock_db_session.delete.assert_called_once_with(mock_credential)
    mock_db_session.commit.assert_called()

def test_delete_credential_not_found(mock_db_session, mock_current_user, authenticated_headers):
    """Test deleting a WebAuthn credential that doesn't exist or belong to the user."""
    # Set up mock DB query chain to return None (credential not found)
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    mock_db_session.query.return_value = mock_query
    
    # Test request
    response = client.delete(
        "/api/v1/webauthn/credentials/999",
        headers=authenticated_headers
    )
    
    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower() 
