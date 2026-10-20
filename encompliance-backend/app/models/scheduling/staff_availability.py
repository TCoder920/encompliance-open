"""
Staff Availability Model Module

Represents recurring availability windows submitted by staff members.
Availability windows are used by the scheduling service to recommend
assignments and detect conflicts.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class AvailabilityStatus(enum.Enum):
    """Lifecycle states for availability blocks."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    UNAVAILABLE = "unavailable"


class StaffAvailability(Base):
    """Availability block definition for a staff member."""

    __tablename__ = "staff_availability"

    id = Column(Integer, primary_key=True, index=True)
    staff_member_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    day_of_week = Column(String(20), nullable=False)  # monday, tuesday, etc.
    start_time = Column(String(5), nullable=False)  # HH:MM (local facility time)
    end_time = Column(String(5), nullable=False)
    preference_level = Column(Integer, default=3)  # 1-5 preference weighting

    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default=AvailabilityStatus.ACTIVE.value, index=True)
    exception_dates = Column(JSON, nullable=True)  # Dates to skip availability
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    staff_member = relationship("StaffMember", back_populates="availability_blocks")
    facility = relationship("Facility", back_populates="availability_blocks")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<StaffAvailability id={self.id} staff={self.staff_member_id} day={self.day_of_week}>"

