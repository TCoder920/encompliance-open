"""
Description: Calendar connection model for storing external calendar integrations.
Purpose: Manages OAuth tokens and connection details for Google Calendar and Apple Calendar (CalDAV).
Educational Note: Implements secure token storage with encryption for external calendar APIs.
Reference: OAuth 2.0 Security Best Practices - https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CalendarConnection(Base):
    """Model for storing external calendar integration details."""
    __tablename__ = "calendar_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Provider information
    provider = Column(String(50), nullable=False)  # 'google' or 'apple'
    provider_user_id = Column(String(255), nullable=True)  # External user ID
    
    # OAuth tokens (encrypted)
    access_token = Column(Text, nullable=True)  # Encrypted access token
    refresh_token = Column(Text, nullable=True)  # Encrypted refresh token
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Connection status
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(String(50), default='connected')  # connected, error, disconnected
    
    # Calendar-specific settings
    calendar_id = Column(String(255), nullable=True)  # External calendar ID
    calendar_name = Column(String(255), nullable=True)
    sync_direction = Column(String(20), default='bidirectional')  # import, export, bidirectional
    sync_enabled = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="calendar_connections")
    
    def __repr__(self):
        return f"<CalendarConnection(id={self.id}, user_id={self.user_id}, provider={self.provider})>"

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "provider": self.provider,
            "calendarId": self.calendar_id,
            "calendarName": self.calendar_name,
            "isActive": self.is_active,
            "syncEnabled": self.sync_enabled,
            "tokenExpiresAt": self.token_expires_at.isoformat() if self.token_expires_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None
        } 