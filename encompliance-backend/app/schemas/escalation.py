"""
Escalation Schemas
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class EscalationStepPayload(BaseModel):
    delay_minutes: int = 0
    channel: str = Field(default="email", description="email|sms|push|pager")
    target_role: Optional[str] = None
    target_user_id: Optional[int] = None
    custom_recipient: Optional[str] = None
    message_template: Optional[str] = None


class EscalationPolicyCreate(BaseModel):
    name: str
    incident_type: str
    description: Optional[str] = None
    steps: List[EscalationStepPayload]


class EscalationStepResponse(EscalationStepPayload):
    id: int
    step_number: int

    class Config:
        from_attributes = True


class EscalationPolicyResponse(BaseModel):
    id: int
    facility_id: int
    name: str
    incident_type: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    steps: List[EscalationStepResponse]

    class Config:
        from_attributes = True


class EscalationIncidentResponse(BaseModel):
    id: int
    policy_id: int
    status: str
    triggered_at: datetime
    last_step_sent: Optional[int] = None
    metadata: Optional[dict] = Field(default=None, alias="incident_metadata")

    class Config:
        from_attributes = True
        populate_by_name = True

