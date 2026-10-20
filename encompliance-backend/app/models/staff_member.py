"""
Staff Member Model Module

This module defines the StaffMember database model for facility staff management.
It represents staff members within a facility with role-based access.

Key functionalities:
- Staff member profile information
- Role and department assignment
- Facility association
- Training assignment tracking
- Certification status management
- Contact information

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class StaffRole(enum.Enum):
    STAFF = "staff"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    ADMINISTRATOR = "administrator"

class StaffStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"

class StaffMember(Base):
    __tablename__ = "staff_members"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), nullable=True, index=True)  # External employee ID
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone_number = Column(String(20), nullable=True)
    birth_date = Column(Date, nullable=True)  # Required for age-based task assignment
    
    # Employment details
    role = Column(String(20), default=StaffRole.STAFF.value)
    department = Column(String(100), nullable=True)
    position_title = Column(String(100), nullable=True)
    hire_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default=StaffStatus.ACTIVE.value)
    
    # Facility association
    facility_administrator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    facility_name = Column(String(255), nullable=True)
    facility_location = Column(String(255), nullable=True)
    
    # Training and certification tracking
    training_completion_rate = Column(Integer, default=0)  # Percentage
    certifications_current = Column(Integer, default=0)
    certifications_expired = Column(Integer, default=0)
    last_training_date = Column(DateTime(timezone=True), nullable=True)
    
    # Notification preferences
    notification_preferences = Column(JSON, nullable=True)  # Email, SMS, push preferences
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    facility_administrator = relationship("User", foreign_keys=[facility_administrator_id])
    training_assignments = relationship("TrainingAssignment", back_populates="staff_member", cascade="all, delete-orphan")
    training_completions = relationship("TrainingCompletion", back_populates="staff_member", cascade="all, delete-orphan")
    
    # Policy relationships
    policy_assignments = relationship("PolicyAssignment", back_populates="staff_member", cascade="all, delete-orphan")
    policy_acknowledgments = relationship("PolicyAcknowledgment", back_populates="staff_member", cascade="all, delete-orphan")
    
    # Task management relationships
    task_assignments = relationship("TaskAssignment", back_populates="staff_member", cascade="all, delete-orphan")
    shift_assignments = relationship("Shift", back_populates="staff_member")
    availability_blocks = relationship(
        "StaffAvailability",
        back_populates="staff_member",
        cascade="all, delete-orphan"
    )
    time_off_requests = relationship(
        "TimeOffRequest",
        back_populates="staff_member",
        cascade="all, delete-orphan"
    )
    swap_requests_initiated = relationship(
        "ShiftSwapRequest",
        foreign_keys="ShiftSwapRequest.requested_by_staff_id",
        back_populates="requested_by_staff",
        cascade="all, delete-orphan"
    )
    facility_assignments = relationship(
        "StaffFacilityAssignment",
        back_populates="staff_member",
        cascade="all, delete-orphan"
    )
    transfer_requests = relationship(
        "StaffTransferRequest",
        back_populates="staff_member",
        cascade="all, delete-orphan"
    )
    swap_requests_received = relationship(
        "ShiftSwapRequest",
        foreign_keys="ShiftSwapRequest.requested_to_staff_id",
        back_populates="requested_to_staff",
        cascade="all, delete-orphan"
    )
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self):
        return self.status == StaffStatus.ACTIVE.value
    
    @property
    def age(self):
        """Calculate current age from birth_date."""
        if not self.birth_date:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    def __repr__(self):
        return f"<StaffMember(id={self.id}, name={self.full_name}, role={self.role})>" 