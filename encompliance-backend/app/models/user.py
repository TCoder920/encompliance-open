"""
User Model Module

This module defines the User database model for the EnCompliance application.
It represents the core user entity with authentication and profile information.

Key functionalities:
- User authentication fields (email, username, password)
- User profile information (name, operation, facility type)
- Multi-factor authentication settings
- Subscription management
- Document relationships
- Activity tracking (login, creation, updates)
- OpenAI integration fields
- Quick access links for dashboard customization
- User notes for personal organization
- User notifications for system alerts
- Facility administration and membership

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, LargeBinary, Enum, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
import enum

class MFAMethod(enum.Enum):
    NONE = "none"
    EMAIL = "email"
    SMS = "sms"
    TOTP = "totp"
    WEBAUTHN = "webauthn"

class UserRole(enum.Enum):
    FREE_USER = "free_user"
    FACILITY_ADMIN = "facility_admin"
    TEAM_MEMBER = "team_member"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    operation_name = Column(String, nullable=True)
    facility_type = Column(String, nullable=True)
    state = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    
    # User role system
    user_role = Column(Enum(UserRole), default=UserRole.FREE_USER, nullable=False)
    role_description = Column(String(100), nullable=True)  # Custom role description for team members
    
    # Facility management fields
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True, index=True)
    
    # Existing relationships
    documents = relationship("Document", back_populates="user", foreign_keys="Document.uploaded_by")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", foreign_keys="Notification.user_id", back_populates="user", cascade="all, delete")
    sent_notifications = relationship("Notification", foreign_keys="Notification.sender_id", back_populates="sender")
    push_subscriptions = relationship("PushSubscription", back_populates="user", cascade="all, delete")
    notification_settings = relationship("NotificationSettings", back_populates="user", uselist=False, cascade="all, delete")
    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    calendar_connections = relationship("CalendarConnection", back_populates="user", cascade="all, delete-orphan")
    role_assignments = relationship("UserRoleAssignment", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship(
        "APIKey",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="APIKey.user_id",
    )
    
    # Facility relationships
    facility = relationship("Facility", foreign_keys=[facility_id], back_populates="users")
    administered_facility = relationship("Facility", foreign_keys="Facility.admin_user_id", back_populates="admin_user", uselist=False)
    
    # Sync relationships
    sync_events = relationship("SyncEvent", foreign_keys="SyncEvent.target_user_id", back_populates="target_user", cascade="all, delete-orphan")
    
    subscription_status = Column(String, nullable=True, default="free")
    subscription_end_date = Column(String, nullable=True)
    
    # Grace period and downgrade tracking
    pending_downgrade = Column(Boolean, default=False)  # User is pending downgrade after grace period
    downgrade_after = Column(DateTime(timezone=True), nullable=True)  # When to downgrade user
    
    is_active = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    last_login = Column(DateTime(timezone=True))
    encrypted_settings = Column(LargeBinary, nullable=True)
    openai_vector_store_id = Column(String, nullable=True)
    openai_assistant_id = Column(String, nullable=True)
    quick_access_links = Column(JSON, nullable=True)  # Store user-customized quick access links
    
    # MFA related fields
    mfa_enabled = Column(Boolean, default=False)
    preferred_mfa_method = Column(Enum(MFAMethod), default=MFAMethod.NONE)
    recovery_codes = Column(String, nullable=True)  # Comma-separated list of hashed recovery codes
    totp_secret = Column(String, nullable=True)  # Encrypted TOTP secret for time-based OTP
    phone_verified = Column(Boolean, default=False)  # Whether the phone number is verified
    
    # For partial login sessions (needs second factor)
    mfa_required = Column(Boolean, default=False)  # Whether MFA is required for current session
    
    # WebAuthn related fields
    webauthn_challenge = Column(String, nullable=True)  # Current WebAuthn challenge for user

    @property
    def is_pro_user(self):
        """Check if user has pro subscription or is a team member with pro access."""
        return self.subscription_status == "pro" or self.user_role == UserRole.TEAM_MEMBER
    
    @property
    def is_facility_admin(self):
        """Check if user is a facility admin."""
        return self.user_role == UserRole.FACILITY_ADMIN
    
    @property
    def is_team_member(self):
        """Check if user is a team member."""
        return self.user_role == UserRole.TEAM_MEMBER
    
    @property
    def can_manage_facility(self):
        """Check if user can manage facility operations (only facility admins can)."""
        return self.is_facility_admin
    
    @property
    def has_pro_features(self):
        """Check if user has access to pro features (facility admins and team members)."""
        return self.is_facility_admin or self.is_team_member
    
    @property
    def facility_name(self):
        """Get the name of the user's facility or create personal facility name for Pro users.
        
        Pro users manage exactly ONE facility. Enterprise users (future feature) 
        will manage multiple facilities.
        """
        if self.facility and self.facility.facility_name:
            return self.facility.facility_name
        elif self.is_pro_user and self.full_name:
            return f"{self.full_name}'s Practice"
        elif self.is_pro_user:
            return f"{self.username}'s Practice"
        return None

    def get_username(self):
        return self.username
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the user's hashed password."""
        from app.auth.utils import verify_password as verify_password_util
        return verify_password_util(password, self.hashed_password)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>" 