"""
Survey Module
------------
This module manages survey functionality in the EnCompliance system.
It provides:
- Survey creation and management
- Response collection and analysis
- Survey templates
- Response validation
- Survey results reporting
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

# Assuming you have a way to get the current user, e.g., via OAuth2
from app.auth.dependencies import get_current_active_user
from app.models.user import User # Import your User model

from app.utils.email_utils import send_survey_response_email

# --- Removed Placeholder Function Definition --- #

router = APIRouter()

class SurveyResponsePayload(BaseModel):
    response: str = Field(..., description="The selected dropdown option or 'Other'")
    otherText: Optional[str] = Field(None, description="User input if 'Other' was selected")

@router.post("/submit-survey", status_code=status.HTTP_201_CREATED)
def submit_survey(
    payload: SurveyResponsePayload,
    current_user: User = Depends(get_current_active_user)
):
    """Receives survey response and sends it via email."""
    user_id = str(current_user.id)  # Ensure user_id is a string
    
    # Collect complete user data
    user_data = {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "phone_number": getattr(current_user, "phone_number", None),
        "name": getattr(current_user, "name", None)
    }

    success = send_survey_response_email(
        user_data=user_data,
        response=payload.response,
        other_text=payload.otherText
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send survey response email.",
        )

    # --- Optional: Save to Database --- #
    # try:
    #     # Assuming you have a DB session and a service/CRUD function
    #     # db_session = Depends(get_db_session)
    #     # survey_service.create_response(db_session, user_id=user_id, response=payload.response, other_text=payload.otherText)
    #     pass # Replace with DB saving logic
    # except Exception as e:
    #     # Log the error, but maybe don't fail the request if email was sent?
    #     print(f"Error saving survey response to DB: {e}")
    # --- End Optional --- #

    return {"message": "Survey response submitted successfully"} 