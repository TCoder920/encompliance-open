"""
SLA Service
-----------
Service for managing Service Level Agreement (SLA) tracking and enforcement
for support tickets.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.support_ticket import SupportTicket, TicketStatus, TicketPriority, SupportTier

logger = logging.getLogger(__name__)

# SLA targets in hours
SLA_RESPONSE_TIME = {
    TicketPriority.URGENT: 1,  # 1 hour
    TicketPriority.HIGH: 4,     # 4 hours
    TicketPriority.MEDIUM: 24,  # 24 hours
    TicketPriority.LOW: 72,     # 72 hours
}

SLA_RESOLUTION_TIME = {
    TicketPriority.URGENT: 4,   # 4 hours
    TicketPriority.HIGH: 24,    # 24 hours
    TicketPriority.MEDIUM: 72,  # 72 hours
    TicketPriority.LOW: 168,    # 7 days
}


class SLAService:
    """Service for SLA tracking and enforcement."""
    
    @staticmethod
    def calculate_sla_deadlines(ticket: SupportTicket) -> tuple[Optional[datetime], Optional[datetime]]:
        """Calculate SLA response and resolution deadlines based on ticket priority."""
        if ticket.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            return None, None
        
        response_hours = SLA_RESPONSE_TIME.get(ticket.priority, 24)
        resolution_hours = SLA_RESOLUTION_TIME.get(ticket.priority, 72)
        
        response_deadline = ticket.created_at + timedelta(hours=response_hours)
        resolution_deadline = ticket.created_at + timedelta(hours=resolution_hours)
        
        return response_deadline, resolution_deadline
    
    @staticmethod
    def update_ticket_sla(db: Session, ticket: SupportTicket) -> SupportTicket:
        """Update SLA deadlines and breach status for a ticket."""
        if ticket.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            ticket.sla_response_deadline = None
            ticket.sla_resolution_deadline = None
            ticket.sla_breached = False
            return ticket
        
        # Calculate deadlines if not set
        if not ticket.sla_response_deadline or not ticket.sla_resolution_deadline:
            response_deadline, resolution_deadline = SLAService.calculate_sla_deadlines(ticket)
            ticket.sla_response_deadline = response_deadline
            ticket.sla_resolution_deadline = resolution_deadline
        
        # Check for SLA breaches
        now = datetime.utcnow()
        breached = False
        
        # Check response SLA
        if ticket.sla_response_deadline and not ticket.first_response_at:
            if now > ticket.sla_response_deadline:
                breached = True
                logger.warning(f"Ticket {ticket.ticket_number} breached response SLA")
        
        # Check resolution SLA
        if ticket.sla_resolution_deadline:
            if now > ticket.sla_resolution_deadline:
                breached = True
                logger.warning(f"Ticket {ticket.ticket_number} breached resolution SLA")
        
        ticket.sla_breached = breached
        db.commit()
        return ticket
    
    @staticmethod
    def mark_first_response(db: Session, ticket: SupportTicket) -> SupportTicket:
        """Mark the first response time for a ticket."""
        if not ticket.first_response_at:
            ticket.first_response_at = datetime.utcnow()
            db.commit()
            logger.info(f"First response marked for ticket {ticket.ticket_number}")
        return ticket
    
    @staticmethod
    def check_sla_breaches(db: Session) -> list[SupportTicket]:
        """Check all open tickets for SLA breaches and return breached tickets."""
        open_tickets = db.query(SupportTicket).filter(
            SupportTicket.status.in_([
                TicketStatus.OPEN,
                TicketStatus.IN_PROGRESS,
                TicketStatus.ESCALATED
            ])
        ).all()
        
        breached_tickets = []
        for ticket in open_tickets:
            SLAService.update_ticket_sla(db, ticket)
            if ticket.sla_breached:
                breached_tickets.append(ticket)
        
        return breached_tickets
    
    @staticmethod
    def auto_escalate_stale_tickets(
        db: Session,
        stale_hours: int = 48,
        auto_escalate: bool = True
    ) -> list[SupportTicket]:
        """Find and optionally escalate tickets that haven't been updated in specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=stale_hours)
        
        stale_tickets = db.query(SupportTicket).filter(
            SupportTicket.status.in_([
                TicketStatus.OPEN,
                TicketStatus.IN_PROGRESS
            ]),
            SupportTicket.updated_at < cutoff_time,
            SupportTicket.support_tier_required != SupportTier.SENIOR
        ).all()
        
        escalated = []
        for ticket in stale_tickets:
            if auto_escalate:
                # Escalate to next tier
                tier_order = {SupportTier.BEGINNER: 1, SupportTier.MID: 2, SupportTier.SENIOR: 3}
                current_tier_order = tier_order.get(ticket.support_tier_required, 1)
                if current_tier_order < 3:
                    next_tier = SupportTier.MID if current_tier_order == 1 else SupportTier.SENIOR
                    ticket.support_tier_required = next_tier
                    ticket.status = TicketStatus.ESCALATED
                    ticket.escalation_reason = f"Auto-escalated after {stale_hours} hours of inactivity"
                    ticket.assigned_to_account_id = None  # Unassign on escalation
                    escalated.append(ticket)
                    logger.info(f"Auto-escalated ticket {ticket.ticket_number} to {next_tier.value}")
        
        if escalated:
            db.commit()
        
        return escalated

