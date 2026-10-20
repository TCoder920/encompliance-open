"""
OAuth Identity Model Module

This module defines the OAuthIdentity database model for the EnCompliance application.
It enables users to authenticate via third-party OAuth providers like Google and Apple.

Key functionalities:
- OAuth provider identity linking
- Multiple OAuth accounts per user
- OAuth token storage and refresh
- Provider-specific profile data storage
- User account federation

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
- JSON: For storing provider-specific data
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship
import enum

class OAuthProvider(enum.Enum):
    GOOGLE = "google"
    APPLE = "apple"
    MICROSOFT = "microsoft"
    GITHUB = "github"

class OAuthIdentity(Base):
    __tablename__ = "oauth_identities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)  # OAuth provider (google, apple, etc.)
    provider_user_id = Column(String, nullable=False)  # User ID from the provider
    email = Column(String, nullable=False)  # Email from the provider
    name = Column(String, nullable=True)  # Name from the provider
    
    # OAuth tokens - encrypt in production
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    id_token = Column(String, nullable=True)
    
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional provider-specific data as JSON
    profile_data = Column(JSON, nullable=True)
    
    # Relationship to user
    user = relationship("User", backref="oauth_identities")
    
    # Composite unique constraint to ensure one identity per provider+provider_user_id
    __table_args__ = (
        UniqueConstraint('provider', 'provider_user_id', name='uix_provider_provider_user_id'),
        {'sqlite_autoincrement': True}  # Needed for SQLite
    )
    
    def __repr__(self):
        return f"<OAuthIdentity(id={self.id}, user_id={self.user_id}, provider={self.provider})>" 