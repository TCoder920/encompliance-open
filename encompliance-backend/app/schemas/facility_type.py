"""
Facility Type Schemas Module

This module defines Pydantic schemas for facility type data validation and serialization
in the EnCompliance application.

Key functionalities:
- Facility type data validation
- Facility type creation schemas
- Facility type response schemas
- Facility type list management
- Facility type identification

Dependencies:
- pydantic: For data validation and serialization
"""

from pydantic import BaseModel
from typing import List, Optional

class FacilityTypeBase(BaseModel):
    name: str

class FacilityTypeCreate(FacilityTypeBase):
    pass

class FacilityType(FacilityTypeBase):
    id: int
    
    class Config:
        from_attributes = True

# Response schema for GET /facility-types
class FacilityTypesResponse(BaseModel):
    facility_types: List[str] 