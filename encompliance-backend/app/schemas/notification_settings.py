"""
Description: Pydantic schemas for notification settings operations.
Purpose: Provides data validation and serialization for user notification preferences.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationSettingsBase(BaseModel):
    """Base schema for notification settings."""
    # In-app notification settings
    in_app_calendar_enabled: bool = True
    in_app_calendar_reminders_enabled: bool = True
    in_app_note_notifications_enabled: bool = True
    in_app_message_notifications_enabled: bool = True
    in_app_regulatory_updates_enabled: bool = True
    in_app_system_notifications_enabled: bool = True
    
    # Email notification settings
    email_calendar_enabled: bool = False
    email_calendar_reminders_enabled: bool = True
    email_note_notifications_enabled: bool = False
    email_message_notifications_enabled: bool = True
    email_regulatory_updates_enabled: bool = True
    email_system_notifications_enabled: bool = True
    
    # Push notification settings
    push_enabled: bool = False
    push_calendar_enabled: bool = True
    push_calendar_reminders_enabled: bool = True
    push_note_notifications_enabled: bool = False
    push_message_notifications_enabled: bool = True
    push_regulatory_updates_enabled: bool = True
    push_system_notifications_enabled: bool = True
    
    # Calendar-specific settings
    calendar_reminder_offset_minutes: int = 15
    
    # Email digest settings
    email_digest_frequency: str = "daily"


class NotificationSettingsCreate(NotificationSettingsBase):
    """Schema for creating notification settings."""
    pass


class NotificationSettingsUpdate(BaseModel):
    """Schema for updating notification settings."""
    # In-app notification settings
    in_app_calendar_enabled: Optional[bool] = None
    in_app_calendar_reminders_enabled: Optional[bool] = None
    in_app_note_notifications_enabled: Optional[bool] = None
    in_app_message_notifications_enabled: Optional[bool] = None
    in_app_regulatory_updates_enabled: Optional[bool] = None
    in_app_system_notifications_enabled: Optional[bool] = None
    
    # Email notification settings
    email_calendar_enabled: Optional[bool] = None
    email_calendar_reminders_enabled: Optional[bool] = None
    email_note_notifications_enabled: Optional[bool] = None
    email_message_notifications_enabled: Optional[bool] = None
    email_regulatory_updates_enabled: Optional[bool] = None
    email_system_notifications_enabled: Optional[bool] = None
    
    # Push notification settings
    push_enabled: Optional[bool] = None
    push_calendar_enabled: Optional[bool] = None
    push_calendar_reminders_enabled: Optional[bool] = None
    push_note_notifications_enabled: Optional[bool] = None
    push_message_notifications_enabled: Optional[bool] = None
    push_regulatory_updates_enabled: Optional[bool] = None
    push_system_notifications_enabled: Optional[bool] = None
    
    # Calendar-specific settings
    calendar_reminder_offset_minutes: Optional[int] = None
    
    # Email digest settings
    email_digest_frequency: Optional[str] = None


class NotificationSettingsResponse(NotificationSettingsBase):
    """Schema for notification settings response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 