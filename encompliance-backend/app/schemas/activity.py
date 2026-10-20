"""
Description: Pydantic schemas for facility activities.
Purpose: Define the data structures for creating and representing activities in API requests and responses.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ActivityCreate(BaseModel):
    """Schema for creating a new activity. Used for request body validation."""
    title: str
    description: Optional[str] = None
    start: str # ISO datetime string
    end: str   # ISO datetime string
    location: Optional[str] = None
    all_day: bool = False
    activity_category: Optional[str] = None
    requires_signup: bool = False
    max_participants: Optional[int] = None
    signup_deadline: Optional[datetime] = None

class Activity(ActivityCreate):
    """Schema for representing an activity. Used for API responses."""
    id: str
    facility_id: int
    created_by_admin: bool
    activity_status: str
    current_participants: int

    class Config:
        orm_mode = True 