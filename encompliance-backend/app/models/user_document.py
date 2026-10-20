"""
User Document Model Module

This module defines the UserDocument database model for the EnCompliance application.
It manages the relationship between users and regulatory documents they have accessed.

Key functionalities:
- User-document relationship tracking
- Regulatory document access logging
- Timestamp-based access tracking
- User and regulation associations
- Document access history

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class UserDocument(Base):
    __tablename__ = "user_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    regulation_id = Column(Integer, ForeignKey("regulations.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Define relationships
    user = relationship("User", foreign_keys=[user_id])
    regulation = relationship("Regulation", back_populates="user_documents")
    
    def __repr__(self):
        return f"<UserDocument(id={self.id}, user_id={self.user_id}, regulation_id={self.regulation_id})>" 