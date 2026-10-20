"""
Policy Assignment Model Module

This module defines the PolicyAssignment database model for tracking
policy assignments to staff members and managing the assignment lifecycle.

Key functionalities:
- Policy assignment to staff members
- Due date management
- Reminder and escalation tracking
- Assignment status tracking
- Bulk assignment support

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class PolicyAssignmentStatus(enum.Enum):
    ASSIGNED = "assigned"
    ACKNOWLEDGED = "acknowledged"
    OVERDUE = "overdue"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class PolicyAssignmentPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class PolicyAssignment(Base):
    __tablename__ = "policy_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Assignment relationships
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    staff_member_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Assignment details
    status = Column(String(20), default=PolicyAssignmentStatus.ASSIGNED.value)
    priority = Column(String(10), default=PolicyAssignmentPriority.MEDIUM.value)
    
    # Scheduling
    assigned_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=False)
    acknowledged_date = Column(DateTime(timezone=True), nullable=True)
    
    # Assignment context
    assignment_reason = Column(String(255), nullable=True)  # new_hire, policy_update, compliance_review, etc.
    custom_message = Column(Text, nullable=True)  # Custom message to staff member
    requires_immediate_attention = Column(Boolean, default=False)
    
    # Reminders and notifications
    reminder_sent_dates = Column(JSON, nullable=True)  # Track when reminders were sent
    escalation_sent = Column(Boolean, default=False)
    escalation_date = Column(DateTime(timezone=True), nullable=True)
    escalation_recipient = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Progress tracking
    viewed_date = Column(DateTime(timezone=True), nullable=True)  # When staff first viewed the policy
    time_spent_reading = Column(Integer, nullable=True)  # Minutes spent reading policy
    
    # Notes and comments
    assignment_notes = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)  # Internal notes for administrators
    
    # Compliance tracking
    is_mandatory = Column(Boolean, default=True)
    compliance_deadline = Column(DateTime(timezone=True), nullable=True)  # Different from due_date for regulatory compliance
    regulatory_requirement = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    policy = relationship("Policy", back_populates="policy_assignments")
    staff_member = relationship("StaffMember", back_populates="policy_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])
    escalation_user = relationship("User", foreign_keys=[escalation_recipient])
    acknowledgment = relationship("PolicyAcknowledgment", back_populates="policy_assignment", uselist=False)
    
    @property
    def is_overdue(self):
        from datetime import datetime
        return (self.status != PolicyAssignmentStatus.ACKNOWLEDGED.value and 
                self.due_date < datetime.now())
    
    @property
    def days_until_due(self):
        from datetime import datetime
        if self.status == PolicyAssignmentStatus.ACKNOWLEDGED.value:
            return None
        delta = self.due_date - datetime.now()
        return delta.days
    
    @property
    def days_overdue(self):
        from datetime import datetime
        if not self.is_overdue:
            return 0
        delta = datetime.now() - self.due_date
        return delta.days
    
    @property
    def is_acknowledged(self):
        return self.status == PolicyAssignmentStatus.ACKNOWLEDGED.value
    
    @property
    def needs_reminder(self):
        from datetime import datetime
        if self.is_acknowledged or self.is_overdue:
            return False
        
        # Check if reminder should be sent based on days until due
        days_until_due = self.days_until_due
        if days_until_due is None:
            return False
            
        # Default reminder schedule: 7, 3, 1 days before due
        reminder_schedule = [7, 3, 1]
        return days_until_due in reminder_schedule
    
    def __repr__(self):
        return f"<PolicyAssignment(id={self.id}, policy_id={self.policy_id}, staff_id={self.staff_member_id}, status={self.status})>" 