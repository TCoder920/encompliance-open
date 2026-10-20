"""
Support Ticket Notification Service
-----------------------------------
Service for sending notifications related to support ticket events.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.support_portal_account import SupportPortalAccount
from app.models.support_ticket import SupportTicket
from app.models.notification import NotificationType, NotificationPriority
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService
from app.database import SessionLocal
from app.utils.email_utils import send_email
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SupportTicketNotificationService:
    """Service for handling support ticket-related notifications."""
    
    @staticmethod
    async def notify_ticket_created(
        db: Session,
        ticket: SupportTicket,
        user_db: Optional[Session] = None,
    ):
        """Notify customer when their ticket is created."""
        if not ticket.user_id:
            return
        
        try:
            # Get user from main database
            if user_db is None:
                user_db = SessionLocal()
            
            user = user_db.query(User).filter(User.id == ticket.user_id).first()
            if not user:
                logger.warning(f"User {ticket.user_id} not found for ticket notification")
                return
            
            notification_data = NotificationCreate(
                title=f"Support Ticket Created: {ticket.ticket_number}",
                message=f"Your support ticket '{ticket.subject}' has been created and is being reviewed.",
                type=NotificationType.SUPPORT_TICKET_CREATED,
                priority=NotificationPriority.MEDIUM,
                related_id=str(ticket.id),
                related_type="support_ticket",
                action_url=f"/support/tickets/{ticket.id}",
            )
            
            await NotificationService.create_notification(
                user_db,
                notification_data,
                user.id,
                send_email=True,
                send_push=True,
            )
            logger.info(f"Ticket creation notification sent to user {user.id} for ticket {ticket.ticket_number}")
        except Exception as e:
            logger.error(f"Failed to send ticket creation notification: {e}")
        finally:
            if user_db and user_db != db:
                user_db.close()
    
    @staticmethod
    async def notify_ticket_assigned(
        db: Session,
        ticket: SupportTicket,
        assigned_to_account_id: int,
    ):
        """Notify support agent when ticket is assigned to them."""
        try:
            account = db.query(SupportPortalAccount).filter(
                SupportPortalAccount.id == assigned_to_account_id
            ).first()
            
            if not account:
                logger.warning(f"Support account {assigned_to_account_id} not found")
                return
            
            # Send email notification to support agent
            settings = get_settings()
            support_portal_url = settings.FRONTEND_URL.replace("5174", "5200") if settings.FRONTEND_URL else "http://localhost:5200"
            
            subject = f"New Ticket Assigned: {ticket.ticket_number} - {ticket.subject}"
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #1e3a8a; color: white; padding: 20px; text-align: center; }}
                    .content {{ background-color: #f8fafc; padding: 30px; }}
                    .ticket-box {{ background-color: white; border: 1px solid #d1d5db; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                    .button {{ display: inline-block; background-color: #1e3a8a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .priority {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; }}
                    .priority-urgent {{ background-color: #fee2e2; color: #991b1b; }}
                    .priority-high {{ background-color: #fed7aa; color: #9a3412; }}
                    .priority-medium {{ background-color: #fef3c7; color: #92400e; }}
                    .priority-low {{ background-color: #dbeafe; color: #1e40af; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>New Support Ticket Assigned</h1>
                    </div>
                    <div class="content">
                        <p>Hello {account.username},</p>
                        <p>A new support ticket has been assigned to you:</p>
                        <div class="ticket-box">
                            <h3>{ticket.subject}</h3>
                            <p><strong>Ticket Number:</strong> {ticket.ticket_number}</p>
                            <p><strong>Priority:</strong> <span class="priority priority-{ticket.priority.value}">{ticket.priority.value.upper()}</span></p>
                            <p><strong>Category:</strong> {ticket.category.value}</p>
                            <p><strong>Status:</strong> {ticket.status.value}</p>
                            <p><strong>Description:</strong></p>
                            <p>{ticket.description[:200]}{'...' if len(ticket.description) > 200 else ''}</p>
                        </div>
                        <div style="text-align: center;">
                            <a href="{support_portal_url}/tickets/{ticket.id}" class="button">View Ticket</a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            try:
                send_email(
                    subject=subject,
                    recipient=account.email,
                    template_name="support_ticket_assigned",
                    context={
                        "agent_name": account.username,
                        "ticket_number": ticket.ticket_number,
                        "ticket_subject": ticket.subject,
                        "ticket_description": ticket.description[:200] + ("..." if len(ticket.description) > 200 else ""),
                        "ticket_priority": ticket.priority.value,
                        "ticket_category": ticket.category.value,
                        "ticket_status": ticket.status.value,
                        "ticket_url": f"{support_portal_url}/tickets/{ticket.id}",
                        "__template_override__": html_content
                    }
                )
                logger.info(f"Ticket assignment email sent to {account.email} for ticket {ticket.ticket_number}")
            except Exception as email_err:
                logger.error(f"Failed to send assignment email: {email_err}")
            
            logger.info(f"Ticket {ticket.ticket_number} assigned to agent {account.username}")
        except Exception as e:
            logger.error(f"Failed to send ticket assignment notification: {e}")
    
    @staticmethod
    async def notify_ticket_comment(
        db: Session,
        ticket: SupportTicket,
        commenter_type: str,
        commenter_id: Optional[int],
        user_db: Optional[Session] = None,
    ):
        """Notify relevant parties when a comment is added to a ticket."""
        try:
            if user_db is None:
                user_db = SessionLocal()
            
            # If support agent commented, notify customer
            if commenter_type == "support" and ticket.user_id:
                user = user_db.query(User).filter(User.id == ticket.user_id).first()
                if user:
                    account = db.query(SupportPortalAccount).filter(
                        SupportPortalAccount.id == commenter_id
                    ).first() if commenter_id else None
                    
                    agent_name = account.username if account else "Support Team"
                    
                    notification_data = NotificationCreate(
                        title=f"New Update on Ticket {ticket.ticket_number}",
                        message=f"{agent_name} has added a comment to your support ticket '{ticket.subject}'.",
                        type=NotificationType.SUPPORT_TICKET_COMMENT,
                        priority=NotificationPriority.MEDIUM,
                        related_id=str(ticket.id),
                        related_type="support_ticket",
                        action_url=f"/support/tickets/{ticket.id}",
                    )
                    
                    await NotificationService.create_notification(
                        user_db,
                        notification_data,
                        user.id,
                        send_email=True,
                        send_push=True,
                    )
            
            # If customer commented, notify assigned agent (if any)
            elif commenter_type == "customer" and ticket.assigned_to_account_id:
                logger.info(f"Customer comment on ticket {ticket.ticket_number} - agent {ticket.assigned_to_account_id} should be notified")
                # TODO: Add email notification for support agents if needed
        except Exception as e:
            logger.error(f"Failed to send ticket comment notification: {e}")
        finally:
            if user_db and user_db != db:
                user_db.close()
    
    @staticmethod
    async def notify_ticket_resolved(
        db: Session,
        ticket: SupportTicket,
        user_db: Optional[Session] = None,
    ):
        """Notify customer when ticket is resolved."""
        if not ticket.user_id:
            return
        
        try:
            if user_db is None:
                user_db = SessionLocal()
            
            user = user_db.query(User).filter(User.id == ticket.user_id).first()
            if not user:
                return
            
            notification_data = NotificationCreate(
                title=f"Support Ticket Resolved: {ticket.ticket_number}",
                message=f"Your support ticket '{ticket.subject}' has been resolved.",
                type=NotificationType.SUPPORT_TICKET_RESOLVED,
                priority=NotificationPriority.MEDIUM,
                related_id=str(ticket.id),
                related_type="support_ticket",
                action_url=f"/support/tickets/{ticket.id}",
            )
            
            await NotificationService.create_notification(
                user_db,
                notification_data,
                user.id,
                send_email=True,
                send_push=True,
            )
            logger.info(f"Ticket resolution notification sent to user {user.id} for ticket {ticket.ticket_number}")
        except Exception as e:
            logger.error(f"Failed to send ticket resolution notification: {e}")
        finally:
            if user_db and user_db != db:
                user_db.close()
    
    @staticmethod
    async def notify_ticket_escalated(
        db: Session,
        ticket: SupportTicket,
    ):
        """Notify senior support agents when ticket is escalated."""
        try:
            logger.info(f"Ticket {ticket.ticket_number} escalated to tier {ticket.support_tier_required}")
            # TODO: Add email notification to senior agents if needed
        except Exception as e:
            logger.error(f"Failed to send ticket escalation notification: {e}")

