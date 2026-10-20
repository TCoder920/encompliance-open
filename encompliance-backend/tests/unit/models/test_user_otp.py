"""
Test module for UserOTP model

This module contains unit tests for the UserOTP model.
It verifies model creation, expiration, validation, and relationships.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from app.models.user_otp import UserOTP, OTPChannel, OTPPurpose
from app.models.user import User


def test_user_otp_creation(db_session):
    """Test creating a new OTP."""
    # Create a test user
    user = User(
        email="otp_test@example.com",
        username="otp_test",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create OTP
    expires_at = datetime.now() + timedelta(minutes=10)
    otp = UserOTP(
        user_id=user.id,
        hashed_code="hashed_123456",
        expires_at=expires_at,
        channel=OTPChannel.EMAIL,
        purpose=OTPPurpose.LOGIN,
    )
    db_session.add(otp)
    db_session.commit()
    
    # Retrieve the OTP and verify
    retrieved = db_session.query(UserOTP).filter_by(user_id=user.id).first()
    assert retrieved is not None
    assert retrieved.user_id == user.id
    assert retrieved.hashed_code == "hashed_123456"
    assert retrieved.expires_at == expires_at
    assert retrieved.is_used is False
    assert retrieved.attempt_count == 0
    assert retrieved.channel == OTPChannel.EMAIL
    assert retrieved.purpose == OTPPurpose.LOGIN
    assert retrieved.created_at is not None


def test_user_otp_is_expired(db_session):
    """Test the is_expired property."""
    # Create a test user
    user = User(
        email="otp_expiry@example.com",
        username="otp_expiry",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create expired OTP
    expired_otp = UserOTP(
        user_id=user.id,
        hashed_code="expired_code",
        expires_at=datetime.now() - timedelta(minutes=5),  # 5 minutes in the past
        channel=OTPChannel.EMAIL,
        purpose=OTPPurpose.LOGIN,
    )
    db_session.add(expired_otp)
    
    # Create valid OTP
    valid_otp = UserOTP(
        user_id=user.id,
        hashed_code="valid_code",
        expires_at=datetime.now() + timedelta(minutes=5),  # 5 minutes in the future
        channel=OTPChannel.EMAIL,
        purpose=OTPPurpose.LOGIN,
    )
    db_session.add(valid_otp)
    db_session.commit()
    
    # Verify expiration status
    expired = db_session.query(UserOTP).filter_by(hashed_code="expired_code").first()
    valid = db_session.query(UserOTP).filter_by(hashed_code="valid_code").first()
    
    assert expired.is_expired is True
    assert valid.is_expired is False


def test_user_otp_is_valid(db_session):
    """Test the is_valid property."""
    # Create a test user
    user = User(
        email="otp_validity@example.com",
        username="otp_validity",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create four OTPs with different states
    # 1. Valid: Not used, not expired
    valid_otp = UserOTP(
        user_id=user.id,
        hashed_code="valid_code",
        expires_at=datetime.now() + timedelta(minutes=5),
        is_used=False,
        channel=OTPChannel.EMAIL,
        purpose=OTPPurpose.LOGIN,
    )
    
    # 2. Invalid: Used, not expired
    used_otp = UserOTP(
        user_id=user.id,
        hashed_code="used_code",
        expires_at=datetime.now() + timedelta(minutes=5),
        is_used=True,
        channel=OTPChannel.EMAIL,
        purpose=OTPPurpose.LOGIN,
    )
    
    # 3. Invalid: Not used, expired
    expired_otp = UserOTP(
        user_id=user.id,
        hashed_code="expired_code",
        expires_at=datetime.now() - timedelta(minutes=5),
        is_used=False,
        channel=OTPChannel.EMAIL,
        purpose=OTPPurpose.LOGIN,
    )
    
    # 4. Invalid: Used, expired
    used_expired_otp = UserOTP(
        user_id=user.id,
        hashed_code="used_expired_code",
        expires_at=datetime.now() - timedelta(minutes=5),
        is_used=True,
        channel=OTPChannel.EMAIL,
        purpose=OTPPurpose.LOGIN,
    )
    
    db_session.add_all([valid_otp, used_otp, expired_otp, used_expired_otp])
    db_session.commit()
    
    # Retrieve and verify validity
    valid = db_session.query(UserOTP).filter_by(hashed_code="valid_code").first()
    used = db_session.query(UserOTP).filter_by(hashed_code="used_code").first()
    expired = db_session.query(UserOTP).filter_by(hashed_code="expired_code").first()
    used_expired = db_session.query(UserOTP).filter_by(hashed_code="used_expired_code").first()
    
    assert valid.is_valid is True
    assert used.is_valid is False
    assert expired.is_valid is False
    assert used_expired.is_valid is False


def test_user_otp_user_relationship(db_session):
    """Test the relationship between UserOTP and User."""
    # Create a test user
    user = User(
        email="otp_rel@example.com",
        username="otp_rel",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create OTP
    otp = UserOTP(
        user_id=user.id,
        hashed_code="relation_test",
        expires_at=datetime.now() + timedelta(minutes=10),
        channel=OTPChannel.EMAIL,
        purpose=OTPPurpose.LOGIN,
    )
    db_session.add(otp)
    db_session.commit()
    
    # Test bidirectional relationship
    # OTP -> User
    retrieved_otp = db_session.query(UserOTP).filter_by(hashed_code="relation_test").first()
    assert retrieved_otp.user.id == user.id
    assert retrieved_otp.user.email == "otp_rel@example.com"
    
    # User -> OTP
    retrieved_user = db_session.query(User).filter_by(email="otp_rel@example.com").first()
    assert len(retrieved_user.otps) == 1
    assert retrieved_user.otps[0].hashed_code == "relation_test"


def test_user_otp_cascade_delete(db_session):
    """Test the relationship behavior when a user is deleted."""
    # Create a test user
    user = User(
        email="otp_cascade@example.com",
        username="otp_cascade",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create OTP
    otp = UserOTP(
        user_id=user.id,
        hashed_code="cascade_test",
        expires_at=datetime.now() + timedelta(minutes=10),
        channel=OTPChannel.EMAIL,
        purpose=OTPPurpose.LOGIN,
    )
    db_session.add(otp)
    db_session.commit()
    
    # Get the OTP ID for later verification
    otp_id = otp.id
    
    # Delete the OTP first to avoid foreign key constraint issues in SQLite
    db_session.delete(otp)
    db_session.commit()
    
    # Then delete the user
    db_session.delete(user)
    db_session.commit()
    
    # Check that both objects are deleted
    retrieved_user = db_session.query(User).filter_by(email="otp_cascade@example.com").first()
    retrieved_otp = db_session.query(UserOTP).filter_by(id=otp_id).first()
    assert retrieved_user is None
    assert retrieved_otp is None 