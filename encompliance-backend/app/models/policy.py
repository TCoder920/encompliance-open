"""
Policy Model Module

This module defines the Policy database model for managing organizational policies
that require staff acknowledgment and compliance tracking.

Key functionalities:
- Policy document management
- Version control and effective dates
- Acknowledgment requirement configuration
- Facility-specific policy management
- Integration with document storage

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class PolicyCategory(enum.Enum):
    SAFETY = "safety"
    HR = "hr"
    OPERATIONS = "operations"
    COMPLIANCE = "compliance"
    TRAINING = "training"
    SECURITY = "security"
    QUALITY = "quality"
    EMERGENCY = "emergency"

class PolicyStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"

class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # PolicyCategory enum values
    
    # Document reference
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    document_url = Column(String(500), nullable=True)
    content_summary = Column(Text, nullable=True)  # Brief summary for quick reference
    
    # Version management
    version = Column(String(50), nullable=False, default="1.0")
    effective_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    supersedes_policy_id = Column(Integer, ForeignKey("policies.id"), nullable=True)
    
    # Acknowledgment requirements
    requires_acknowledgment = Column(Boolean, default=True)
    acknowledgment_deadline_days = Column(Integer, default=30)
    auto_assign_new_staff = Column(Boolean, default=False)
    acknowledgment_reminder_days = Column(String(100), default="[30, 14, 7, 1]")  # JSON array as string
    
    # Compliance and regulatory
    regulatory_reference = Column(String(255), nullable=True)  # Reference to specific regulation
    compliance_level = Column(String(50), default="mandatory")  # mandatory, recommended, optional
    
    # Status and metadata
    status = Column(String(20), default=PolicyStatus.DRAFT.value)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    facility_administrator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_date = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", foreign_keys=[document_id])
    creator = relationship("User", foreign_keys=[created_by])
    facility_administrator = relationship("User", foreign_keys=[facility_administrator_id])
    approver = relationship("User", foreign_keys=[approved_by])
    superseded_policy = relationship("Policy", remote_side=[id], foreign_keys=[supersedes_policy_id])
    
    # Back references
    policy_assignments = relationship("PolicyAssignment", back_populates="policy", cascade="all, delete-orphan")
    policy_acknowledgments = relationship("PolicyAcknowledgment", back_populates="policy", cascade="all, delete-orphan")
    
    @property
    def is_expired(self):
        from datetime import datetime
        return self.expiry_date and self.expiry_date < datetime.now()
    
    @property
    def is_effective(self):
        from datetime import datetime
        now = datetime.now()
        return (self.effective_date <= now and 
                (not self.expiry_date or self.expiry_date > now) and
                self.status == PolicyStatus.ACTIVE.value)
    
    @property
    def days_until_expiry(self):
        from datetime import datetime
        if self.expiry_date:
            delta = self.expiry_date - datetime.now()
            return delta.days
        return None
    
    def __repr__(self):
        return f"<Policy(id={self.id}, title={self.title}, version={self.version}, status={self.status})>" 