"""
Description: Notification settings model for storing user notification preferences.
Purpose: Enables users to control which notifications they receive and how they receive them.
"""
from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, String, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class NotificationSettings(Base):
    """SQLAlchemy model for user notification settings."""
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # In-app notification settings
    in_app_calendar_enabled = Column(Boolean, default=True)
    in_app_calendar_reminders_enabled = Column(Boolean, default=True)
    in_app_note_notifications_enabled = Column(Boolean, default=True)
    in_app_message_notifications_enabled = Column(Boolean, default=True)
    in_app_regulatory_updates_enabled = Column(Boolean, default=True)
    in_app_system_notifications_enabled = Column(Boolean, default=True)
    in_app_training_enabled = Column(Boolean, default=True)
    
    # Email notification settings
    email_calendar_enabled = Column(Boolean, default=False)
    email_calendar_reminders_enabled = Column(Boolean, default=True)
    email_note_notifications_enabled = Column(Boolean, default=False)
    email_message_notifications_enabled = Column(Boolean, default=True)
    email_regulatory_updates_enabled = Column(Boolean, default=True)
    email_system_notifications_enabled = Column(Boolean, default=True)
    email_training_enabled = Column(Boolean, default=True)
    
    # Push notification settings
    push_enabled = Column(Boolean, default=False)
    push_calendar_enabled = Column(Boolean, default=True)
    push_calendar_reminders_enabled = Column(Boolean, default=True)
    push_note_notifications_enabled = Column(Boolean, default=False)
    push_message_notifications_enabled = Column(Boolean, default=True)
    push_regulatory_updates_enabled = Column(Boolean, default=True)
    push_system_notifications_enabled = Column(Boolean, default=True)
    
    # Training-specific push notification settings
    push_training_assignments_enabled = Column(Boolean, default=True)
    push_training_reminders_enabled = Column(Boolean, default=True)
    push_training_due_enabled = Column(Boolean, default=True)
    push_certification_expiring_enabled = Column(Boolean, default=True)
    push_training_completed_enabled = Column(Boolean, default=True)
    
    # Calendar-specific settings
    calendar_reminder_offset_minutes = Column(Integer, default=15)  # Default 15 minutes before event
    
    # Training reminder timing settings
    training_reminder_days = Column(JSON, default=[30, 14, 7, 1])  # Days before due date
    certification_expiry_reminder_days = Column(JSON, default=[60, 30, 14, 7, 1])
    
    # Document expiration notification settings for Pro Mode
    document_expiration_reminders_enabled = Column(Boolean, default=True)
    document_expiration_reminder_days = Column(JSON, default=[30, 14, 7, 1])
    
    # Facility task notification settings
    facility_task_reminders_enabled = Column(Boolean, default=True)
    facility_task_reminder_days = Column(JSON, default=[7, 3, 1])
    task_overdue_notifications_enabled = Column(Boolean, default=True)
    
    # Facility digest settings
    facility_daily_digest_enabled = Column(Boolean, default=True)
    facility_weekly_digest_enabled = Column(Boolean, default=True)
    
    # Email digest settings
    email_digest_frequency = Column(String(20), default="daily")  # daily, weekly, never
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notification_settings")

    def __repr__(self):
        return f"<NotificationSettings(id={self.id}, user_id={self.user_id})>" 