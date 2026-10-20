"""
Facility Model Module

This module defines the Facility database model for the EnCompliance Pro Mode system.
It represents healthcare facilities that subscribe to the platform and manage multiple users.

Key functionalities:
- Facility information storage (name, address, contact details)
- Admin user relationship management
- Subscription tracking and billing integration
- User capacity management
- Facility-wide settings and preferences

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime


class Facility(Base):
    __tablename__ = "facilities"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Facility information
    facility_name = Column(String(255), nullable=False, index=True)
    facility_address = Column(Text, nullable=True)
    facility_city = Column(String(100), nullable=True)
    facility_state = Column(String(50), nullable=True)
    facility_zip = Column(String(20), nullable=True)
    facility_phone = Column(String(20), nullable=True)
    facility_email = Column(String(255), nullable=True)
    
    # Admin relationship
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Subscription management
    subscription_id = Column(String(255), nullable=True, unique=True)  # Stripe subscription ID
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    
    # Facility settings
    max_users = Column(Integer, nullable=True)  # Unlimited for Pro users
    is_active = Column(Boolean, default=True)
    
    # Invitation system
    invitation_code = Column(String(50), nullable=True, unique=True)  # Current invitation code
    invitation_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    admin_user = relationship("User", foreign_keys=[admin_user_id], back_populates="administered_facility")
    organization = relationship("Organization", back_populates="facilities")
    users = relationship("User", foreign_keys="User.facility_id", back_populates="facility")
    subscriptions = relationship("Subscription", back_populates="facility", cascade="all, delete-orphan")
    training_assignments = relationship("TrainingAssignment", back_populates="facility")
    calendar_events = relationship("CalendarEvent", back_populates="facility")
    invitations = relationship("FacilityInvitation", back_populates="facility", cascade="all, delete-orphan")
    sync_events = relationship("SyncEvent", back_populates="facility", cascade="all, delete-orphan")
    operational_tasks = relationship("OperationalTask", back_populates="facility", cascade="all, delete-orphan")
    shifts = relationship("Shift", back_populates="facility", cascade="all, delete-orphan")
    availability_blocks = relationship("StaffAvailability", back_populates="facility", cascade="all, delete-orphan")
    time_off_requests = relationship("TimeOffRequest", back_populates="facility", cascade="all, delete-orphan")
    shift_swap_requests = relationship("ShiftSwapRequest", back_populates="facility", cascade="all, delete-orphan")
    team_channels = relationship("TeamChannel", back_populates="facility", cascade="all, delete-orphan")
    team_messages = relationship("TeamMessage", back_populates="facility", cascade="all, delete-orphan")
    staff_assignments = relationship("StaffFacilityAssignment", back_populates="facility", cascade="all, delete-orphan")
    email_campaigns = relationship("EmailCampaign", back_populates="facility", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="facility", cascade="all, delete-orphan")
    
    @property
    def current_user_count(self):
        """Get current number of users in facility."""
        return len(self.users) if self.users else 0
    
    @property
    def available_seats(self):
        """Calculate available seats based on subscription."""
        # This will be calculated based on subscription seat_count vs current users
        # Return a large number to avoid JSON serialization issues, actual logic in subscription
        return 999999  # Placeholder for JSON serialization
    
    @property
    def is_at_capacity(self):
        """Check if facility needs additional seats (payment required)."""
        # This will be handled by subscription logic, not hard limits
        return False  # No hard capacity limits, just payment requirements
    
    def __repr__(self):
        return f"<Facility(id={self.id}, name={self.facility_name}, admin_id={self.admin_user_id})>" 