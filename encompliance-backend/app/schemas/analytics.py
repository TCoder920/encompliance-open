"""
Analytics Schemas
"""

from typing import List
from pydantic import BaseModel


class FacilityMetric(BaseModel):
    facility_id: int
    facility_name: str
    active_staff: int
    open_policies: int


class CrossFacilityAnalytics(BaseModel):
    total_facilities: int
    staff_count: int
    policy_distribution_pending: int
    facilities: List[FacilityMetric]

