"""
Support Ticket Service Layer
----------------------------
Encapsulates business logic for ticket lifecycle events so the API layer stays thin.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.support_ticket import SupportTicket, SupportTicketComment, SupportAgent
from app.schemas.support import (
    SupportTicketCreate,
    SupportTicketUpdate,
    SupportTicketResponse,
    SupportTicketCommentCreate,
    SupportAgentCreate,
    SupportAgentUpdate,
    SupportAgentResponse,
)


class SupportTicketService:
    TICKET_PREFIX = "SUP"

    @staticmethod
    def _generate_ticket_number(db: Session) -> str:
        today_stamp = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"{SupportTicketService.TICKET_PREFIX}-{today_stamp}"
        latest = (
            db.query(SupportTicket.ticket_number)
            .filter(SupportTicket.ticket_number.like(f"{prefix}-%"))
            .order_by(SupportTicket.ticket_number.desc())
            .first()
        )
        if not latest:
            next_sequence = 1
        else:
            try:
                next_sequence = int(latest[0].split("-")[-1]) + 1
            except (ValueError, IndexError):
                next_sequence = 1
        return f"{prefix}-{next_sequence:04d}"

    @staticmethod
    def create_ticket(
        db: Session,
        payload: SupportTicketCreate,
        *,
        user_id: Optional[int],
    ) -> SupportTicket:
        ticket_number = SupportTicketService._generate_ticket_number(db)
        ticket = SupportTicket(
            ticket_number=ticket_number,
            user_id=user_id,
            facility_id=payload.facility_id,
            subject=payload.subject,
            description=payload.description,
            priority=payload.priority.value,
            category=payload.category.value,
            support_tier_required=payload.support_tier_required.value,
            tags=payload.tags or [],
            attachments=payload.attachments or [],
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def update_ticket(db: Session, ticket: SupportTicket, payload: SupportTicketUpdate) -> SupportTicket:
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in {"status", "priority", "support_tier_required"} and hasattr(value, "value"):
                value = value.value
            setattr(ticket, field, value)
        ticket.updated_at = datetime.utcnow()
        if ticket.status in {"resolved", "closed"} and not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def add_comment(
        db: Session,
        ticket: SupportTicket,
        *,
        author_type: str,
        author_id: Optional[int],
        payload: SupportTicketCommentCreate,
    ) -> SupportTicketComment:
        comment = SupportTicketComment(
            ticket_id=ticket.id,
            author_type=author_type,
            author_id=author_id,
            body=payload.body,
            is_internal=payload.is_internal,
            attachments=payload.attachments or [],
        )
        ticket.updated_at = datetime.utcnow()
        if author_type == "customer":
            ticket.last_customer_reply_at = datetime.utcnow()
        else:
            ticket.last_agent_reply_at = datetime.utcnow()
        db.add(comment)
        db.add(ticket)
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def assign_ticket(db: Session, ticket: SupportTicket, agent_id: int) -> SupportTicket:
        ticket.assigned_agent_id = agent_id
        ticket.status = "in_progress"
        ticket.updated_at = datetime.utcnow()
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def get_ticket_response(ticket: SupportTicket) -> SupportTicketResponse:
        return SupportTicketResponse.from_orm(ticket)


class SupportAgentService:
    @staticmethod
    def create_agent(db: Session, payload: SupportAgentCreate) -> SupportAgent:
        agent = SupportAgent(
            admin_user_id=payload.admin_user_id,
            display_name=payload.display_name,
            tier=payload.tier.value,
            specialization_tags=payload.specialization_tags,
            max_concurrent_tickets=payload.max_concurrent_tickets,
            is_active=payload.is_active,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def update_agent(db: Session, agent: SupportAgent, payload: SupportAgentUpdate) -> SupportAgent:
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "tier" and hasattr(value, "value"):
                value = value.value
            setattr(agent, field, value)
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def get_agent_response(agent: SupportAgent) -> SupportAgentResponse:
        return SupportAgentResponse.from_orm(agent)

