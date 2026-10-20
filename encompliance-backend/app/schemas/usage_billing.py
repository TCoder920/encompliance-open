"""
Usage Billing Schemas
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel


class UsageLogResponse(BaseModel):
    tokens_used: int
    cost_usd: float
    created_at: datetime
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    model_name: str | None = None

    class Config:
        from_attributes = True


class UsageSummary(BaseModel):
    month_tokens: int
    month_cost: float
    logs: List[UsageLogResponse]

