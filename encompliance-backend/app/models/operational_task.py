"""
Operational Task Model Module

This module defines the OperationalTask database model for tracking
facility operational tasks and chores with age-based assignment capabilities.

Key functionalities:
- Task creation and assignment to staff members
- Age-based assignment filtering
- Recurring and one-time task support
- Progress tracking and completion verification
- Due date management with reminder scheduling
- Facility-based task management

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling

Educational Note: Implements task management with age-based filtering for compliance
with child labor laws and facility safety requirements. References OSHA guidelines
for age-appropriate task assignment in childcare facilities.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class TaskType(enum.Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"

class TaskStatus(enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class RecurrencePattern(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class OperationalTask(Base):
    __tablename__ = "operational_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Task basic information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # cleaning, maintenance, safety, administrative
    
    # Task type and scheduling
    task_type = Column(String(20), default=TaskType.ONE_TIME.value)
    recurrence_pattern = Column(String(20), nullable=True)  # For recurring tasks
    recurrence_interval = Column(Integer, default=1)  # Every X days/weeks/months
    
    # Assignment and facility
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Age-based assignment criteria
    min_age_required = Column(Integer, nullable=True)  # Minimum age for assignment
    max_age_allowed = Column(Integer, nullable=True)  # Maximum age for assignment
    
    # Task details
    estimated_duration_minutes = Column(Integer, nullable=True)
    priority = Column(String(10), default=TaskPriority.MEDIUM.value)
    requires_supervision = Column(Boolean, default=False)
    special_instructions = Column(Text, nullable=True)
    
    # Location and equipment
    location = Column(String(255), nullable=True)  # Where task should be performed
    required_equipment = Column(JSON, nullable=True)  # List of required equipment
    
    # Photo requirements
    requires_before_photos = Column(Boolean, default=False)  # Photo requirements are optional
    requires_after_photos = Column(Boolean, default=False)   # Photo requirements are optional
    photo_instructions = Column(Text, nullable=True)        # Instructions for photo taking
    
    # Scheduling
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)  # For recurring tasks
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    facility = relationship("Facility", back_populates="operational_tasks")
    creator = relationship("User", foreign_keys=[created_by])
    task_assignments = relationship("TaskAssignment", back_populates="operational_task", cascade="all, delete-orphan")
    reference_images = relationship("TaskReferenceImage", back_populates="operational_task", cascade="all, delete-orphan")
    
    @property
    def is_recurring(self):
        """Check if this is a recurring task."""
        return self.task_type == TaskType.RECURRING.value
    
    @property
    def has_age_restrictions(self):
        """Check if task has age-based assignment restrictions."""
        return self.min_age_required is not None or self.max_age_allowed is not None
    
    @property
    def age_range_description(self):
        """Get human-readable age range description."""
        if not self.has_age_restrictions:
            return "All ages"
        
        if self.min_age_required and self.max_age_allowed:
            return f"Ages {self.min_age_required}-{self.max_age_allowed}"
        elif self.min_age_required:
            return f"Ages {self.min_age_required}+"
        elif self.max_age_allowed:
            return f"Ages up to {self.max_age_allowed}"
        
        return "All ages"
    
    def __repr__(self):
        return f"<OperationalTask(id={self.id}, title={self.title}, facility_id={self.facility_id})>" 