# Description: API router for handling Contact Us form submissions.
# Purpose: Receives user contact messages and relays them to support via email, supporting both authenticated and unauthenticated users.

"""
Contact Module
-------------
Handles Contact Us form submissions and sends them to support.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from sqlalchemy.orm import Session

from app.utils.email_utils import send_contact_message_email
from app.auth.dependencies import get_current_user_optional
from app.models.user import User
from app.database import get_support_portal_db

router = APIRouter()

class ContactMessagePayload(BaseModel):
    name: str = Field(..., description="Name of the sender")
    email: EmailStr = Field(..., description="Sender's email address")
    message: str = Field(..., description="Message content")

@router.post("/contact", status_code=status.HTTP_201_CREATED)
def send_contact_message(
    payload: ContactMessagePayload,
    current_user: Optional[User] = Depends(get_current_user_optional),
    support_db: Session = Depends(get_support_portal_db)
):
    """Receives a contact message and sends it to support."""
    if current_user:
        user_data = {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username,
            "phone_number": getattr(current_user, "phone_number", None),
            "name": getattr(current_user, "name", None)
        }
    else:
        user_data = {
            "id": None,
            "email": payload.email,
            "username": None,
            "phone_number": None,
            "name": payload.name
        }

    success = send_contact_message_email(
        user_data=user_data,
        message=payload.message
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send contact message email.",
        )

    # Create Support Ticket if user is authenticated
    # This supplements the email by tracking it in the support portal
    if current_user:
        try:
            from app.models.support_ticket import (
                SupportTicket, 
                TicketStatus, 
                TicketPriority, 
                TicketCategory, 
                SupportTier
            )
            
            # Use specific facility ID if available on user
            facility_id = current_user.facility_id if hasattr(current_user, 'facility_id') else None
            
            new_ticket = SupportTicket(
                subject=f"Contact Form: {payload.name}",
                description=payload.message,
                status=TicketStatus.OPEN,
                priority=TicketPriority.MEDIUM,
                category=TicketCategory.OTHER,
                support_tier_required=SupportTier.BEGINNER,
                user_id=current_user.id,
                facility_id=facility_id
            )
            support_db.add(new_ticket)
            support_db.commit()
            support_db.refresh(new_ticket)
        except Exception as e:
            # Log error but don't fail the request since the email was sent successfully
            # In a real app, use the logger
            print(f"Failed to create support ticket for contact message: {e}")

    return {"message": "Contact message sent successfully"} 