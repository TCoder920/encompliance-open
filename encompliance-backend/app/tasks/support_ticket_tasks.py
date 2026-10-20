"""
Support Ticket Background Tasks
--------------------------------
Background tasks for support ticket automation including SLA monitoring
and auto-escalation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SupportPortalSessionLocal
from app.models.support_ticket import SupportTicket, TicketStatus
from app.services.sla_service import SLAService
from app.services.support_ticket_notification_service import SupportTicketNotificationService

logger = logging.getLogger(__name__)


async def monitor_sla_breaches():
    """Background task to monitor and handle SLA breaches."""
    db = SupportPortalSessionLocal()
    try:
        breached_tickets = SLAService.check_sla_breaches(db)
        
        if breached_tickets:
            logger.warning(f"Found {len(breached_tickets)} tickets with SLA breaches")
            for ticket in breached_tickets:
                # Auto-escalate breached tickets
                if ticket.support_tier_required.value != "senior":
                    from app.models.support_ticket import SupportTier
                    tier_order = {SupportTier.BEGINNER: 1, SupportTier.MID: 2, SupportTier.SENIOR: 3}
                    current_tier_order = tier_order.get(ticket.support_tier_required, 1)
                    if current_tier_order < 3:
                        next_tier = SupportTier.MID if current_tier_order == 1 else SupportTier.SENIOR
                        ticket.support_tier_required = next_tier
                        ticket.status = TicketStatus.ESCALATED
                        ticket.escalation_reason = f"Auto-escalated due to SLA breach"
                        ticket.assigned_to_account_id = None
                        db.commit()
                        logger.info(f"Auto-escalated breached ticket {ticket.ticket_number} to {next_tier.value}")
    except Exception as e:
        logger.error(f"Error in SLA monitoring task: {e}")
        db.rollback()
    finally:
        db.close()


async def auto_escalate_stale_tickets():
    """Background task to auto-escalate stale tickets."""
    db = SupportPortalSessionLocal()
    try:
        # Escalate tickets that haven't been updated in 48 hours
        escalated = SLAService.auto_escalate_stale_tickets(db, stale_hours=48, auto_escalate=True)
        
        if escalated:
            logger.info(f"Auto-escalated {len(escalated)} stale tickets")
            # Notify about escalations
            for ticket in escalated:
                await SupportTicketNotificationService.notify_ticket_escalated(db, ticket)
    except Exception as e:
        logger.error(f"Error in auto-escalation task: {e}")
        db.rollback()
    finally:
        db.close()


async def run_support_ticket_tasks():
    """Run all support ticket background tasks."""
    logger.info("Starting support ticket background tasks")
    
    # Run SLA monitoring
    await monitor_sla_breaches()
    
    # Run auto-escalation
    await auto_escalate_stale_tickets()
    
    logger.info("Completed support ticket background tasks")


def schedule_support_ticket_tasks():
    """Schedule support ticket background tasks (call this from your scheduler)."""
    asyncio.create_task(run_support_ticket_tasks())

