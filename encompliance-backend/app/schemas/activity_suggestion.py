"""
Description: Pydantic schemas for activity suggestions.
Purpose: Define data structures for submitting and representing activity suggestions.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.activity_suggestion import ActivitySuggestionStatus

class ActivitySuggestionCreate(BaseModel):
    """Schema for creating a new activity suggestion. Used for request body validation."""
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    suggested_date: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = None

class ActivitySuggestionUpdate(BaseModel):
    """Schema for updating an activity suggestion."""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    suggested_date: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = None

class ActivitySuggestionReview(BaseModel):
    """Schema for admin review of activity suggestions."""
    status: ActivitySuggestionStatus
    admin_response: Optional[str] = None

class ActivitySuggestionVoteCreate(BaseModel):
    """Schema for creating a vote on an activity suggestion."""
    vote_type: str  # 'upvote' or 'downvote'

class UserSummary(BaseModel):
    """Summary schema for user information."""
    id: int
    full_name: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)

class ActivitySuggestionVote(BaseModel):
    """Schema for representing a vote on an activity suggestion."""
    id: int
    suggestion_id: int
    user_id: int
    vote_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ActivitySuggestion(ActivitySuggestionCreate):
    """Schema for representing an activity suggestion. Used for API responses."""
    id: int
    facility_id: int
    suggested_by_user_id: int
    status: ActivitySuggestionStatus
    admin_response: Optional[str] = None
    reviewed_by_admin_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    suggested_by_user: Optional[UserSummary] = None
    reviewed_by_admin: Optional[UserSummary] = None
    votes: Optional[List[ActivitySuggestionVote]] = []
    
    # Vote counts
    upvote_count: Optional[int] = 0
    downvote_count: Optional[int] = 0
    total_votes: Optional[int] = 0
    user_vote: Optional[str] = None  # Current user's vote if any

    model_config = ConfigDict(from_attributes=True) 