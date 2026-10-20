"""
WebAuthn Credential Model Module

This module defines the WebAuthnCredential database model for the EnCompliance application.
It stores passkey (WebAuthn) credentials for users, enabling passwordless authentication.

Key functionalities:
- Storing WebAuthn credential IDs and public keys
- User-credential relationship management
- Credential metadata tracking
- Enabling secure passkey (WebAuthn) authentication
- Supporting multi-factor authentication flows

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, LargeBinary, Text
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class WebAuthnCredential(Base):
    __tablename__ = "webauthn_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    credential_id = Column(String, unique=True, nullable=False)  # Base64URL-encoded credential ID
    public_key = Column(LargeBinary, nullable=False)  # Raw public key bytes
    
    # Credential metadata
    sign_count = Column(Integer, nullable=False, default=0)
    name = Column(String, nullable=True)  # User-friendly name for the credential
    device_type = Column(String, nullable=True)  # Platform or cross-platform
    
    # Registration metadata
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship to user
    user = relationship("User", backref="webauthn_credentials")
    
    def __repr__(self):
        return f"<WebAuthnCredential(id={self.id}, user_id={self.user_id}, name={self.name})>" 