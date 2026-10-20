"""
Description: SQLAlchemy model for storing real-time synchronization events.
Purpose: Tracks synchronization events between facility administrators and team members,
providing audit trail and fallback for real-time sync functionality.

Educational Note: This model stores sync events for both real-time delivery via SSE
and polling fallback. Events are retained for a limited time to support offline clients.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class SyncEvent(Base):
    """
    Description: Database model for synchronization events between facility admins and team members.
    Purpose: Stores events that need to be synchronized across team member accounts when
    facility administrators make changes to shared data like facility settings, documents, etc.
    """
    __tablename__ = "sync_events"

    id = Column(Integer, primary_key=True, index=True)
    
    # Facility and user targeting
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Null = all team members
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # User who triggered the event
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # account_update, document_update, etc.
    data = Column('data', JSON, nullable=False)  # Serialized event payload
    
    # Delivery tracking
    delivered = Column(Boolean, default=False, nullable=False)
    delivery_attempts = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Auto-cleanup old events
    delivered_at = Column(DateTime(timezone=True), nullable=True)  # When the event was delivered
    
    # Relationships
    facility = relationship("Facility", back_populates="sync_events")
    target_user = relationship("User", foreign_keys=[target_user_id], back_populates="sync_events")
    
    def __repr__(self):
        return f"<SyncEvent(id={self.id}, type={self.event_type}, facility_id={self.facility_id})>" 