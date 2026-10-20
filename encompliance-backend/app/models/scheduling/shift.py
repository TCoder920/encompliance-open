"""
Shift Model Module

Defines the core shift scheduling entity used by facility administrators to
publish work schedules. Shifts support recurrence, conflict tracking, and
audit-friendly metadata to satisfy compliance requirements.

Educational Note: References OSHA scheduling guidance and state workforce
regulations that require accurate record keeping for staffing plans.
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


class ShiftStatus(enum.Enum):
    """Enumeration of supported shift lifecycle states."""

    DRAFT = "draft"
    PUBLISHED = "published"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PENDING_SWAP = "pending_swap"


class ShiftRecurrencePattern(enum.Enum):
    """Supported recurrence rules for templated scheduling."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class Shift(Base):
    """Database model representing a single shift assignment."""

    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    staff_member_id = Column(Integer, ForeignKey("staff_members.id"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    role = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    break_minutes = Column(Integer, default=0)
    timezone = Column(String(64), nullable=True)

    status = Column(String(20), default=ShiftStatus.DRAFT.value, index=True)
    color_code = Column(String(20), nullable=True)
    coverage_tags = Column(JSON, nullable=True)
    compliance_notes = Column(String(1000), nullable=True)

    recurrence_pattern = Column(String(20), default=ShiftRecurrencePattern.NONE.value)
    recurrence_interval = Column(Integer, default=1)
    recurrence_days = Column(JSON, nullable=True)  # e.g., ["monday", "wednesday"]
    recurrence_ends_at = Column(DateTime(timezone=True), nullable=True)

    conflict_code = Column(String(50), nullable=True)
    conflict_reason = Column(String(255), nullable=True)
    last_conflict_check = Column(DateTime(timezone=True), nullable=True)

    is_locked = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    facility = relationship("Facility", back_populates="shifts")
    creator = relationship("User", foreign_keys=[created_by])
    staff_member = relationship("StaffMember", back_populates="shift_assignments")
    swap_requests = relationship(
        "ShiftSwapRequest",
        back_populates="shift",
        cascade="all, delete-orphan",
    )

    def mark_conflict(self, code: str, reason: str):
        """Persist a conflict marker for downstream analytics."""
        self.conflict_code = code
        self.conflict_reason = reason

    @property
    def is_recurring(self) -> bool:
        return self.recurrence_pattern != ShiftRecurrencePattern.NONE.value

    @property
    def duration_minutes(self) -> int:
        if not (self.start_time and self.end_time):
            return 0
        delta = self.end_time - self.start_time
        return max(0, int(delta.total_seconds() // 60) - (self.break_minutes or 0))

    def __repr__(self):
        return f"<Shift id={self.id} facility={self.facility_id} status={self.status}>"

