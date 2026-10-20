"""
Training Program Model Module

This module defines the TrainingProgram database model for the EnCompliance application.
It manages training programs available to facility staff.

Key functionalities:
- Training program metadata and content
- Facility type associations
- Certification requirements
- Training material management
- Completion tracking
- Annual renewal requirements

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Association table for many-to-many relationship between TrainingProgram and FacilityType
training_program_facility_types = Table(
    'training_program_facility_types',
    Base.metadata,
    Column('training_program_id', Integer, ForeignKey('training_programs.id'), primary_key=True),
    Column('facility_type_id', Integer, ForeignKey('facility_types.id'), primary_key=True)
)

class TrainingProgram(Base):
    __tablename__ = "training_programs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # Safety, Compliance, Technical, etc.
    
    # Program requirements
    is_mandatory = Column(Boolean, default=False)
    requires_certification = Column(Boolean, default=False)
    certification_valid_months = Column(Integer, default=12)  # Certification validity period
    
    # Content and delivery
    estimated_duration_minutes = Column(Integer, nullable=True)
    delivery_method = Column(String(50), default="online")  # online, in_person, hybrid
    prerequisites = Column(JSON, nullable=True)  # List of prerequisite training IDs
    
    # Scheduling and reminders
    reminder_schedule_days = Column(JSON, default=[30, 14, 7, 1])  # Days before due date
    auto_assign_new_staff = Column(Boolean, default=False)
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    facility_types = relationship(
        "FacilityType", 
        secondary=training_program_facility_types,
        back_populates="training_programs"
    )
    creator = relationship("User", foreign_keys=[created_by])
    training_materials = relationship("TrainingMaterial", back_populates="training_program", cascade="all, delete-orphan")
    training_assignments = relationship("TrainingAssignment", back_populates="training_program", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TrainingProgram(id={self.id}, title={self.title}, mandatory={self.is_mandatory})>" 