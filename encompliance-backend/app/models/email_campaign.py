"""
Email Campaign Model

Tracks admin-driven email campaigns to staff with compliance templates.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class EmailCampaignStatus:
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"


class EmailCampaign(Base):
    __tablename__ = "email_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    template_type = Column(String(50), nullable=True)
    target_roles = Column(JSON, nullable=True)
    status = Column(String(20), default=EmailCampaignStatus.DRAFT)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    delivery_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    facility = relationship("Facility", back_populates="email_campaigns")
    creator = relationship("User")

