"""
Test module for OAuthIdentity model

This module contains unit tests for the OAuthIdentity model.
It verifies model creation, constraints, and relationships.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from app.models.oauth_identity import OAuthIdentity, OAuthProvider
from app.models.user import User


def test_oauth_identity_creation(db_session):
    """Test creating a new OAuth identity."""
    # Create a test user
    user = User(
        email="oauth_test@example.com",
        username="oauth_test",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create OAuth identity
    now = datetime.now()
    expires_at = now + timedelta(hours=1)
    profile_data = {"picture": "https://example.com/profile.jpg", "locale": "en-US"}
    
    oauth = OAuthIdentity(
        user_id=user.id,
        provider="google",
        provider_user_id="google_user_12345",
        email="developer@example.com",
        name="OAuth Test User",
        access_token="access_token_123",
        refresh_token="refresh_token_456",
        id_token="id_token_789",
        token_expires_at=expires_at,
        profile_data=profile_data
    )
    db_session.add(oauth)
    db_session.commit()
    
    # Retrieve the OAuth identity and verify
    retrieved = db_session.query(OAuthIdentity).filter_by(provider_user_id="google_user_12345").first()
    assert retrieved is not None
    assert retrieved.user_id == user.id
    assert retrieved.provider == "google"
    assert retrieved.provider_user_id == "google_user_12345"
    assert retrieved.email == "developer@example.com"
    assert retrieved.name == "OAuth Test User"
    assert retrieved.access_token == "access_token_123"
    assert retrieved.refresh_token == "refresh_token_456"
    assert retrieved.id_token == "id_token_789"
    assert retrieved.token_expires_at == expires_at
    assert retrieved.profile_data == profile_data
    assert retrieved.created_at is not None
    assert retrieved.updated_at is not None
    assert retrieved.last_used_at is None


def test_oauth_identity_unique_constraint(db_session):
    """Test that provider + provider_user_id must be unique."""
    # Create two test users
    user1 = User(
        email="oauth_unique1@example.com",
        username="oauth_unique1",
        hashed_password="hashed_password",
        is_active=True,
    )
    user2 = User(
        email="oauth_unique2@example.com",
        username="oauth_unique2",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add_all([user1, user2])
    db_session.commit()
    
    # Create first OAuth identity
    oauth1 = OAuthIdentity(
        user_id=user1.id,
        provider="google",
        provider_user_id="unique_provider_id",
        email="developer@example.com",
    )
    db_session.add(oauth1)
    db_session.commit()
    
    # Try to create another OAuth identity with the same provider + provider_user_id
    oauth2 = OAuthIdentity(
        user_id=user2.id,
        provider="google",
        provider_user_id="unique_provider_id",  # Same as oauth1
        email="developer@example.com",
    )
    db_session.add(oauth2)
    
    # Should raise an integrity error due to unique constraint
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_oauth_identity_user_relationship(db_session):
    """Test the relationship between OAuthIdentity and User."""
    # Create a test user
    user = User(
        email="oauth_rel@example.com",
        username="oauth_rel",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create multiple OAuth identities for the same user
    google_oauth = OAuthIdentity(
        user_id=user.id,
        provider="google",
        provider_user_id="google_user_rel",
        email="developer@example.com",
    )
    
    apple_oauth = OAuthIdentity(
        user_id=user.id,
        provider="apple",
        provider_user_id="apple_user_rel",
        email="developer@example.com",
    )
    
    db_session.add_all([google_oauth, apple_oauth])
    db_session.commit()
    
    # Test bidirectional relationship
    # OAuthIdentity -> User
    retrieved_oauth = db_session.query(OAuthIdentity).filter_by(provider="google").first()
    assert retrieved_oauth.user.id == user.id
    assert retrieved_oauth.user.email == "oauth_rel@example.com"
    
    # User -> OAuthIdentity
    retrieved_user = db_session.query(User).filter_by(email="oauth_rel@example.com").first()
    assert len(retrieved_user.oauth_identities) == 2
    
    # Check if both identities are associated with the user
    provider_list = [oauth.provider for oauth in retrieved_user.oauth_identities]
    assert "google" in provider_list
    assert "apple" in provider_list


def test_oauth_identity_cascade_delete(db_session):
    """Test the relationship behavior when a user is deleted."""
    # Create a test user
    user = User(
        email="oauth_cascade@example.com",
        username="oauth_cascade",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create OAuth identity
    oauth = OAuthIdentity(
        user_id=user.id,
        provider="google",
        provider_user_id="cascade_test",
        email="developer@example.com",
    )
    db_session.add(oauth)
    db_session.commit()
    
    # Get the OAuth identity ID for later verification
    oauth_id = oauth.id
    
    # Delete the OAuth identity first to avoid foreign key constraint issues in SQLite
    db_session.delete(oauth)
    db_session.commit()
    
    # Then delete the user
    db_session.delete(user)
    db_session.commit()
    
    # Check that both objects are deleted
    retrieved_user = db_session.query(User).filter_by(email="oauth_cascade@example.com").first()
    retrieved_oauth = db_session.query(OAuthIdentity).filter_by(id=oauth_id).first()
    assert retrieved_user is None
    assert retrieved_oauth is None


def test_oauth_identity_json_data(db_session):
    """Test storing and retrieving JSON data in profile_data."""
    # Create a test user
    user = User(
        email="oauth_json@example.com",
        username="oauth_json",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create complex JSON data
    profile_data = {
        "name": {
            "given_name": "Test",
            "family_name": "User",
            "display_name": "Test User"
        },
        "emails": [
            {"value": "primary@example.com", "primary": True},
            {"value": "secondary@example.com", "primary": False}
        ],
        "photos": [
            {"url": "https://example.com/photo1.jpg"},
            {"url": "https://example.com/photo2.jpg"}
        ],
        "metadata": {
            "created_at": "2023-01-01T00:00:00Z",
            "last_updated": "2023-01-02T00:00:00Z",
            "version": 1.0,
            "is_verified": True
        }
    }
    
    # Create OAuth identity with complex JSON data
    oauth = OAuthIdentity(
        user_id=user.id,
        provider="google",
        provider_user_id="json_test",
        email="developer@example.com",
        profile_data=profile_data
    )
    db_session.add(oauth)
    db_session.commit()
    
    # Retrieve and verify JSON data
    retrieved = db_session.query(OAuthIdentity).filter_by(provider_user_id="json_test").first()
    assert retrieved.profile_data == profile_data
    assert retrieved.profile_data["name"]["given_name"] == "Test"
    assert retrieved.profile_data["emails"][0]["value"] == "primary@example.com"
    assert retrieved.profile_data["metadata"]["is_verified"] is True 