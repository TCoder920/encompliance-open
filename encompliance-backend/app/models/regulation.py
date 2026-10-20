"""
Regulation Model Module

This module defines the Regulation database model for the EnCompliance application.
It manages regulatory documents and their relationships with facility types.

Key functionalities:
- Regulatory document metadata
- State/territory tracking
- Document versioning
- Facility type associations
- User document relationships
- OpenAI file integration

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.facility_type import regulation_facility_types

class Regulation(Base):
    __tablename__ = "regulations"
    
    id = Column(Integer, primary_key=True, index=True)
    state_territory = Column(String, index=True, nullable=False)  # Keep this as state_territory to match DB
    document_title = Column(String, nullable=False)
    document_type = Column(String, nullable=True)
    file_name = Column(String, nullable=False)  # This matches the DB schema
    last_updated = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    openai_file_id = Column(String, nullable=True)
    
    # Define relationship to facility types
    facility_types = relationship(
        "FacilityType", 
        secondary=regulation_facility_types,
        back_populates="regulations"
    )
    
    # Define relationship to user documents
    user_documents = relationship("UserDocument", back_populates="regulation")
    
    def __repr__(self):
        return f"<Regulation(id={self.id}, state={self.state_territory}, title={self.document_title})>" 