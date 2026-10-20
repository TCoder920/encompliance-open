"""
Staff Directory Models

Implements facility assignment tracking and transfer workflows for staff members.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class StaffAssignmentStatus(enum.Enum):
    ACTIVE = "active"
    TRANSFERRING = "transferring"
    REMOVED = "removed"


class StaffTransferStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class StaffFacilityAssignment(Base):
    """
    Links a staff member to a facility with auditing metadata.
    """

    __tablename__ = "staff_facility_assignments"

    id = Column(Integer, primary_key=True, index=True)
    staff_member_id = Column(Integer, ForeignKey("staff_members.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    is_primary = Column(Boolean, default=True)
    status = Column(String(20), default=StaffAssignmentStatus.ACTIVE.value, nullable=False, index=True)
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    unassigned_at = Column(DateTime(timezone=True), nullable=True)
    assignment_metadata = Column("metadata", JSON, nullable=True)

    staff_member = relationship("StaffMember", back_populates="facility_assignments")
    facility = relationship("Facility", back_populates="staff_assignments")
    assigned_by_user = relationship("User")


class StaffTransferRequest(Base):
    """
    Records transfer approvals between facilities for a staff member.
    """

    __tablename__ = "staff_transfer_requests"

    id = Column(Integer, primary_key=True, index=True)
    staff_member_id = Column(Integer, ForeignKey("staff_members.id", ondelete="CASCADE"), nullable=False, index=True)
    source_facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False)
    target_facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default=StaffTransferStatus.PENDING.value, nullable=False, index=True)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    staff_member = relationship("StaffMember", back_populates="transfer_requests")
    source_facility = relationship("Facility", foreign_keys=[source_facility_id])
    target_facility = relationship("Facility", foreign_keys=[target_facility_id])
    requested_by_user = relationship("User", foreign_keys=[requested_by_user_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by_user_id])


