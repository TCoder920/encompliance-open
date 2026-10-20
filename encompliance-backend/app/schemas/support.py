"""
Support Ticket Schemas
----------------------
Pydantic models for support ticket operations across both the customer-facing
and support agent experiences.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class SupportTicketStatus(str, Enum):
    open = "open"
    triaging = "triaging"
    in_progress = "in_progress"
    waiting_customer = "waiting_customer"
    resolved = "resolved"
    closed = "closed"
    escalated = "escalated"


class SupportTicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class SupportTicketCategory(str, Enum):
    general = "general"
    billing = "billing"
    technical = "technical"
    training = "training"
    compliance = "compliance"
    feature_request = "feature_request"
    account = "account"
    other = "other"


class SupportTier(str, Enum):
    beginner = "beginner"
    mid = "mid"
    senior = "senior"


class SupportTicketBase(BaseModel):
    subject: str = Field(..., max_length=255)
    description: str
    priority: SupportTicketPriority = SupportTicketPriority.low
    category: SupportTicketCategory = SupportTicketCategory.general
    tags: List[str] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)


class SupportTicketCreate(SupportTicketBase):
    facility_id: Optional[int] = None
    support_tier_required: SupportTier = SupportTier.beginner


class SupportTicketAdminCreate(SupportTicketCreate):
    user_id: Optional[int] = None


class SupportTicketUpdate(BaseModel):
    status: Optional[SupportTicketStatus] = None
    priority: Optional[SupportTicketPriority] = None
    support_tier_required: Optional[SupportTier] = None
    assigned_agent_id: Optional[int] = None
    resolution_summary: Optional[str] = None
    tags: Optional[List[str]] = None


class SupportTicketCommentCreate(BaseModel):
    body: str
    is_internal: bool = False
    attachments: List[Dict[str, Any]] = Field(default_factory=list)


class SupportTicketCommentResponse(BaseModel):
    id: int
    ticket_id: int
    author_type: str
    author_id: Optional[int]
    body: str
    is_internal: bool
    attachments: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class SupportTicketResponse(BaseModel):
    id: int
    ticket_number: str
    user_id: Optional[int]
    facility_id: Optional[int]
    subject: str
    description: str
    status: SupportTicketStatus
    priority: SupportTicketPriority
    category: SupportTicketCategory
    support_tier_required: SupportTier
    assigned_agent_id: Optional[int]
    tags: List[str]
    attachments: List[Dict[str, Any]]
    auto_attempts: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    comments: List[SupportTicketCommentResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SupportAgentBase(BaseModel):
    admin_user_id: int
    display_name: Optional[str] = None
    tier: SupportTier = SupportTier.beginner
    specialization_tags: List[str] = Field(default_factory=list)
    max_concurrent_tickets: int = 10
    is_active: bool = True


class SupportAgentCreate(SupportAgentBase):
    pass


class SupportAgentUpdate(BaseModel):
    display_name: Optional[str] = None
    tier: Optional[SupportTier] = None
    specialization_tags: Optional[List[str]] = None
    max_concurrent_tickets: Optional[int] = None
    is_active: Optional[bool] = None


class SupportAgentResponse(BaseModel):
    id: int
    admin_user_id: int
    display_name: Optional[str]
    tier: SupportTier
    specialization_tags: List[str]
    max_concurrent_tickets: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

