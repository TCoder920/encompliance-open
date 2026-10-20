"""
Training Completion Model Module

This module defines the TrainingCompletion database model for tracking
training completion records and certificate generation.

Key functionalities:
- Training completion tracking
- Certificate generation and storage
- Completion verification
- Renewal tracking
- Audit trail for compliance

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class CompletionStatus(enum.Enum):
    COMPLETED = "completed"
    VERIFIED = "verified"
    EXPIRED = "expired"
    REVOKED = "revoked"

class CertificateStatus(enum.Enum):
    PENDING = "pending"
    GENERATED = "generated"
    ISSUED = "issued"
    EXPIRED = "expired"
    REVOKED = "revoked"

class TrainingCompletion(Base):
    __tablename__ = "training_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Completion relationships
    training_assignment_id = Column(Integer, ForeignKey("training_assignments.id"), nullable=False, unique=True)
    staff_member_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False)
    training_program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    
    # Completion details
    completion_status = Column(String(20), default=CompletionStatus.COMPLETED.value)
    completed_date = Column(DateTime(timezone=True), nullable=False)
    completion_method = Column(String(50), nullable=True)  # online, in_person, hybrid
    
    # Verification details
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Assessment results
    final_score = Column(Integer, nullable=True)  # Final assessment score
    passing_score_required = Column(Integer, nullable=True)
    attempts_taken = Column(Integer, default=1)
    time_spent_minutes = Column(Integer, nullable=True)
    
    # Certificate information
    certificate_status = Column(String(20), default=CertificateStatus.PENDING.value)
    certificate_number = Column(String(100), nullable=True, unique=True)
    certificate_file_path = Column(String(500), nullable=True)
    certificate_issued_date = Column(DateTime(timezone=True), nullable=True)
    
    # Expiration and renewal
    expires_date = Column(DateTime(timezone=True), nullable=True)
    renewal_required = Column(Boolean, default=False)
    renewal_reminder_sent = Column(Boolean, default=False)
    
    # Compliance and audit
    compliance_notes = Column(Text, nullable=True)
    audit_trail = Column(JSON, nullable=True)  # Track all changes and verifications
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    training_assignment = relationship("TrainingAssignment", back_populates="training_completion")
    staff_member = relationship("StaffMember", back_populates="training_completions")
    training_program = relationship("TrainingProgram")
    verifier = relationship("User", foreign_keys=[verified_by])
    
    @property
    def is_expired(self):
        from datetime import datetime
        return self.expires_date and self.expires_date < datetime.now()
    
    @property
    def days_until_expiry(self):
        from datetime import datetime
        if self.expires_date:
            delta = self.expires_date - datetime.now()
            return delta.days
        return None
    
    @property
    def is_certificate_valid(self):
        return (self.certificate_status == CertificateStatus.ISSUED.value and 
                not self.is_expired and 
                self.completion_status != CompletionStatus.REVOKED.value)
    
    @property
    def needs_renewal_reminder(self):
        if not self.expires_date or self.renewal_reminder_sent:
            return False
        days_until_expiry = self.days_until_expiry
        return days_until_expiry is not None and days_until_expiry <= 30
    
    def __repr__(self):
        return f"<TrainingCompletion(id={self.id}, staff_id={self.staff_member_id}, program_id={self.training_program_id}, status={self.completion_status})>" 