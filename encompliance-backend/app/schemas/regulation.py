"""
Regulation Schemas Module

This module defines Pydantic schemas for regulatory document data validation and serialization
in the EnCompliance application.

Key functionalities:
- Regulatory document data validation
- Facility type association schemas
- Document metadata validation
- State/territory tracking schemas
- Document versioning schemas

Dependencies:
- pydantic: For data validation and serialization
- datetime: For timestamp handling
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class RegulationBase(BaseModel):
    state_territory: str
    facility_type: Optional[str] = None
    is_default: bool = False
    document_title: str
    document_type: Optional[str] = None
    file_name: str
    document_filename: Optional[str] = None
    last_updated: Optional[date] = None

class RegulationCreate(RegulationBase):
    facility_type_names: List[str]

class Regulation(RegulationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RegulationWithFacilityTypes(Regulation):
    facility_types: List[str]
    
    class Config:
        from_attributes = True 