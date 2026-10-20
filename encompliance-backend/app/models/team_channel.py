"""
Team Channel Model

Stores facility-level chat channels for asynchronous communication.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TeamChannel(Base):
    __tablename__ = "team_channels"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    is_private = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    facility = relationship("Facility", back_populates="team_channels")
    creator = relationship("User")
    messages = relationship(
        "TeamMessage",
        back_populates="channel",
        cascade="all, delete-orphan",
    )

