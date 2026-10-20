"""
Support Ticket Schemas Module

This module defines Pydantic schemas for customer support ticket operations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.support_ticket import (
    TicketStatus,
    TicketPriority,
    TicketCategory,
    SupportTier,
    CommenterType,
)


# --- Support Ticket Schemas ---
class SupportTicketBase(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: TicketCategory = Field(default=TicketCategory.OTHER)
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM)
    tags: Optional[List[str]] = Field(default_factory=list)
    attachments: Optional[List[str]] = Field(default_factory=list)


class SupportTicketCreate(SupportTicketBase):
    facility_id: Optional[int] = None


class SupportTicketUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    category: Optional[TicketCategory] = None
    support_tier_required: Optional[SupportTier] = None
    assigned_to_account_id: Optional[int] = None
    tags: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    escalation_reason: Optional[str] = None
    internal_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None


class SupportTicketOut(SupportTicketBase):
    id: int
    ticket_number: str
    status: TicketStatus
    support_tier_required: SupportTier
    user_id: Optional[int]
    facility_id: Optional[int]
    assigned_to_account_id: Optional[int]
    auto_attempts: int
    escalation_reason: Optional[str]
    internal_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    last_customer_reply_at: Optional[datetime]
    last_support_reply_at: Optional[datetime]
    assigned_to_username: Optional[str] = None

    class Config:
        from_attributes = True


# --- Support Ticket Comment Schemas ---
class SupportTicketCommentBase(BaseModel):
    comment_text: str = Field(..., min_length=1)
    is_internal: bool = Field(default=False)


class SupportTicketCommentCreate(SupportTicketCommentBase):
    pass


class SupportTicketCommentOut(SupportTicketCommentBase):
    id: int
    ticket_id: int
    commenter_type: CommenterType
    commenter_id: Optional[int]
    created_at: datetime
    commenter_name: Optional[str] = None

    class Config:
        from_attributes = True


# --- Support Agent Profile Schemas ---
class SupportAgentProfileBase(BaseModel):
    support_tier: SupportTier = Field(default=SupportTier.BEGINNER)
    specialization_tags: Optional[List[str]] = Field(default_factory=list)
    max_concurrent_tickets: int = Field(default=5, ge=1, le=50)
    is_active: bool = Field(default=True)


class SupportAgentProfileCreate(SupportAgentProfileBase):
    account_id: int


class SupportAgentProfileUpdate(BaseModel):
    support_tier: Optional[SupportTier] = None
    specialization_tags: Optional[List[str]] = None
    max_concurrent_tickets: Optional[int] = Field(None, ge=1, le=50)
    is_active: Optional[bool] = None


class SupportAgentProfileOut(SupportAgentProfileBase):
    id: int
    account_id: int
    created_at: datetime
    updated_at: datetime
    account_username: Optional[str] = None
    account_email: Optional[str] = None

    class Config:
        from_attributes = True


# --- Ticket Assignment Schemas ---
class TicketAssignmentRequest(BaseModel):
    assigned_to_account_id: int


class TicketEscalationRequest(BaseModel):
    escalation_reason: str = Field(..., min_length=1, max_length=255)
    target_tier: Optional[SupportTier] = None


class TicketResolutionRequest(BaseModel):
    resolution_summary: Optional[str] = None
    internal_notes: Optional[str] = None


# --- Analytics Schemas ---
class SupportAnalyticsOut(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    escalated_tickets: int
    tickets_by_priority: Dict[str, int]
    tickets_by_category: Dict[str, int]
    tickets_by_tier: Dict[str, int]
    average_resolution_time_hours: Optional[float]
    tickets_by_agent: Dict[str, int]
    recent_tickets: List[SupportTicketOut]
    # SLA metrics
    sla_breached_tickets: int = 0
    average_response_time_hours: Optional[float] = None
    sla_compliance_rate: Optional[float] = None
    tickets_requiring_attention: int = 0
