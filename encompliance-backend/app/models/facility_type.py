"""
Facility Type Model Module

This module defines the FacilityType database model and its association table
for the EnCompliance application. It manages facility types and their relationships
with regulatory documents and training programs.

Key functionalities:
- Facility type categorization
- Many-to-many relationship with regulations
- Many-to-many relationship with training programs
- Facility type naming and indexing
- Regulatory document associations
- Training program associations
- Facility type lookup and management

Dependencies:
- sqlalchemy: For database model definition
- sqlalchemy.orm: For relationship management
"""

from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# Association table for many-to-many relationship between Regulation and FacilityType
regulation_facility_types = Table(
    'regulation_facility_types',
    Base.metadata,
    Column('regulation_id', Integer, ForeignKey('regulations.id'), primary_key=True),
    Column('facility_type_id', Integer, ForeignKey('facility_types.id'), primary_key=True)
)

class FacilityType(Base):
    __tablename__ = "facility_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    
    # Define relationship to regulations
    regulations = relationship(
        "Regulation", 
        secondary=regulation_facility_types,
        back_populates="facility_types"
    )
    
    # Define relationship to training programs
    training_programs = relationship(
        "TrainingProgram",
        secondary="training_program_facility_types",
        back_populates="facility_types"
    )
    
    def __repr__(self):
        return f"<FacilityType(id={self.id}, name={self.name})>" 