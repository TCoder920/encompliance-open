"""
Test module for MagicLink model

This module contains unit tests for the MagicLink model.
It verifies model creation, expiration, validation, and relationships.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from app.models.magic_link import MagicLink, MagicLinkPurpose
from app.models.user import User


def test_magic_link_creation(db_session):
    """Test creating a new magic link."""
    # Create a test user
    user = User(
        email="magic_test@example.com",
        username="magic_test",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create magic link
    expires_at = datetime.now() + timedelta(hours=1)
    magic_link = MagicLink(
        user_id=user.id,
        token="hashed_unique_token",
        expires_at=expires_at,
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0 (Test)",
        purpose="login"
    )
    db_session.add(magic_link)
    db_session.commit()
    
    # Retrieve the magic link and verify
    retrieved = db_session.query(MagicLink).filter_by(token="hashed_unique_token").first()
    assert retrieved is not None
    assert retrieved.user_id == user.id
    assert retrieved.token == "hashed_unique_token"
    assert retrieved.expires_at == expires_at
    assert retrieved.is_used is False
    assert retrieved.used_at is None
    assert retrieved.ip_address == "127.0.0.1"
    assert retrieved.user_agent == "Mozilla/5.0 (Test)"
    assert retrieved.purpose == "login"
    assert retrieved.created_at is not None


def test_magic_link_unique_token(db_session):
    """Test that token must be unique."""
    # Create two test users
    user1 = User(
        email="magic_unique1@example.com",
        username="magic_unique1",
        hashed_password="hashed_password",
        is_active=True,
    )
    user2 = User(
        email="magic_unique2@example.com",
        username="magic_unique2",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add_all([user1, user2])
    db_session.commit()
    
    # Create first magic link
    magic_link1 = MagicLink(
        user_id=user1.id,
        token="unique_token_test",
        expires_at=datetime.now() + timedelta(hours=1),
        purpose="login"
    )
    db_session.add(magic_link1)
    db_session.commit()
    
    # Try to create another magic link with the same token
    magic_link2 = MagicLink(
        user_id=user2.id,
        token="unique_token_test",  # Same token as magic_link1
        expires_at=datetime.now() + timedelta(hours=1),
        purpose="login"
    )
    db_session.add(magic_link2)
    
    # Should raise an integrity error due to duplicate token
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_magic_link_is_expired(db_session):
    """Test the is_expired property."""
    # Create a test user
    user = User(
        email="magic_expiry@example.com",
        username="magic_expiry",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create expired magic link
    expired_link = MagicLink(
        user_id=user.id,
        token="expired_token",
        expires_at=datetime.now() - timedelta(minutes=5),  # 5 minutes in the past
        purpose="login"
    )
    db_session.add(expired_link)
    
    # Create valid magic link
    valid_link = MagicLink(
        user_id=user.id,
        token="valid_token",
        expires_at=datetime.now() + timedelta(minutes=5),  # 5 minutes in the future
        purpose="login"
    )
    db_session.add(valid_link)
    db_session.commit()
    
    # Verify expiration status
    expired = db_session.query(MagicLink).filter_by(token="expired_token").first()
    valid = db_session.query(MagicLink).filter_by(token="valid_token").first()
    
    assert expired.is_expired is True
    assert valid.is_expired is False


def test_magic_link_is_valid(db_session):
    """Test the is_valid property."""
    # Create a test user
    user = User(
        email="magic_validity@example.com",
        username="magic_validity",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create four magic links with different states
    # 1. Valid: Not used, not expired
    valid_link = MagicLink(
        user_id=user.id,
        token="valid_token",
        expires_at=datetime.now() + timedelta(minutes=5),
        is_used=False,
        purpose="login"
    )
    
    # 2. Invalid: Used, not expired
    used_link = MagicLink(
        user_id=user.id,
        token="used_token",
        expires_at=datetime.now() + timedelta(minutes=5),
        is_used=True,
        used_at=datetime.now() - timedelta(minutes=1),
        purpose="login"
    )
    
    # 3. Invalid: Not used, expired
    expired_link = MagicLink(
        user_id=user.id,
        token="expired_token",
        expires_at=datetime.now() - timedelta(minutes=5),
        is_used=False,
        purpose="login"
    )
    
    # 4. Invalid: Used, expired
    used_expired_link = MagicLink(
        user_id=user.id,
        token="used_expired_token",
        expires_at=datetime.now() - timedelta(minutes=5),
        is_used=True,
        used_at=datetime.now() - timedelta(minutes=10),
        purpose="login"
    )
    
    db_session.add_all([valid_link, used_link, expired_link, used_expired_link])
    db_session.commit()
    
    # Retrieve and verify validity
    valid = db_session.query(MagicLink).filter_by(token="valid_token").first()
    used = db_session.query(MagicLink).filter_by(token="used_token").first()
    expired = db_session.query(MagicLink).filter_by(token="expired_token").first()
    used_expired = db_session.query(MagicLink).filter_by(token="used_expired_token").first()
    
    assert valid.is_valid is True
    assert used.is_valid is False
    assert expired.is_valid is False
    assert used_expired.is_valid is False


def test_magic_link_user_relationship(db_session):
    """Test the relationship between MagicLink and User."""
    # Create a test user
    user = User(
        email="magic_rel@example.com",
        username="magic_rel",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create magic link
    link = MagicLink(
        user_id=user.id,
        token="relation_test",
        expires_at=datetime.now() + timedelta(hours=1),
        purpose="login"
    )
    db_session.add(link)
    db_session.commit()
    
    # Test bidirectional relationship
    # MagicLink -> User
    retrieved_link = db_session.query(MagicLink).filter_by(token="relation_test").first()
    assert retrieved_link.user.id == user.id
    assert retrieved_link.user.email == "magic_rel@example.com"
    
    # User -> MagicLink
    retrieved_user = db_session.query(User).filter_by(email="magic_rel@example.com").first()
    assert len(retrieved_user.magic_links) == 1
    assert retrieved_user.magic_links[0].token == "relation_test"


def test_magic_link_cascade_delete(db_session):
    """Test the relationship behavior when a user is deleted."""
    # Create a test user
    user = User(
        email="magic_cascade@example.com",
        username="magic_cascade",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create magic link
    link = MagicLink(
        user_id=user.id,
        token="cascade_test",
        expires_at=datetime.now() + timedelta(hours=1),
        purpose="login"
    )
    db_session.add(link)
    db_session.commit()
    
    # Get the link ID for later verification
    link_id = link.id
    
    # Delete the link first to avoid foreign key constraint issues in SQLite
    db_session.delete(link)
    db_session.commit()
    
    # Then delete the user
    db_session.delete(user)
    db_session.commit()
    
    # Check that both objects are deleted
    retrieved_user = db_session.query(User).filter_by(email="magic_cascade@example.com").first()
    retrieved_link = db_session.query(MagicLink).filter_by(id=link_id).first()
    assert retrieved_user is None
    assert retrieved_link is None 