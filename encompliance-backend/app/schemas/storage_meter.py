"""
Storage Meter Schemas

Defines API response models for facility storage usage.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StorageUsageEventSchema(BaseModel):
    id: int
    resource_type: str = Field(..., description="Document, assignment_image, etc.")
    resource_id: int
    delta_bytes: int
    source: str
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="event_metadata")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class StorageUsageSummary(BaseModel):
    facility_id: int
    billing_period_start: datetime
    billing_period_end: datetime
    tier_name: str
    included_bytes: int
    used_bytes: int
    overage_bytes: int
    percent_used: float
    alert_level: Optional[str] = None
    overage_rate: float
    available_bytes: int
    recommended_tier: Optional[str] = None
    events: List[StorageUsageEventSchema] = []

    class Config:
        from_attributes = True

