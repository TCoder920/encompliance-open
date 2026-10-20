"""
Description: Pydantic schemas for Notification objects.
Purpose: Defines data validation and serialization for Notification objects in the API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime, timezone
from enum import Enum


class NotificationType(str, Enum):
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


class NotificationPriority(str, Enum):
    """Enum for notification priority levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class NotificationBase(BaseModel):
    """Base schema for Notification objects."""
    title: str = Field(..., min_length=1, max_length=255)
    message: str
    type: NotificationType = NotificationType.SYSTEM
    priority: NotificationPriority = NotificationPriority.MEDIUM
    related_id: Optional[Union[int, str]] = None
    related_type: Optional[str] = None
    action_url: Optional[str] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a new Notification."""
    pass


class NotificationUpdate(BaseModel):
    """Schema for updating an existing Notification."""
    is_read: Optional[bool] = None


class NotificationInDB(NotificationBase):
    """Schema for Notification as stored in the database."""
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z') if dt.tzinfo is None 
                                else dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        }


class Notification(NotificationInDB):
    """Schema for Notification responses."""
    pass


class NotificationList(BaseModel):
    """Schema for a list of Notifications."""
    notifications: List[Notification]
    total: int
    unread_count: int 