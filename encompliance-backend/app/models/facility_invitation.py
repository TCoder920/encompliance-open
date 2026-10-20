"""
Facility Invitation Model Module

This module defines the FacilityInvitation database model for managing user invitations to facilities.
It tracks invitation codes, usage, and expiration for secure facility user registration.

Key functionalities:
- Invitation code generation and validation
- Usage tracking and limits
- Expiration management
- Email-based invitation system
- Security and audit trail

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
- uuid: For secure invitation code generation
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime, timedelta
import uuid
import enum


class InvitationStatus(enum.Enum):
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class FacilityInvitation(Base):
    __tablename__ = "facility_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Invitation details
    invitation_code = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=True, index=True)  # Optional: specific email invitation
    
    # Facility relationship
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Usage tracking
    status = Column(String(20), nullable=False, default=InvitationStatus.PENDING.value)
    used_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Expiration management
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Optional invitation details
    personal_message = Column(Text, nullable=True)
    role_description = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    facility = relationship("Facility", back_populates="invitations")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    used_by = relationship("User", foreign_keys=[used_by_user_id])
    
    @classmethod
    def generate_invitation_code(cls):
        """Generate a secure invitation code."""
        return str(uuid.uuid4()).replace('-', '').upper()[:16]
    
    @classmethod
    def create_invitation(cls, facility_id, created_by_user_id, email=None, expires_in_days=7, personal_message=None):
        """Create a new facility invitation."""
        invitation = cls(
            invitation_code=cls.generate_invitation_code(),
            facility_id=facility_id,
            created_by_user_id=created_by_user_id,
            email=email,
            expires_at=datetime.now() + timedelta(days=expires_in_days),
            personal_message=personal_message
        )
        return invitation
    
    @property
    def is_valid(self):
        """Check if invitation is valid and can be used."""
        return (
            self.status == InvitationStatus.PENDING.value and
            self.expires_at > datetime.now()
        )
    
    @property
    def is_expired(self):
        """Check if invitation has expired."""
        return datetime.now() > self.expires_at
    
    @property
    def days_until_expiry(self):
        """Get days until invitation expires."""
        if self.expires_at:
            delta = self.expires_at - datetime.now()
            return max(0, delta.days)
        return 0
    
    def mark_as_used(self, user_id):
        """Mark invitation as used by a specific user."""
        self.status = InvitationStatus.USED.value
        self.used_by_user_id = user_id
        self.used_at = datetime.now()
    
    def cancel(self):
        """Cancel the invitation."""
        self.status = InvitationStatus.CANCELLED.value
    
    def __repr__(self):
        return f"<FacilityInvitation(id={self.id}, code={self.invitation_code}, facility_id={self.facility_id}, status={self.status})>" 