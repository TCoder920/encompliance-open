"""
Audit Schemas
"""

from datetime import datetime
from typing import Optional, Any, Dict

from pydantic import BaseModel, Field


class ActivityAuditEntry(BaseModel):
    id: int
    actor_user_id: Optional[int]
    facility_id: Optional[int]
    event_type: str
    description: str
    metadata: Optional[Dict[str, Any]] = Field(alias="entry_metadata")
    created_at: datetime
    entry_hash: str

    class Config:
        from_attributes = True
        populate_by_name = True

