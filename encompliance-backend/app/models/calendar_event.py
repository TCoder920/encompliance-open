"""
Description: Calendar event model for storing user calendar events.
Purpose: Provides persistent storage for calendar events with user association and reminder tracking.
Educational Note: Implements SQLAlchemy ORM pattern for calendar data persistence.
Reference: SQLAlchemy documentation - https://docs.sqlalchemy.org/en/20/orm/
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CalendarEvent(Base):
    """SQLAlchemy model for calendar events."""
    __tablename__ = "calendar_events"

    id = Column(String(36), primary_key=True, index=True)  # UUID string
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    start = Column(String(50), nullable=False)  # ISO datetime string
    end = Column(String(50), nullable=False)    # ISO datetime string
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    all_day = Column(Boolean, default=False, nullable=False)
    
    # Facility management fields
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True, index=True)
    created_by_admin = Column(Boolean, default=False, nullable=False)  # True if created by facility admin
    is_editable_by_user = Column(Boolean, default=True, nullable=False)  # False for admin-only events
    
    # External calendar integration fields
    external_calendar_id = Column(String(255), nullable=True)  # Google/Apple event ID
    external_calendar_provider = Column(String(50), nullable=True)  # 'google' or 'apple'
    sync_status = Column(String(50), default='local', nullable=False)  # 'synced', 'pending', 'error', 'local'
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    
    # Task integration fields
    operational_task_id = Column(Integer, ForeignKey("operational_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    task_assignment_id = Column(Integer, ForeignKey("task_assignments.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Training integration fields
    training_program_id = Column(Integer, ForeignKey("training_programs.id", ondelete="CASCADE"), nullable=True, index=True)
    training_assignment_id = Column(Integer, ForeignKey("training_assignments.id", ondelete="CASCADE"), nullable=True, index=True)
    training_completion_id = Column(Integer, ForeignKey("training_completions.id", ondelete="CASCADE"), nullable=True, index=True)
    
    event_type = Column(String(50), default='general', nullable=False)  # 'general', 'task', 'assignment', 'training_assignment', 'certification_renewal', 'training_deadline', 'facility_activity'
    
    # New fields for facility activities
    activity_category = Column(String(100), nullable=True) # e.g., 'wellness', 'training', 'meeting'
    requires_signup = Column(Boolean, default=False, nullable=False)
    max_participants = Column(Integer, nullable=True)
    signup_deadline = Column(DateTime(timezone=True), nullable=True)
    activity_status = Column(String(50), default='planned', nullable=False) # e.g., 'planned', 'active', 'completed', 'cancelled'
    
    # Reminder tracking fields
    reminder_sent = Column(Boolean, default=False, nullable=False)
    start_notification_sent = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="calendar_events")
    facility = relationship("Facility", back_populates="calendar_events")
    operational_task = relationship("OperationalTask", foreign_keys=[operational_task_id])
    task_assignment = relationship("TaskAssignment", foreign_keys=[task_assignment_id])
    training_program = relationship("TrainingProgram", foreign_keys=[training_program_id])
    training_assignment = relationship("TrainingAssignment", foreign_keys=[training_assignment_id])
    training_completion = relationship("TrainingCompletion", foreign_keys=[training_completion_id])
    
    # Relationship for activity signups
    signups = relationship("ActivitySignup", back_populates="calendar_event", cascade="all, delete-orphan")

    @property
    def is_facility_event(self):
        """Check if this is a facility-wide event."""
        return self.facility_id is not None
    
    @property
    def is_admin_created(self):
        """Check if event was created by facility admin."""
        return self.created_by_admin
    
    @property
    def can_user_edit(self):
        """Check if regular users can edit this event."""
        return self.is_editable_by_user and not self.created_by_admin

    @property
    def current_participants(self):
        """Calculate current number of participants who have signed up."""
        if not self.requires_signup:
            return 0
        return len(self.signups)

    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title={self.title}, user_id={self.user_id})>"

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start,
            "end": self.end,
            "description": self.description,
            "location": self.location,
            "allDay": self.all_day,
            "facilityId": self.facility_id,
            "createdByAdmin": self.created_by_admin,
            "isEditableByUser": self.is_editable_by_user,
            "externalCalendarId": self.external_calendar_id,
            "externalCalendarProvider": self.external_calendar_provider,
            "syncStatus": self.sync_status,
            "lastSyncedAt": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "operationalTaskId": self.operational_task_id,
            "taskAssignmentId": self.task_assignment_id,
            "trainingProgramId": self.training_program_id,
            "trainingAssignmentId": self.training_assignment_id,
            "trainingCompletionId": self.training_completion_id,
            "eventType": self.event_type,
            "activityCategory": self.activity_category,
            "requiresSignup": self.requires_signup,
            "maxParticipants": self.max_participants,
            "currentParticipants": self.current_participants,
            "signupDeadline": self.signup_deadline.isoformat() if self.signup_deadline else None,
            "activityStatus": self.activity_status,
        } 