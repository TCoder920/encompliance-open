"""
Description: Database model for tracking user signups for facility activities.
Purpose: Connects users to calendar events, enabling registration for activities that require signups.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class ActivitySignupStatus(str, enum.Enum):
    """Enum for the status of an activity signup."""
    SIGNED_UP = "signed_up"
    WAITLISTED = "waitlisted"
    CANCELLED = "cancelled"

class ActivitySignup(Base):
    """
    Represents a user's signup for a specific calendar event (activity).
    This table links a user to an event they have registered for.
    """
    __tablename__ = "activity_signups"

    id = Column(Integer, primary_key=True, index=True)
    calendar_event_id = Column(String(36), ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status of the signup, e.g., confirmed, waitlisted, or cancelled.
    status = Column(String(50), nullable=False, default=ActivitySignupStatus.SIGNED_UP.value)
    # Optional notes provided by the user during signup.
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    calendar_event = relationship("CalendarEvent", back_populates="signups")
    user = relationship("User")

    def __repr__(self):
        return f"<ActivitySignup(id={self.id}, event_id='{self.calendar_event_id}', user_id={self.user_id})>" 