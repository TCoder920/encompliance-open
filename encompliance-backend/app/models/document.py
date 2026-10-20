"""
Document Model Module

This module defines the Document database model for the EnCompliance application.
It manages user-uploaded documents and their metadata.

Key functionalities:
- Document metadata storage
- File tracking and management
- User ownership tracking
- Soft deletion support
- OpenAI file integration
- File size and type tracking
- Custom user-defined labels for document categorization
- Document expiration tracking for facility compliance

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Boolean, Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    custom_label = Column(String, nullable=True)  # User-defined label for document categorization
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    openai_file_id = Column(String, nullable=True)
    
    # Document expiration tracking for Pro Mode facility administrators
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    document_type = Column(String(100), nullable=True)  # license, certification, permit, policy, etc.
    issuing_authority = Column(String(255), nullable=True)  # Authority that issued the document
    renewal_required = Column(Boolean, default=False)
    expiration_reminder_30_days_sent = Column(Boolean, default=False)
    expiration_reminder_14_days_sent = Column(Boolean, default=False)
    expiration_reminder_7_days_sent = Column(Boolean, default=False)
    expiration_reminder_1_day_sent = Column(Boolean, default=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True, index=True)
    
    # Define relationship back to the User model
    user = relationship("User", back_populates="documents", foreign_keys=[uploaded_by])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])
    facility = relationship("Facility", foreign_keys=[facility_id])
    
    @property
    def is_expired(self):
        """Check if document has expired."""
        from datetime import datetime
        return self.expiration_date and self.expiration_date < datetime.now()
    
    @property
    def days_until_expiry(self):
        """Calculate days until document expires."""
        from datetime import datetime
        if self.expiration_date:
            # Ensure we're comparing timezone-aware or timezone-naive datetimes consistently
            now = datetime.now()
            expiry = self.expiration_date
            
            # If expiration_date is timezone-aware, make now timezone-aware too
            if expiry.tzinfo is not None and now.tzinfo is None:
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            elif expiry.tzinfo is None and now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            
            delta = expiry - now
            return max(0, delta.days)  # Don't return negative days
        return None
    
    @property
    def needs_expiration_reminder(self):
        """Check if document needs an expiration reminder."""
        if not self.expiration_date:
            return False
        
        days_until_expiry = self.days_until_expiry
        if days_until_expiry is None:
            return False
        
        # Check if we need to send any reminder
        if days_until_expiry <= 1 and not self.expiration_reminder_1_day_sent:
            return True
        elif days_until_expiry <= 7 and not self.expiration_reminder_7_days_sent:
            return True
        elif days_until_expiry <= 14 and not self.expiration_reminder_14_days_sent:
            return True
        elif days_until_expiry <= 30 and not self.expiration_reminder_30_days_sent:
            return True
        
        return False 