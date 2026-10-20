"""
Description: Pydantic schemas for activity signups.
Purpose: Define data structures for creating and representing activity registrations.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.activity_signup import ActivitySignupStatus

class ActivitySignupCreate(BaseModel):
    """Schema for creating a new activity signup. Used for request body validation."""
    calendar_event_id: str
    notes: Optional[str] = None

class ActivitySignup(ActivitySignupCreate):
    """Schema for representing an activity signup. Used for API responses."""
    id: int
    user_id: int
    status: ActivitySignupStatus
    created_at: datetime
    
    class Config:
        orm_mode = True 