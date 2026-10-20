"""
Manager Control Schemas
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ManagerOverrideRequestCreate(BaseModel):
    action_type: str
    payload: Dict[str, Any]


class ManagerOverrideResolution(BaseModel):
    resolution_notes: Optional[str] = None


class ManagerOverrideResponse(BaseModel):
    id: int
    facility_id: int
    requested_by_user_id: int
    approved_by_user_id: Optional[int]
    status: str
    action_type: str
    payload: Dict[str, Any]
    created_at: datetime
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]

    class Config:
        from_attributes = True

