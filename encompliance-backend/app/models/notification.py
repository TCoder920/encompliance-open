"""
Description: Notification model for storing user notifications.
Purpose: Enables the system to track and display notifications for various events.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class NotificationType(enum.Enum):
    """Enum for notification types."""
    NOTE = "note"
    DOCUMENT = "document"
    SYSTEM = "system"
    SECURITY = "security"
    SUBSCRIPTION = "subscription"
    CALENDAR = "calendar"
    CALENDAR_REMINDER = "calendar_reminder"
    MESSAGE = "message"
    REGULATORY_UPDATE = "regulatory_update"
    # Training-specific notification types
    TRAINING_ASSIGNED = "training_assigned"
    TRAINING_DUE = "training_due"
    TRAINING_OVERDUE = "training_overdue"
    TRAINING_COMPLETED = "training_completed"
    CERTIFICATION_EXPIRING = "certification_expiring"
    CERTIFICATION_EXPIRED = "certification_expired"
    TRAINING_REMINDER = "training_reminder"
    STAFF_TRAINING_UPDATE = "staff_training_update"
    # Facility-specific notification types
    CALENDAR_EVENT_CREATED = "calendar_event_created"
    FACILITY_INVITATION = "facility_invitation"
    FACILITY_JOINED = "facility_joined"
    FACILITY_UPDATE = "facility_update"
    USER_REMOVED = "user_removed"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    # Document expiration notification types
    DOCUMENT_EXPIRING = "document_expiring"
    DOCUMENT_EXPIRED = "document_expired"
    DOCUMENT_RENEWAL_REQUIRED = "document_renewal_required"
    # Scheduled task notification types
    TASK_DUE = "task_due"
    TASK_OVERDUE = "task_overdue"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    FACILITY_DIGEST = "facility_digest"
    ESCALATION = "escalation"
    # Support ticket notification types
    SUPPORT_TICKET_CREATED = "support_ticket_created"
    SUPPORT_TICKET_ASSIGNED = "support_ticket_assigned"
    SUPPORT_TICKET_UPDATED = "support_ticket_updated"
    SUPPORT_TICKET_COMMENT = "support_ticket_comment"
    SUPPORT_TICKET_ESCALATED = "support_ticket_escalated"
    SUPPORT_TICKET_RESOLVED = "support_ticket_resolved"


class NotificationPriority(enum.Enum):
    """Enum for notification priorities."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Notification(Base):
    """SQLAlchemy model for notifications."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # User who triggered notification
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(25), nullable=False)  # Increased length to accommodate training types
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Optional fields for linking to related objects
    related_id = Column(String(100), nullable=True)  # ID of related object (document, event, etc.)
    related_type = Column(String(50), nullable=True)  # Type of related object
    related_entity_id = Column(Integer, nullable=True)  # Generic foreign key for linking to specific records
    action_url = Column(String(255), nullable=True)  # URL for action button
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    sender = relationship("User", foreign_keys=[sender_id])

    @property
    def is_from_admin(self):
        """Check if notification is from a facility administrator."""
        return self.sender and self.sender.is_pro_user
    
    @property
    def is_facility_notification(self):
        """Check if this is a facility-related notification."""
        facility_types = [
            NotificationType.TRAINING_ASSIGNED.value,
            NotificationType.CALENDAR_EVENT_CREATED.value,
            NotificationType.FACILITY_INVITATION.value,
            NotificationType.FACILITY_JOINED.value,
            NotificationType.FACILITY_UPDATE.value,
            NotificationType.USER_REMOVED.value,
            NotificationType.SUBSCRIPTION_UPDATED.value
        ]
        return self.type in facility_types

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, title={self.title})>" 