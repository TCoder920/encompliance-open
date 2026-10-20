"""
OTP Model Module

This module defines the OTP (One-Time Password) model for the EnCompliance application.
It handles storage and management of OTP tokens for email/SMS verification.

Key functionalities:
- OTP generation and storage
- Expiry time tracking
- Verification attempt tracking
- OTP type classification (email, SMS)
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime, timezone
import enum

class OTPType(enum.Enum):
    EMAIL = "email"
    SMS = "sms"

class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for session-based OTPs
    otp_type = Column(Enum(OTPType), nullable=False)
    otp_hash = Column(String, nullable=False)  # Store hashed OTP, not plaintext
    recipient = Column(String, nullable=False)  # Email or phone number
    is_verified = Column(Boolean, default=False)
    verification_attempts = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    def is_expired(self) -> bool:
        """Check if the OTP has expired"""
        # Ensure we compare timezone-aware datetimes if expires_at is aware
        now = datetime.now(timezone.utc)
        if self.expires_at.tzinfo is None:
            # If expires_at represents UTC but is naive, make it aware
            return now > self.expires_at.replace(tzinfo=timezone.utc)
        return now > self.expires_at
    
    def increase_attempt(self) -> int:
        """Increase verification attempt count"""
        self.verification_attempts += 1
        return self.verification_attempts
    
    def __repr__(self):
        return f"<OTP(id={self.id}, user_id={self.user_id}, type={self.otp_type.value}, expires_at={self.expires_at})>" 