"""
Team Communication Schemas

Defines request/response models for chat channels, messages, and email campaigns.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TeamChannelCreate(BaseModel):
    name: str = Field(..., max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    is_private: bool = False


class TeamChannelResponse(TeamChannelCreate):
    id: int
    facility_id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class TeamMessageCreate(BaseModel):
    content: str = Field(..., max_length=4000)
    attachments: Optional[List[dict]] = None
    mentions: Optional[List[int]] = None


class TeamMessageResponse(TeamMessageCreate):
    id: int
    channel_id: int
    facility_id: int
    sender_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EmailCampaignCreate(BaseModel):
    subject: str = Field(..., max_length=200)
    body: str = Field(..., max_length=6000)
    template_type: Optional[str] = Field(None, max_length=50)
    target_roles: List[str] = Field(default_factory=list)
    scheduled_for: Optional[datetime] = None


class EmailCampaignResponse(EmailCampaignCreate):
    id: int
    facility_id: int
    created_by: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

