"""
Task Assignment Model Module

This module defines the TaskAssignment database model for tracking
individual task assignments to staff members with completion verification.

Key functionalities:
- Task assignment to staff members
- Progress tracking and completion status
- Due date management with overdue detection
- Completion verification with photo evidence
- Time tracking and performance metrics
- Status management and escalation

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling

Educational Note: Implements task assignment tracking with completion verification
for operational accountability. Supports photo evidence collection for task
completion verification following facility management best practices.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class TaskAssignmentStatus(enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class TaskAssignmentPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskAssignment(Base):
    __tablename__ = "task_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Assignment relationships
    operational_task_id = Column(Integer, ForeignKey("operational_tasks.id"), nullable=False)
    staff_member_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Assignment details
    status = Column(String(20), default=TaskAssignmentStatus.ASSIGNED.value)
    priority = Column(String(10), default=TaskAssignmentPriority.MEDIUM.value)
    
    # Scheduling
    assigned_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=False)
    started_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    time_spent_minutes = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # Completion verification
    completion_verified = Column(Boolean, default=False)
    verification_notes = Column(Text, nullable=True)
    completion_photo_url = Column(String(500), nullable=True)  # Photo evidence
    verification_method = Column(String(50), nullable=True)  # photo, supervisor_approval, self_reported
    
    # Reminders and notifications
    reminder_sent_dates = Column(JSON, nullable=True)  # Track when reminders were sent
    escalation_sent = Column(Boolean, default=False)
    escalation_date = Column(DateTime(timezone=True), nullable=True)
    
    # Notes and comments
    assignment_notes = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)
    supervisor_notes = Column(Text, nullable=True)
    
    # Quality and performance tracking
    quality_rating = Column(Integer, nullable=True)  # 1-5 rating scale
    efficiency_rating = Column(Integer, nullable=True)  # 1-5 rating scale
    requires_followup = Column(Boolean, default=False)
    
    # Photo requirements and tracking
    requires_before_photos = Column(Boolean, default=False)
    requires_after_photos = Column(Boolean, default=False)
    min_before_photos = Column(Integer, default=0)
    min_after_photos = Column(Integer, default=0)
    max_photos_per_type = Column(Integer, default=50)
    photo_requirements = Column(JSON, nullable=True)
    total_image_storage_bytes = Column(BigInteger, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    operational_task = relationship("OperationalTask", back_populates="task_assignments")
    staff_member = relationship("StaffMember", back_populates="task_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])
    images = relationship("AssignmentImage", back_populates="assignment", cascade="all, delete-orphan")
    
    @property
    def is_overdue(self):
        """Check if task assignment is overdue."""
        from datetime import datetime
        return (self.due_date < datetime.now() and 
                self.status != TaskAssignmentStatus.COMPLETED.value)
    
    @property
    def days_until_due(self):
        """Calculate days until due date."""
        from datetime import datetime
        if self.due_date:
            delta = self.due_date - datetime.now()
            return delta.days
        return None
    
    @property
    def days_overdue(self):
        """Calculate days overdue if applicable."""
        from datetime import datetime
        if not self.is_overdue:
            return 0
        delta = datetime.now() - self.due_date
        return delta.days
    
    @property
    def is_completed(self):
        """Check if task is completed."""
        return self.status == TaskAssignmentStatus.COMPLETED.value
    
    @property
    def is_in_progress(self):
        """Check if task is currently in progress."""
        return self.status == TaskAssignmentStatus.IN_PROGRESS.value
    
    @property
    def completion_time_minutes(self):
        """Calculate total completion time in minutes."""
        if self.completed_date and self.started_date:
            delta = self.completed_date - self.started_date
            return int(delta.total_seconds() / 60)
        return self.time_spent_minutes
    
    @property
    def has_photo_verification(self):
        """Check if task has photo verification."""
        return self.completion_photo_url is not None
    
    def __repr__(self):
        return f"<TaskAssignment(id={self.id}, task_id={self.operational_task_id}, staff_id={self.staff_member_id}, status={self.status})>" 