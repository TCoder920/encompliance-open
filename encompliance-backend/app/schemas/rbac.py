"""
RBAC Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    scope: str = Field(default="facility")
    permissions: List[str] = Field(default_factory=list)


class RoleResponse(RoleCreate):
    id: int

    class Config:
        from_attributes = True


class RoleAssignmentCreate(BaseModel):
    user_id: int
    role_id: int
    facility_id: Optional[int] = None

