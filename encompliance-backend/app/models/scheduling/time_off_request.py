"""
Time Off Request Model Module

Captures PTO, sick leave, and other absence requests that impact workforce
coverage. Supports approval workflow, audit logging, and compliance tagging.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class TimeOffStatus(enum.Enum):
    """Workflow states for time off requests."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"


class TimeOffCategory(enum.Enum):
    """Categorization used for reporting/audit requirements."""

    PTO = "pto"
    VACATION = "vacation"
    SICK = "sick"
    TRAINING = "training"
    BEREAVEMENT = "bereavement"
    OTHER = "other"


class TimeOffRequest(Base):
    """Database representation of a staff member time off request."""

    __tablename__ = "time_off_requests"

    id = Column(Integer, primary_key=True, index=True)
    staff_member_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default=TimeOffStatus.PENDING.value, index=True)
    category = Column(String(20), default=TimeOffCategory.PTO.value)

    requested_hours = Column(Integer, nullable=True)
    is_paid = Column(Boolean, default=True)
    reason = Column(String(1000), nullable=True)
    supporting_files = Column(JSON, nullable=True)

    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    decision_notes = Column(String(1000), nullable=True)

    audit_trail = Column(JSON, nullable=True)
    overlaps_shift_ids = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    staff_member = relationship("StaffMember", back_populates="time_off_requests")
    facility = relationship("Facility", back_populates="time_off_requests")
    requester = relationship("User", foreign_keys=[requested_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def add_audit_entry(self, entry: dict):
        """Append an audit entry keeping history immutable."""
        entries = self.audit_trail or []
        entries.append(entry)
        self.audit_trail = entries

    def __repr__(self):
        return f"<TimeOffRequest id={self.id} staff={self.staff_member_id} status={self.status}>"

