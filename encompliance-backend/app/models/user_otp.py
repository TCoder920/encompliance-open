"""
User OTP Model Module

This module defines the UserOTP database model for the EnCompliance application.
It enables one-time password authentication as an additional security factor.

Key functionalities:
- OTP code generation and storage
- Time-based expiration tracking
- Verification attempt tracking
- Support for email and SMS delivery channels
- Integration with multi-factor authentication workflows

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling and expiration
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
import enum
from sqlalchemy.orm import relationship

class OTPChannel(enum.Enum):
    EMAIL = "email"
    SMS = "sms"

class OTPPurpose(enum.Enum):
    LOGIN = "login"
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"
    MFA = "mfa"

class UserOTP(Base):
    __tablename__ = "user_otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    hashed_code = Column(String, nullable=False)  # Store hashed OTP, never plaintext
    created_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    attempt_count = Column(Integer, default=0)  # Track failed attempts
    channel = Column(Enum(OTPChannel), nullable=False)  # How was it sent
    purpose = Column(Enum(OTPPurpose), nullable=False)  # What is it for
    
    # Relationship to user
    user = relationship("User", backref="otps")
    
    @property
    def is_expired(self):
        """Check if the OTP is expired."""
        return datetime.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if the OTP is still valid (not used, not expired)."""
        return not self.is_used and not self.is_expired
    
    def __repr__(self):
        return f"<UserOTP(id={self.id}, user_id={self.user_id}, channel={self.channel}, purpose={self.purpose})>" 