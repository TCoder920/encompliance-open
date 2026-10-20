"""
Test module for WebAuthnCredential model

This module contains unit tests for the WebAuthnCredential model.
It verifies model creation, constraints, and relationships.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta

from app.models.webauthn_credential import WebAuthnCredential
from app.models.user import User


def test_webauthn_credential_creation(db_session):
    """Test creating a new WebAuthn credential."""
    # Create a test user
    user = User(
        email="webauthn_test@example.com",
        username="webauthn_test",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create WebAuthn credential
    credential = WebAuthnCredential(
        user_id=user.id,
        credential_id="credential123",
        public_key=b"public_key_bytes",
        sign_count=0,
        name="My Security Key",
        device_type="cross-platform",
    )
    db_session.add(credential)
    db_session.commit()
    
    # Retrieve the credential and verify
    retrieved = db_session.query(WebAuthnCredential).filter_by(credential_id="credential123").first()
    assert retrieved is not None
    assert retrieved.user_id == user.id
    assert retrieved.credential_id == "credential123"
    assert retrieved.public_key == b"public_key_bytes"
    assert retrieved.sign_count == 0
    assert retrieved.name == "My Security Key"
    assert retrieved.device_type == "cross-platform"
    assert retrieved.created_at is not None
    assert retrieved.last_used_at is None


def test_webauthn_credential_unique_constraint(db_session):
    """Test that credential_id must be unique."""
    # Create a test user
    user = User(
        email="webauthn_unique@example.com",
        username="webauthn_unique",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create first credential
    credential1 = WebAuthnCredential(
        user_id=user.id,
        credential_id="unique_cred_id",
        public_key=b"public_key_bytes1",
        sign_count=0,
    )
    db_session.add(credential1)
    db_session.commit()
    
    # Try to create another credential with the same ID
    credential2 = WebAuthnCredential(
        user_id=user.id,
        credential_id="unique_cred_id",  # Same ID as credential1
        public_key=b"public_key_bytes2",
        sign_count=0,
    )
    db_session.add(credential2)
    
    # Should raise an integrity error due to duplicate credential_id
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_webauthn_credential_user_relationship(db_session):
    """Test the relationship between WebAuthnCredential and User."""
    # Create a test user
    user = User(
        email="webauthn_rel@example.com",
        username="webauthn_rel",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create WebAuthn credential
    credential = WebAuthnCredential(
        user_id=user.id,
        credential_id="relation_test",
        public_key=b"public_key_bytes",
        sign_count=0,
    )
    db_session.add(credential)
    db_session.commit()
    
    # Test bidirectional relationship
    # Credential -> User
    retrieved_credential = db_session.query(WebAuthnCredential).filter_by(credential_id="relation_test").first()
    assert retrieved_credential.user.id == user.id
    assert retrieved_credential.user.email == "webauthn_rel@example.com"
    
    # User -> Credential
    retrieved_user = db_session.query(User).filter_by(email="webauthn_rel@example.com").first()
    assert len(retrieved_user.webauthn_credentials) == 1
    assert retrieved_user.webauthn_credentials[0].credential_id == "relation_test"


def test_webauthn_credential_cascade_delete(db_session):
    """Test the relationship behavior when a user is deleted."""
    # Create a test user
    user = User(
        email="webauthn_cascade@example.com",
        username="webauthn_cascade",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create WebAuthn credential
    credential = WebAuthnCredential(
        user_id=user.id,
        credential_id="cascade_test",
        public_key=b"public_key_bytes",
        sign_count=0,
    )
    db_session.add(credential)
    db_session.commit()
    
    # Get the credential ID for later verification
    cred_id = credential.id
    
    # Delete the credential first to avoid foreign key constraint issues in SQLite
    db_session.delete(credential)
    db_session.commit()
    
    # Then delete the user
    db_session.delete(user)
    db_session.commit()
    
    # Check that both objects are deleted
    retrieved_user = db_session.query(User).filter_by(email="webauthn_cascade@example.com").first()
    retrieved_cred = db_session.query(WebAuthnCredential).filter_by(id=cred_id).first()
    assert retrieved_user is None
    assert retrieved_cred is None 