"""
Description: Database model for storing activity suggestions from facility staff.
Purpose: Allows users to suggest new activities, which can then be reviewed by administrators.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class ActivitySuggestionStatus(str, enum.Enum):
    """Enum for the status of an activity suggestion."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"

class ActivitySuggestion(Base):
    """
    Represents an activity suggestion made by a user for their facility.
    Admins can review these suggestions and decide whether to implement them.
    """
    __tablename__ = "activity_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    suggested_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    suggested_date = Column(DateTime(timezone=True), nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    
    # Review status of the suggestion, handled by facility administrators.
    status = Column(String(50), nullable=False, default=ActivitySuggestionStatus.PENDING.value)
    # Optional feedback from an admin on the suggestion.
    admin_response = Column(Text, nullable=True)
    # Admin who approved/rejected the suggestion
    reviewed_by_admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    facility = relationship("Facility")
    suggested_by_user = relationship("User", foreign_keys=[suggested_by_user_id])
    reviewed_by_admin = relationship("User", foreign_keys=[reviewed_by_admin_id])
    votes = relationship("ActivitySuggestionVote", back_populates="suggestion", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ActivitySuggestion(id={self.id}, title='{self.title}', facility_id={self.facility_id})>"

class ActivitySuggestionVote(Base):
    """
    Represents a vote on an activity suggestion by a team member.
    """
    __tablename__ = "activity_suggestion_votes"

    id = Column(Integer, primary_key=True, index=True)
    suggestion_id = Column(Integer, ForeignKey("activity_suggestions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vote_type = Column(String(20), nullable=False)  # 'upvote' or 'downvote'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    suggestion = relationship("ActivitySuggestion", back_populates="votes")
    user = relationship("User")

    # Ensure one vote per user per suggestion
    __table_args__ = (UniqueConstraint('suggestion_id', 'user_id', name='unique_user_vote_per_suggestion'),)

    def __repr__(self):
        return f"<ActivitySuggestionVote(id={self.id}, suggestion_id={self.suggestion_id}, user_id={self.user_id}, vote_type='{self.vote_type}')>" 