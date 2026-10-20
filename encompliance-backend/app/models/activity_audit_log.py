"""
Activity Audit Log Model
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class ActivityAuditLog(Base):
    __tablename__ = "activity_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    entry_metadata = Column("metadata", JSON, nullable=True)
    prev_hash = Column(String(128), nullable=True)
    entry_hash = Column(String(128), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    actor = relationship("User")
    facility = relationship("Facility")

