"""
Manager Override Request Model
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class ManagerOverrideStatus(str):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ManagerOverrideRequest(Base):
    __tablename__ = "manager_override_requests"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default=ManagerOverrideStatus.PENDING, nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(String(255), nullable=True)

    facility = relationship("Facility")
    requester = relationship("User", foreign_keys=[requested_by_user_id])
    approver = relationship("User", foreign_keys=[approved_by_user_id])

