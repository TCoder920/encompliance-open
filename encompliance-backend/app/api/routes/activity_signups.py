"""
Description: API routes for managing activity signups.
Purpose: Provides endpoints for users to register for activities and view their signups.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth.dependencies import get_current_active_user
from app.services.activity_signup_service import ActivitySignupService
from app.schemas.activity_signup import ActivitySignup, ActivitySignupCreate
from typing import List

router = APIRouter(prefix="/activity-signups", tags=["Activity Signups"])

@router.post("/", response_model=ActivitySignup, status_code=status.HTTP_201_CREATED)
def signup_for_activity(
    signup_data: ActivitySignupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Sign up the current user for an activity.
    
    - **Requires**: Any authenticated user.
    """
    service = ActivitySignupService(db)
    signup = service.register_for_activity(signup_data, current_user)
    return signup

@router.get("/my-signups", response_model=List[ActivitySignup])
def get_my_signups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all activity signups for the current user.
    
    - **Requires**: Any authenticated user.
    """
    service = ActivitySignupService(db)
    signups = service.get_user_signups(current_user.id)
    return signups 