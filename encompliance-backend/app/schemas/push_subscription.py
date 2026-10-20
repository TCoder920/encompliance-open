"""
Description: Pydantic schemas for push subscription operations.
Purpose: Provides data validation and serialization for push notification subscriptions.
"""
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime


class PushSubscriptionKeys(BaseModel):
    """Schema for push subscription keys."""
    p256dh: str
    auth: str


class PushSubscriptionCreate(BaseModel):
    """Schema for creating a push subscription."""
    endpoint: str
    keys: PushSubscriptionKeys


class PushSubscriptionResponse(BaseModel):
    """Schema for push subscription response."""
    id: int
    user_id: int
    endpoint: str
    keys: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class PushSubscriptionDelete(BaseModel):
    """Schema for deleting a push subscription."""
    endpoint: str 