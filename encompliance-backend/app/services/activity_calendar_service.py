"""
Description: Service layer for managing facility activities and events.
Purpose: Encapsulates the business logic for creating, retrieving, and managing facility-wide activities.
Key functionalities: create_facility_activity, get_facility_activities
"""
from sqlalchemy.orm import Session
from app.models import CalendarEvent, User
from app.schemas.activity import ActivityCreate
from typing import List
import uuid
from datetime import datetime

class ActivityCalendarService:
    """
    Provides methods for activity-related operations, interfacing between the API routes and the database models.
    """
    def __init__(self, db: Session):
        self.db = db

    def create_facility_activity(self, activity_data: ActivityCreate, admin_user: User) -> CalendarEvent:
        """
        Creates a new facility-wide activity event. This is restricted to facility administrators.
        The event is associated with the facility and marked as an 'facility_activity' type.
        """
        event_id = str(uuid.uuid4())

        new_activity = CalendarEvent(
            id=event_id,
            user_id=admin_user.id, # The event is owned by the creating admin
            facility_id=admin_user.facility_id,
            title=activity_data.title,
            description=activity_data.description,
            start=activity_data.start,
            end=activity_data.end,
            location=activity_data.location,
            all_day=activity_data.all_day,
            event_type='facility_activity',
            activity_category=activity_data.activity_category,
            requires_signup=activity_data.requires_signup,
            max_participants=activity_data.max_participants,
            signup_deadline=activity_data.signup_deadline,
            activity_status='planned',
            created_by_admin=True,
            is_editable_by_user=False
        )

        self.db.add(new_activity)
        self.db.commit()
        self.db.refresh(new_activity)
        return new_activity

    def get_facility_activities(self, facility_id: int) -> List[CalendarEvent]:
        """
        Retrieves all activity events for a given facility.
        Only includes facility_activity events, not general calendar events.
        """
        return self.db.query(CalendarEvent).filter(
            CalendarEvent.facility_id == facility_id,
            CalendarEvent.event_type == 'facility_activity'
        ).all() 