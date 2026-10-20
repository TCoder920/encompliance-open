"""
Description: API routes for managing facility activities.
Purpose: Provides endpoints for creating, retrieving, and managing facility-wide activities.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth.dependencies import get_current_active_user, require_facility_admin
from app.services.activity_calendar_service import ActivityCalendarService
from app.schemas.activity import Activity, ActivityCreate
from typing import List

router = APIRouter(prefix="/activities", tags=["Activities"])

@router.post("/", response_model=Activity, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity_data: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """
    Create a new facility activity.
    
    - **Requires**: Facility Administrator role.
    """
    service = ActivityCalendarService(db)
    activity = service.create_facility_activity(activity_data, current_user)
    return activity

@router.get("/", response_model=List[Activity])
def get_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all activities for the user's facility.
    
    - **Requires**: Any authenticated user belonging to a facility.
    """
    if not current_user.facility_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not associated with a facility.")
    
    service = ActivityCalendarService(db)
    activities = service.get_facility_activities(current_user.facility_id)
    return activities 