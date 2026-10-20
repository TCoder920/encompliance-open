"""
Staff Directory Schemas
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class StaffDirectoryEntry(BaseModel):
    staff_member_id: int
    assignment_id: int
    full_name: str
    email: str
    department: Optional[str] = None
    role: Optional[str] = Field(None, description="Staff role classification")
    status: str
    facility_id: int
    facility_name: str
    assigned_at: datetime


class StaffDirectoryListResponse(BaseModel):
    items: List[StaffDirectoryEntry]
    page: int
    page_size: int
    total: int


class AssignStaffPayload(BaseModel):
    staff_member_id: int
    facility_id: int


class TransferRequestPayload(BaseModel):
    staff_member_id: int
    source_facility_id: int
    target_facility_id: int
    reason: Optional[str] = None


class TransferResolutionPayload(BaseModel):
    resolution_notes: Optional[str] = None


class StaffTransferResponse(BaseModel):
    id: int
    staff_member_id: int
    source_facility_id: int
    target_facility_id: int
    status: str
    reason: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

