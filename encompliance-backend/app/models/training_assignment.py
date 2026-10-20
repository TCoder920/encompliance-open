"""
Training Assignment Model Module

This module defines the TrainingAssignment database model for tracking
staff training assignments and progress.

Key functionalities:
- Training assignment to staff members
- Progress tracking and completion status
- Due date management
- Completion verification
- Certificate generation
- Reminder scheduling
- Facility-based assignment management
- Admin assignment tracking

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class AssignmentStatus(enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class AssignmentPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TrainingAssignment(Base):
    __tablename__ = "training_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Assignment relationships
    training_program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    staff_member_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Facility management fields
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True, index=True)
    assigned_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Track facility admin assignments
    
    # Assignment details
    status = Column(String(20), default=AssignmentStatus.ASSIGNED.value)
    priority = Column(String(10), default=AssignmentPriority.MEDIUM.value)
    
    # Scheduling
    assigned_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=False)
    started_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    time_spent_minutes = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # Completion and verification
    completion_verified = Column(Boolean, default=False)
    verification_method = Column(String(50), nullable=True)  # quiz, assessment, supervisor_approval
    verification_score = Column(Integer, nullable=True)  # For quiz/assessment results
    verification_notes = Column(Text, nullable=True)
    
    # Reminders and notifications
    reminder_sent_dates = Column(JSON, nullable=True)  # Track when reminders were sent
    escalation_sent = Column(Boolean, default=False)
    
    # Notes and comments
    assignment_notes = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)
    
    # Training content URL
    training_url = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    training_program = relationship("TrainingProgram", back_populates="training_assignments")
    staff_member = relationship("StaffMember", back_populates="training_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])
    facility = relationship("Facility", back_populates="training_assignments")
    assigned_by_admin = relationship("User", foreign_keys=[assigned_by_admin_id])
    training_completion = relationship("TrainingCompletion", back_populates="training_assignment", uselist=False)
    
    @property
    def is_overdue(self):
        from datetime import datetime
        return self.due_date < datetime.now() and self.status != AssignmentStatus.COMPLETED.value
    
    @property
    def days_until_due(self):
        from datetime import datetime
        if self.due_date:
            delta = self.due_date - datetime.now()
            return delta.days
        return None
    
    @property
    def is_completed(self):
        return self.status == AssignmentStatus.COMPLETED.value
    
    @property
    def is_facility_assignment(self):
        """Check if this is a facility-wide assignment."""
        return self.facility_id is not None
    
    @property
    def assigned_by_facility_admin(self):
        """Check if assignment was created by facility admin."""
        return self.assigned_by_admin_id is not None
    
    def __repr__(self):
        return f"<TrainingAssignment(id={self.id}, program_id={self.training_program_id}, staff_id={self.staff_member_id}, status={self.status})>" 