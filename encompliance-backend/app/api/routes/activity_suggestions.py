"""
Description: API routes for managing activity suggestions.
Purpose: Provides endpoints for users to submit activity suggestions, vote on them, and for admins to review them.
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth.dependencies import get_current_active_user, require_facility_admin
from app.services.activity_suggestion_service import ActivitySuggestionService
from app.schemas.activity_suggestion import (
    ActivitySuggestion, 
    ActivitySuggestionCreate, 
    ActivitySuggestionUpdate,
    ActivitySuggestionReview,
    ActivitySuggestionVote,
    ActivitySuggestionVoteCreate
)
from typing import List
import os

router = APIRouter(prefix="/activity-suggestions", tags=["Activity Suggestions"])

@router.post("/", response_model=ActivitySuggestion, status_code=status.HTTP_201_CREATED)
def submit_activity_suggestion(
    suggestion_data: ActivitySuggestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit an activity suggestion for the user's facility.
    
    - **Requires**: Any authenticated user belonging to a facility.
    """
    if not current_user.facility_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not associated with a facility.")
    service = ActivitySuggestionService(db)
    suggestion = service.submit_suggestion(suggestion_data, current_user)
    return suggestion

@router.get("/", response_model=List[ActivitySuggestion])
def get_facility_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all activity suggestions for the user's facility.
    
    - **Requires**: Any authenticated user belonging to a facility.
    """
    if not current_user.facility_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not associated with a facility.")
    
    service = ActivitySuggestionService(db)
    suggestions = service.get_facility_suggestions(current_user.facility_id, current_user.id)
    return suggestions

@router.get("/all", response_model=List[ActivitySuggestion])
def get_all_suggestions(
    db: Session = Depends(get_db)
):
    """
    Get all activity suggestions (development endpoint).
    
    - **Note**: This is a development endpoint that shows all suggestions regardless of facility.
    - **Warning**: No authentication required for development testing.
    """
    # Only enable in development environment
    if os.getenv("ENVIRONMENT", "development") != "development":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not available")
    
    service = ActivitySuggestionService(db)
    suggestions = service.get_all_suggestions()
    return suggestions

@router.get("/my-suggestions", response_model=List[ActivitySuggestion])
def get_my_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all activity suggestions submitted by the current user.
    
    - **Requires**: Any authenticated user.
    """
    service = ActivitySuggestionService(db)
    suggestions = service.get_user_suggestions(current_user.id)
    return suggestions

@router.put("/{suggestion_id}", response_model=ActivitySuggestion)
def update_activity_suggestion(
    suggestion_id: int,
    update_data: ActivitySuggestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an activity suggestion.
    
    - **Requires**: Creator of the suggestion or facility administrator.
    """
    service = ActivitySuggestionService(db)
    suggestion = service.update_suggestion(suggestion_id, update_data, current_user)
    return suggestion

@router.delete("/{suggestion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an activity suggestion.
    
    - **Requires**: Creator of the suggestion or facility administrator.
    """
    service = ActivitySuggestionService(db)
    service.delete_suggestion(suggestion_id, current_user)
    return

@router.post("/{suggestion_id}/review", response_model=ActivitySuggestion)
def review_activity_suggestion(
    suggestion_id: int,
    review_data: ActivitySuggestionReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """
    Review (approve/reject) an activity suggestion.
    
    - **Requires**: Facility Administrator role.
    """
    service = ActivitySuggestionService(db)
    suggestion = service.review_suggestion(suggestion_id, review_data, current_user)
    return suggestion

@router.post("/{suggestion_id}/vote", response_model=ActivitySuggestionVote)
def vote_on_suggestion(
    suggestion_id: int,
    vote_data: ActivitySuggestionVoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Vote on an activity suggestion.
    
    - **Requires**: Any authenticated user in the same facility.
    - **Note**: Can only vote on pending suggestions.
    """
    service = ActivitySuggestionService(db)
    vote = service.vote_on_suggestion(suggestion_id, vote_data, current_user)
    return vote

@router.delete("/{suggestion_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
def remove_vote_from_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove your vote from an activity suggestion.
    
    - **Requires**: Any authenticated user.
    """
    service = ActivitySuggestionService(db)
    service.remove_vote(suggestion_id, current_user)
    return 