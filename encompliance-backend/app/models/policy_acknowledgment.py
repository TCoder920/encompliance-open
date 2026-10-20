"""
Policy Acknowledgment Model Module

This module defines the PolicyAcknowledment database model for tracking
staff acknowledgments of organizational policies.

Key functionalities:
- Policy acknowledgment tracking
- Digital signature capture
- Audit trail for compliance
- IP address and device tracking
- Acknowledgment verification

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class AcknowledgmentMethod(enum.Enum):
    DIGITAL_SIGNATURE = "digital_signature"
    CHECKBOX_CONFIRMATION = "checkbox_confirmation"
    VERBAL_CONFIRMATION = "verbal_confirmation"
    WRITTEN_SIGNATURE = "written_signature"

class AcknowledgmentStatus(enum.Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    OVERDUE = "overdue"
    EXPIRED = "expired"

class PolicyAcknowledgment(Base):
    __tablename__ = "policy_acknowledgments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relationships
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    staff_member_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False)
    policy_assignment_id = Column(Integer, ForeignKey("policy_assignments.id"), nullable=True)
    
    # Acknowledgment details
    acknowledged_date = Column(DateTime(timezone=True), nullable=True)
    acknowledgment_method = Column(String(50), default=AcknowledgmentMethod.DIGITAL_SIGNATURE.value)
    status = Column(String(20), default=AcknowledgmentStatus.PENDING.value)
    
    # Digital signature and verification
    digital_signature = Column(Text, nullable=True)  # Base64 encoded signature image
    signature_metadata = Column(JSON, nullable=True)  # Signature capture metadata
    
    # Audit trail
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    geolocation = Column(JSON, nullable=True)  # Optional location data
    
    # Verification and compliance
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    is_current = Column(Boolean, default=True)  # False if superseded by newer policy version
    
    # Additional context
    acknowledgment_text = Column(Text, nullable=True)  # What the staff member acknowledged
    witness_name = Column(String(255), nullable=True)  # For verbal confirmations
    witness_signature = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Compliance tracking
    compliance_score = Column(Integer, nullable=True)  # Optional scoring system
    requires_reacknowledgment = Column(Boolean, default=False)
    reacknowledgment_reason = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    policy = relationship("Policy", back_populates="policy_acknowledgments")
    staff_member = relationship("StaffMember", back_populates="policy_acknowledgments")
    policy_assignment = relationship("PolicyAssignment", back_populates="acknowledgment")
    verifier = relationship("User", foreign_keys=[verified_by])
    
    @property
    def is_overdue(self):
        from datetime import datetime
        if self.status == AcknowledgmentStatus.ACKNOWLEDGED.value:
            return False
        if self.policy_assignment and self.policy_assignment.due_date:
            return self.policy_assignment.due_date < datetime.now()
        return False
    
    @property
    def days_overdue(self):
        from datetime import datetime
        if not self.is_overdue:
            return 0
        if self.policy_assignment and self.policy_assignment.due_date:
            delta = datetime.now() - self.policy_assignment.due_date
            return delta.days
        return 0
    
    @property
    def is_verified(self):
        return self.verified_by is not None and self.verification_date is not None
    
    def __repr__(self):
        return f"<PolicyAcknowledgment(id={self.id}, policy_id={self.policy_id}, staff_id={self.staff_member_id}, status={self.status})>" 