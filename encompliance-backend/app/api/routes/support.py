"""
Consumer Support Routes
-----------------------
This module defines consumer-facing support ticket API endpoints.
Allows customers to create tickets and view their own tickets.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db, get_support_portal_db
from app.models.support_ticket import (
    SupportTicket,
    SupportTicketComment,
    TicketStatus,
    CommenterType,
)
from app.models.support_portal_account import SupportPortalAccount
from app.models.user import User
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketOut,
    SupportTicketCommentCreate,
    SupportTicketCommentOut,
)
from app.auth.dependencies import get_current_user
from app.services.support_ticket_notification_service import SupportTicketNotificationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/support", tags=["Support"])


@router.post("/tickets", response_model=SupportTicketOut, status_code=status.HTTP_201_CREATED)
async def create_support_ticket(
    ticket_in: SupportTicketCreate,
    request: Request,
    db: Session = Depends(get_db),
    support_db: Session = Depends(get_support_portal_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new support ticket as a customer."""
    # Use support_db for ticket creation since tickets are stored in the support portal database
    from app.models.support_ticket import TicketPriority, SupportTier
    
    # Determine initial tier based on priority
    initial_tier = SupportTier.BEGINNER
    if ticket_in.priority in [TicketPriority.HIGH, TicketPriority.URGENT]:
        initial_tier = SupportTier.MID
    
    # Auto-set facility_id if user has one
    facility_id = ticket_in.facility_id
    if facility_id is None and current_user.facility_id:
        facility_id = current_user.facility_id
    
    new_ticket = SupportTicket(
        subject=ticket_in.subject,
        description=ticket_in.description,
        category=ticket_in.category,
        priority=ticket_in.priority,
        support_tier_required=initial_tier,
        user_id=current_user.id,
        facility_id=facility_id,
        tags=ticket_in.tags or [],
        attachments=ticket_in.attachments or [],
    )
    support_db.add(new_ticket)
    support_db.commit()
    support_db.refresh(new_ticket)
    
    # Send notification to customer
    try:
        await SupportTicketNotificationService.notify_ticket_created(
            support_db,
            new_ticket,
            user_db=db,
        )
    except Exception as e:
        logger.error(f"Failed to send ticket creation notification: {e}")
        # Don't fail ticket creation if notification fails
    
    result = SupportTicketOut.model_validate(new_ticket)
    return result


@router.get("/tickets", response_model=List[SupportTicketOut])
async def get_my_tickets(
    status_filter: Optional[TicketStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    support_db: Session = Depends(get_support_portal_db),
    current_user: User = Depends(get_current_user),
):
    """Get all support tickets for the current user."""
    query = support_db.query(SupportTicket).filter(SupportTicket.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(SupportTicket.status == status_filter)
    
    tickets = query.order_by(SupportTicket.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for ticket in tickets:
        ticket_dict = SupportTicketOut.model_validate(ticket)
        if ticket.assigned_to_account_id:
            account = (
                support_db.query(SupportPortalAccount)
                .filter(SupportPortalAccount.id == ticket.assigned_to_account_id)
                .first()
            )
            if account:
                ticket_dict.assigned_to_username = account.username
        result.append(ticket_dict)
    
    return result


@router.get("/tickets/{ticket_id}", response_model=SupportTicketOut)
async def get_my_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    support_db: Session = Depends(get_support_portal_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific support ticket (only if owned by current user)."""
    ticket = support_db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or you do not have access to this ticket"
        )
    
    result = SupportTicketOut.model_validate(ticket)
    if ticket.assigned_to_account_id:
        account = (
            support_db.query(SupportPortalAccount)
            .filter(SupportPortalAccount.id == ticket.assigned_to_account_id)
            .first()
        )
        if account:
            result.assigned_to_username = account.username
    
    return result


@router.post("/tickets/{ticket_id}/comments", response_model=SupportTicketCommentOut, status_code=status.HTTP_201_CREATED)
async def add_ticket_comment(
    ticket_id: int,
    comment_in: SupportTicketCommentCreate,
    db: Session = Depends(get_db),
    support_db: Session = Depends(get_support_portal_db),
    current_user: User = Depends(get_current_user),
):
    """Add a comment to a support ticket (customer-facing)."""
    # Verify ticket ownership
    ticket = support_db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or you do not have access to this ticket"
        )
    
    # Customers cannot add internal comments
    if comment_in.is_internal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot create internal comments"
        )
    
    new_comment = SupportTicketComment(
        ticket_id=ticket_id,
        commenter_type=CommenterType.CUSTOMER,
        commenter_id=current_user.id,
        comment_text=comment_in.comment_text,
        is_internal=False,
    )
    support_db.add(new_comment)
    
    # Update ticket timestamp
    ticket.last_customer_reply_at = datetime.utcnow()
    
    support_db.commit()
    support_db.refresh(new_comment)
    
    # Notify assigned support agent if ticket is assigned
    try:
        await SupportTicketNotificationService.notify_ticket_comment(
            support_db,
            ticket,
            commenter_type="customer",
            commenter_id=current_user.id,
            user_db=db,
        )
    except Exception as e:
        logger.error(f"Failed to send ticket comment notification: {e}")
    
    result = SupportTicketCommentOut.model_validate(new_comment)
    result.commenter_name = current_user.username or current_user.email
    return result


@router.get("/tickets/{ticket_id}/comments", response_model=List[SupportTicketCommentOut])
async def get_ticket_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    support_db: Session = Depends(get_support_portal_db),
    current_user: User = Depends(get_current_user),
):
    """Get comments for a support ticket (customer-facing, excludes internal comments)."""
    # Verify ticket ownership
    ticket = support_db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.user_id == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or you do not have access to this ticket"
        )
    
    # Only return non-internal comments for customers
    comments = support_db.query(SupportTicketComment).filter(
        SupportTicketComment.ticket_id == ticket_id,
        SupportTicketComment.is_internal == False
    ).order_by(SupportTicketComment.created_at).all()
    
    result = []
    for comment in comments:
        comment_dict = SupportTicketCommentOut.model_validate(comment)
        if comment.commenter_type == CommenterType.CUSTOMER:
            comment_dict.commenter_name = current_user.username or current_user.email
        elif comment.commenter_type == CommenterType.SUPPORT and comment.commenter_id:
            account = (
                support_db.query(SupportPortalAccount)
                .filter(SupportPortalAccount.id == comment.commenter_id)
                .first()
            )
            if account:
                comment_dict.commenter_name = account.username
        result.append(comment_dict)
    
    return result

