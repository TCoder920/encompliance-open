"""
Policy Distribution Schemas
"""

from typing import List
from pydantic import BaseModel, Field


class PolicyDistributionRequest(BaseModel):
    policy_id: int
    facility_ids: List[int] = Field(..., min_items=1)
    notes: str = Field("", max_length=1000)


class PolicyDistributionResponse(BaseModel):
    policy_id: int
    facilities_targeted: int
    status: str

