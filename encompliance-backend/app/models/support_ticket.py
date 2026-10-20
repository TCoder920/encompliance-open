"""
Support Ticket Domain Models
----------------------------
Defines customer support ticketing entities that live inside the admin/support
portal database.
"""

from __future__ import annotations

import enum
import uuid
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import SupportPortalBase


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(str, enum.Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    TRAINING = "training"
    ACCOUNT = "account"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class SupportTier(str, enum.Enum):
    BEGINNER = "beginner"
    MID = "mid"
    SENIOR = "senior"


class CommenterType(str, enum.Enum):
    CUSTOMER = "customer"
    SUPPORT = "support"
    SYSTEM = "system"


def generate_ticket_number() -> str:
    """Generate a human-friendly ticket number."""
    return f"TKT-{uuid.uuid4().hex[:10].upper()}"


class SupportTicket(SupportPortalBase):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(24), unique=True, index=True, default=generate_ticket_number)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.OPEN)
    priority = Column(Enum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM)
    category = Column(Enum(TicketCategory), nullable=False, default=TicketCategory.OTHER)
    support_tier_required = Column(Enum(SupportTier), nullable=False, default=SupportTier.BEGINNER)
    user_id = Column(Integer, nullable=True, index=True)
    facility_id = Column(Integer, nullable=True, index=True)
    assigned_to_account_id = Column(
        Integer,
        ForeignKey("support_portal_users.id"),
        nullable=True,
        index=True,
    )
    tags = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)
    auto_attempts = Column(Integer, default=0)
    escalation_reason = Column(String(255), nullable=True)
    internal_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    last_customer_reply_at = Column(DateTime(timezone=True), nullable=True)
    last_support_reply_at = Column(DateTime(timezone=True), nullable=True)
    # SLA tracking fields
    first_response_at = Column(DateTime(timezone=True), nullable=True)
    sla_response_deadline = Column(DateTime(timezone=True), nullable=True)
    sla_resolution_deadline = Column(DateTime(timezone=True), nullable=True)
    sla_breached = Column(Boolean, default=False)

    assigned_to = relationship("SupportPortalAccount")
    comments = relationship(
        "SupportTicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportTicketComment.created_at",
    )

    def __repr__(self) -> str:
        return f"<SupportTicket ticket_number={self.ticket_number} status={self.status}>"


class SupportTicketComment(SupportPortalBase):
    __tablename__ = "support_ticket_comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False, index=True)
    commenter_type = Column(Enum(CommenterType), nullable=False, default=CommenterType.SUPPORT)
    commenter_id = Column(Integer, nullable=True)
    comment_text = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("SupportTicket", back_populates="comments")

    def __repr__(self) -> str:
        return f"<SupportTicketComment ticket_id={self.ticket_id} commenter_type={self.commenter_type}>"


class SupportAgentProfile(SupportPortalBase):
    __tablename__ = "support_agent_profiles"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(
        Integer,
        ForeignKey("support_portal_users.id"),
        unique=True,
        nullable=False,
    )
    support_tier = Column(Enum(SupportTier), default=SupportTier.BEGINNER, nullable=False)
    specialization_tags = Column(JSON, nullable=True)
    max_concurrent_tickets = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    support_account = relationship("SupportPortalAccount")

    def __repr__(self) -> str:
        return f"<SupportAgentProfile account_id={self.account_id} tier={self.support_tier}>"
