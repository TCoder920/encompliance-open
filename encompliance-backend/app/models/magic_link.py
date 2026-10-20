"""
Magic Link Model Module

This module defines the MagicLink database model for the EnCompliance application.
It enables passwordless authentication via one-time use links sent to users' emails.

Key functionalities:
- Secure token generation and storage
- Time-based expiration tracking
- User identity verification via email
- Single-use link enforcement
- Easy integration with email delivery systems

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling and expiration
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship
import enum

class MagicLinkPurpose(enum.Enum):
    LOGIN = "login"
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"

class MagicLink(Base):
    __tablename__ = "magic_links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, index=True, unique=True, nullable=False)  # Store hashed token
    created_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String, nullable=True)  # IP address of requester
    user_agent = Column(Text, nullable=True)  # User agent of requester
    purpose = Column(String, nullable=False, default="login")
    
    # Relationship to user
    user = relationship("User", backref="magic_links")
    
    @property
    def is_expired(self):
        """Check if the magic link is expired."""
        return datetime.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if the magic link is still valid (not used, not expired)."""
        return not self.is_used and not self.is_expired
    
    def __repr__(self):
        return f"<MagicLink(id={self.id}, user_id={self.user_id}, purpose={self.purpose})>" 