"""
Team Message Model

Captures channel messages, mentions, and lightweight attachment metadata.
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TeamMessage(Base):
    __tablename__ = "team_messages"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("team_channels.id"), nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    attachments = Column(JSON, nullable=True)
    mentions = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    channel = relationship("TeamChannel", back_populates="messages")
    facility = relationship("Facility", back_populates="team_messages")
    sender = relationship("User")

