"""
Signup Session Model Module

This module defines the SignupSession database model for temporary storage
of user signup data before email verification is completed.

Key functionalities:
- Temporary storage of signup form data
- Session expiration management
- Automatic cleanup of expired sessions
- Prevention of database pollution with unverified accounts

Educational Note: Implements temporary data storage pattern to defer permanent
record creation until verification completion, following OWASP data minimization principles.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime, timedelta, timezone
import uuid

class SignupSession(Base):
    __tablename__ = "signup_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String, unique=True, index=True, nullable=False)  # UUID for session identification
    email = Column(String, index=True, nullable=False)  # For duplicate checking
    
    # Store all signup data as JSON until verification
    signup_data = Column(JSON, nullable=False)  # Contains: full_name, operation_name, phone_number, hashed_password, etc.
    
    # Track signup progress
    step_completed = Column(Integer, default=0)  # 0=none, 1=basic info, 2=state, 3=facility types
    
    # Session management
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Email verification
    email_verification_sent = Column(Boolean, default=False)
    verification_attempts = Column(Integer, default=0)
    
    def is_expired(self) -> bool:
        """Check if the signup session has expired"""
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        
        # Handle naive datetime (ensure it's treated as UTC if naive)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
            
        return now > expires
    
    def extend_session(self, hours: int = 24):
        """Extend session expiration by specified hours"""
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        self.last_activity = datetime.now(timezone.utc)
    
    @classmethod
    def generate_session_token(cls) -> str:
        """Generate a unique session token"""
        return str(uuid.uuid4())
    
    def __repr__(self):
        return f"<SignupSession(id={self.id}, email={self.email}, step={self.step_completed}, expires={self.expires_at})>" 