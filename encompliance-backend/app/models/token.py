"""
Token Model Module

This module defines the BlacklistedToken database model for the EnCompliance application.
It manages JWT token blacklisting for secure logout and token invalidation.

Key functionalities:
- JWT token blacklisting
- Token expiration tracking
- User-token relationships
- Automatic cleanup of expired tokens
- Indexed lookups for performance

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_jti = Column(String, index=True, unique=True, nullable=False)  # JWT ID field
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    blacklisted_on = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationship to the user
    user = relationship("User", backref="blacklisted_tokens")
    
    # Create an index for fast lookups
    __table_args__ = (
        Index('ix_blacklisted_tokens_token_jti_user_id', 'token_jti', 'user_id'),
    )

    def __repr__(self):
        return f"<BlacklistedToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>" 