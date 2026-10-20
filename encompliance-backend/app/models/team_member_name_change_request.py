"""
Team Member Name Change Request Model Module

This module defines the TeamMemberNameChangeRequest database model for managing
name change requests from team members that require facility admin approval.

Key functionalities:
- Name change request tracking
- Admin approval workflow
- Audit trail for name changes
- Status management (pending, approved, rejected)

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
import enum


class NameChangeStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TeamMemberNameChangeRequest(Base):
    __tablename__ = "team_member_name_change_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Request details
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    current_name = Column(String(255), nullable=False)
    requested_name = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(String(20), nullable=False, default=NameChangeStatus.PENDING.value)
    
    # Admin review
    reviewed_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Metadata
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    reviewed_by_admin = relationship("User", foreign_keys=[reviewed_by_admin_id])
    
    @property
    def is_pending(self):
        """Check if request is pending approval."""
        return self.status == NameChangeStatus.PENDING.value
    
    @property
    def is_approved(self):
        """Check if request has been approved."""
        return self.status == NameChangeStatus.APPROVED.value
    
    @property
    def is_rejected(self):
        """Check if request has been rejected."""
        return self.status == NameChangeStatus.REJECTED.value
    
    def approve(self, admin_id, admin_notes=None):
        """Approve the name change request."""
        self.status = NameChangeStatus.APPROVED.value
        self.reviewed_by_admin_id = admin_id
        self.reviewed_at = datetime.now()
        self.admin_notes = admin_notes
    
    def reject(self, admin_id, admin_notes=None):
        """Reject the name change request."""
        self.status = NameChangeStatus.REJECTED.value
        self.reviewed_by_admin_id = admin_id
        self.reviewed_at = datetime.now()
        self.admin_notes = admin_notes
    
    def __repr__(self):
        return f"<TeamMemberNameChangeRequest(id={self.id}, user_id={self.user_id}, status={self.status})>" 