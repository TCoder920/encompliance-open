"""
Description: Service layer for managing user signups for activities.
Purpose: Handles the business logic for registering users for activities, validating signups, and retrieving signup information.
Key functionalities: register_for_activity, get_user_signups
"""
from sqlalchemy.orm import Session
from app.models import ActivitySignup, User, CalendarEvent
from app.schemas.activity_signup import ActivitySignupCreate
from typing import List, Optional
from fastapi import HTTPException, status

class ActivitySignupService:
    """
    Manages the logic for user registration in activities.
    """
    def __init__(self, db: Session):
        self.db = db

    def register_for_activity(self, signup_data: ActivitySignupCreate, user: User) -> ActivitySignup:
        """
        Registers a user for a facility activity.
        Performs validation to ensure the activity exists, requires signup, is not full,
        and the user has not already signed up.
        """
        activity = self.db.query(CalendarEvent).filter(CalendarEvent.id == signup_data.calendar_event_id).first()
        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

        if not activity.requires_signup:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This activity does not require signup.")

        existing_signup = self.db.query(ActivitySignup).filter(
            ActivitySignup.calendar_event_id == signup_data.calendar_event_id,
            ActivitySignup.user_id == user.id
        ).first()

        if existing_signup:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already signed up for this activity.")
        
        if activity.max_participants is not None and activity.current_participants >= activity.max_participants:
            # For now, just raise an error. Waitlist logic will be added later.
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Activity is full.")

        new_signup = ActivitySignup(
            calendar_event_id=signup_data.calendar_event_id,
            user_id=user.id,
            notes=signup_data.notes
        )
        self.db.add(new_signup)
        self.db.commit()
        self.db.refresh(new_signup)
        return new_signup

    def get_user_signups(self, user_id: int) -> List[ActivitySignup]:
        """
        Retrieves all activity signups for a specific user.
        """
        return self.db.query(ActivitySignup).filter(ActivitySignup.user_id == user_id).all() 