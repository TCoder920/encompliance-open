"""
Shift Swap Request Model Module

Handles peer-to-peer or admin-facilitated shift swap workflows. Swap requests
reference the originating shift and maintain an approval state machine.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ShiftSwapStatus(enum.Enum):
    """Status codes describing the shift swap lifecycle."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ShiftSwapRequest(Base):
    """Database model for shift swap workflow management."""

    __tablename__ = "shift_swap_requests"

    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False, index=True)
    requested_by_staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False)
    requested_to_staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    status = Column(String(20), default=ShiftSwapStatus.PENDING.value, index=True)
    reason = Column(String(1000), nullable=True)
    admin_notes = Column(String(1000), nullable=True)

    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True), nullable=True)

    shift = relationship("Shift", back_populates="swap_requests")
    requested_by_staff = relationship(
        "StaffMember",
        foreign_keys=[requested_by_staff_id],
        back_populates="swap_requests_initiated",
    )
    requested_to_staff = relationship(
        "StaffMember",
        foreign_keys=[requested_to_staff_id],
        back_populates="swap_requests_received",
    )
    facility = relationship("Facility", back_populates="shift_swap_requests")
    creator = relationship("User", foreign_keys=[created_by])
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<ShiftSwapRequest id={self.id} shift={self.shift_id} status={self.status}>"

