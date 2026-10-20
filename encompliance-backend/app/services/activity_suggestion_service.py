"""
Description: Service layer for managing user-submitted activity suggestions.
Purpose: Encapsulates the business logic for submitting and retrieving activity suggestions.
Key functionalities: submit_suggestion, get_facility_suggestions, get_user_suggestions, get_all_suggestions, voting, admin review
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case
from app.models import ActivitySuggestion, ActivitySuggestionVote, User
from app.schemas.activity_suggestion import (
    ActivitySuggestionCreate, 
    ActivitySuggestionUpdate, 
    ActivitySuggestionReview,
    ActivitySuggestionVoteCreate
)
from app.models.activity_suggestion import ActivitySuggestionStatus
from typing import List, Optional
from fastapi import HTTPException, status
from datetime import datetime

class ActivitySuggestionService:
    """
    Handles business logic related to activity suggestions from users.
    """
    def __init__(self, db: Session):
        self.db = db

    def submit_suggestion(self, suggestion_data: ActivitySuggestionCreate, user: User) -> ActivitySuggestion:
        """
        Allows a user to submit an activity suggestion for their facility.
        The suggestion is automatically linked to the user and their associated facility.
        """
        new_suggestion = ActivitySuggestion(
            **suggestion_data.dict(),
            suggested_by_user_id=user.id,
            facility_id=user.facility_id
        )
        self.db.add(new_suggestion)
        self.db.commit()
        self.db.refresh(new_suggestion)
        return new_suggestion

    def get_facility_suggestions(self, facility_id: int, current_user_id: Optional[int] = None) -> List[ActivitySuggestion]:
        """
        Retrieves all activity suggestions for a specific facility with vote counts and user's vote.
        """
        query = self.db.query(ActivitySuggestion).options(
            joinedload(ActivitySuggestion.suggested_by_user),
            joinedload(ActivitySuggestion.reviewed_by_admin),
            joinedload(ActivitySuggestion.votes)
        ).filter(ActivitySuggestion.facility_id == facility_id)
        
        suggestions = query.all()
        return self._enrich_suggestions_with_vote_data(suggestions, current_user_id)

    def get_user_suggestions(self, user_id: int) -> List[ActivitySuggestion]:
        """
        Retrieves all activity suggestions submitted by a specific user.
        """
        query = self.db.query(ActivitySuggestion).options(
            joinedload(ActivitySuggestion.suggested_by_user),
            joinedload(ActivitySuggestion.reviewed_by_admin),
            joinedload(ActivitySuggestion.votes)
        ).filter(ActivitySuggestion.suggested_by_user_id == user_id)
        
        suggestions = query.all()
        return self._enrich_suggestions_with_vote_data(suggestions, user_id)

    def get_all_suggestions(self, current_user_id: Optional[int] = None) -> List[ActivitySuggestion]:
        """
        Retrieves all activity suggestions regardless of facility.
        This is a development method for testing purposes.
        """
        query = self.db.query(ActivitySuggestion).options(
            joinedload(ActivitySuggestion.suggested_by_user),
            joinedload(ActivitySuggestion.reviewed_by_admin),
            joinedload(ActivitySuggestion.votes)
        )
        
        suggestions = query.all()
        return self._enrich_suggestions_with_vote_data(suggestions, current_user_id)

    def update_suggestion(self, suggestion_id: int, update_data: ActivitySuggestionUpdate, current_user: User) -> ActivitySuggestion:
        """
        Updates an activity suggestion. Only the creator or facility admin can update.
        """
        suggestion = self.db.query(ActivitySuggestion).filter(ActivitySuggestion.id == suggestion_id).first()
        if not suggestion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity suggestion not found")
        
        # Check permissions
        if not self._can_edit_suggestion(suggestion, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this suggestion")
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(suggestion, field, value)
        
        suggestion.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(suggestion)
        return suggestion

    def delete_suggestion(self, suggestion_id: int, current_user: User) -> bool:
        """
        Deletes an activity suggestion. Only the creator or facility admin can delete.
        """
        suggestion = self.db.query(ActivitySuggestion).filter(ActivitySuggestion.id == suggestion_id).first()
        if not suggestion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity suggestion not found")
        
        # Check permissions
        if not self._can_edit_suggestion(suggestion, current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this suggestion")
        
        self.db.delete(suggestion)
        self.db.commit()
        return True

    def review_suggestion(self, suggestion_id: int, review_data: ActivitySuggestionReview, admin_user: User) -> ActivitySuggestion:
        """
        Allows facility admin to approve/reject activity suggestions.
        When approved, automatically creates a calendar event.
        """
        suggestion = self.db.query(ActivitySuggestion).filter(ActivitySuggestion.id == suggestion_id).first()
        if not suggestion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity suggestion not found")
        
        # Check if user is admin of the facility
        if not self._is_facility_admin(admin_user, suggestion.facility_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only facility administrators can review suggestions")
        
        suggestion.status = review_data.status.value
        suggestion.admin_response = review_data.admin_response
        suggestion.reviewed_by_admin_id = admin_user.id
        suggestion.reviewed_at = datetime.utcnow()
        suggestion.updated_at = datetime.utcnow()
        
        # If approved, create a calendar event
        if review_data.status.value == 'approved':
            self._create_calendar_event_from_suggestion(suggestion, admin_user)
        
        self.db.commit()
        self.db.refresh(suggestion)
        return suggestion

    def vote_on_suggestion(self, suggestion_id: int, vote_data: ActivitySuggestionVoteCreate, user: User) -> ActivitySuggestionVote:
        """
        Allows users to vote on activity suggestions.
        """
        suggestion = self.db.query(ActivitySuggestion).filter(ActivitySuggestion.id == suggestion_id).first()
        if not suggestion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity suggestion not found")
        
        # Check if suggestion is still pending
        if suggestion.status != ActivitySuggestionStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only vote on pending suggestions")
        
        # Check if user is in the same facility
        if user.facility_id != suggestion.facility_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only vote on suggestions from your facility")
        
        # Validate vote type
        if vote_data.vote_type not in ['upvote', 'downvote']:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vote type must be 'upvote' or 'downvote'")
        
        # Check if user already voted
        existing_vote = self.db.query(ActivitySuggestionVote).filter(
            ActivitySuggestionVote.suggestion_id == suggestion_id,
            ActivitySuggestionVote.user_id == user.id
        ).first()
        
        if existing_vote:
            # Update existing vote
            existing_vote.vote_type = vote_data.vote_type
            existing_vote.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing_vote)
            return existing_vote
        else:
            # Create new vote
            new_vote = ActivitySuggestionVote(
                suggestion_id=suggestion_id,
                user_id=user.id,
                vote_type=vote_data.vote_type
            )
            self.db.add(new_vote)
            self.db.commit()
            self.db.refresh(new_vote)
            return new_vote

    def remove_vote(self, suggestion_id: int, user: User) -> bool:
        """
        Removes a user's vote from an activity suggestion.
        """
        vote = self.db.query(ActivitySuggestionVote).filter(
            ActivitySuggestionVote.suggestion_id == suggestion_id,
            ActivitySuggestionVote.user_id == user.id
        ).first()
        
        if not vote:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vote not found")
        
        self.db.delete(vote)
        self.db.commit()
        return True

    def _enrich_suggestions_with_vote_data(self, suggestions: List[ActivitySuggestion], current_user_id: Optional[int] = None) -> List[ActivitySuggestion]:
        """
        Enriches suggestions with vote count data and current user's vote.
        """
        for suggestion in suggestions:
            # Count votes
            upvotes = sum(1 for vote in suggestion.votes if vote.vote_type == 'upvote')
            downvotes = sum(1 for vote in suggestion.votes if vote.vote_type == 'downvote')
            
            # Add vote counts as attributes
            suggestion.upvote_count = upvotes
            suggestion.downvote_count = downvotes
            suggestion.total_votes = upvotes + downvotes
            
            # Find current user's vote if provided
            if current_user_id:
                user_vote = next((vote.vote_type for vote in suggestion.votes if vote.user_id == current_user_id), None)
                suggestion.user_vote = user_vote
            
        return suggestions

    def _can_edit_suggestion(self, suggestion: ActivitySuggestion, user: User) -> bool:
        """
        Checks if a user can edit/delete a suggestion.
        """
        # Creator can always edit their own suggestions
        if suggestion.suggested_by_user_id == user.id:
            return True
        
        # Facility admin can edit all suggestions in their facility
        if self._is_facility_admin(user, suggestion.facility_id):
            return True
        
        return False

    def _is_facility_admin(self, user: User, facility_id: int) -> bool:
        """
        Checks if a user is a facility administrator.
        """
        from app.models.user import UserRole
        
        user_role = getattr(user, 'user_role', None)
        if user_role is None:
            return False
        
        # Compare with the enum value directly
        return user_role == UserRole.FACILITY_ADMIN and user.facility_id == facility_id

    def _create_calendar_event_from_suggestion(self, suggestion: ActivitySuggestion, admin_user: User) -> None:
        """
        Creates a calendar event from an approved activity suggestion.
        """
        import uuid
        from app.models.calendar_event import CalendarEvent
        from datetime import timedelta
        
        try:
            event_id = str(uuid.uuid4())
            
            # Use suggested date or default to next week
            if suggestion.suggested_date:
                start_time = suggestion.suggested_date
            else:
                # Default to next week at 2 PM
                from datetime import datetime, timedelta
                start_time = datetime.utcnow() + timedelta(days=7)
                start_time = start_time.replace(hour=14, minute=0, second=0, microsecond=0)
            
            # Calculate end time based on estimated duration or default to 1 hour
            if suggestion.estimated_duration_minutes:
                end_time = start_time + timedelta(minutes=suggestion.estimated_duration_minutes)
            else:
                end_time = start_time + timedelta(hours=1)
            
            # Create description with suggestion details
            description = f"Activity: {suggestion.title}"
            if suggestion.description:
                description += f"\n\nDescription: {suggestion.description}"
            if suggestion.category:
                description += f"\nCategory: {suggestion.category.title()}"
            if suggestion.location:
                description += f"\nLocation: {suggestion.location}"
            description += f"\n\nOriginally suggested by: {suggestion.suggested_by_user.full_name or suggestion.suggested_by_user.username}"
            
            # Create the calendar event
            calendar_event = CalendarEvent(
                id=event_id,
                user_id=admin_user.id,
                title=suggestion.title,
                start=start_time.isoformat(),
                end=end_time.isoformat(),
                description=description,
                location=suggestion.location,
                all_day=False,
                facility_id=suggestion.facility_id,
                created_by_admin=True,
                is_editable_by_user=True,  # Allow editing for activities
                event_type='facility_activity',
                activity_category=suggestion.category,
                requires_signup=False,  # Default to no signup required
                max_participants=None,
                signup_deadline=None,
                activity_status='planned'
            )
            
            self.db.add(calendar_event)
            # Note: commit will be called by the parent method
            
        except Exception as e:
            # Log the error but don't fail the suggestion approval
            print(f"Error creating calendar event from suggestion {suggestion.id}: {str(e)}")
            # Could add proper logging here 