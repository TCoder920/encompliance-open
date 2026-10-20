"""
Description: Push subscription model for storing web push notification subscriptions.
Purpose: Enables the system to send push notifications to users' browsers.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PushSubscription(Base):
    """SQLAlchemy model for push notification subscriptions."""
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    endpoint = Column(Text, nullable=False, unique=True)
    keys = Column(JSON, nullable=False)  # Stores p256dh and auth keys
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="push_subscriptions")

    def __repr__(self):
        return f"<PushSubscription(id={self.id}, user_id={self.user_id})>" 