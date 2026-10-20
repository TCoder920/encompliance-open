"""
Support Ticket Routes
--------------------
This module defines the customer support ticket API endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.database import get_support_portal_db
from app.models.support_ticket import (
    SupportTicket,
    SupportTicketComment,
    SupportAgentProfile,
    TicketStatus,
    TicketPriority,
    TicketCategory,
    SupportTier,
    CommenterType,
)
from app.models.support_portal_account import SupportPortalAccount
from app.models.facility import Facility
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketUpdate,
    SupportTicketOut,
    SupportTicketCommentCreate,
    SupportTicketCommentOut,
    SupportAgentProfileCreate,
    SupportAgentProfileUpdate,
    SupportAgentProfileOut,
    TicketAssignmentRequest,
    TicketEscalationRequest,
    TicketResolutionRequest,
    SupportAnalyticsOut,
)
from app.auth.support_portal_auth_utils import (
    get_current_support_account,
    require_role,
    SUPPORT_ADMIN_ROLE,
    SUPPORT_AGENT_ROLE,
    is_support_admin,
)
from app.services.audit_service import log_support_audit_event
from app.services.support_ticket_notification_service import SupportTicketNotificationService
from app.services.sla_service import SLAService
from app.services.websocket_manager import broadcast_ticket_event
from app.database import SessionLocal, get_db
from app.schemas.customer_context import CustomerContextOut, UserContext, FacilityContext, SubscriptionContext, PaymentContext
from app.models.user import User
from app.models.facility import Facility
from app.models.subscription import Subscription
# Payment model not available - payment history can be added later
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Role dependencies
require_agent_role = require_role([SUPPORT_AGENT_ROLE])
require_senior_role = require_role([SUPPORT_ADMIN_ROLE])


def ensure_ticket_visibility(ticket: SupportTicket, account: SupportPortalAccount):
    """
    Ensure the current account can view customer data for the ticket.
    Admins can view all tickets; agents must be assigned to the ticket.
    """
    if is_support_admin(account):
        return
    if ticket.assigned_to_account_id != account.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view customer details for this ticket",
        )


def get_support_tier_from_account(db: Session, account_id: int) -> SupportTier:
    """Get the support tier for a support portal account."""
    profile = db.query(SupportAgentProfile).filter(
        SupportAgentProfile.account_id == account_id
    ).first()
    if profile:
        return profile.support_tier
    return SupportTier.BEGINNER


def can_handle_ticket(agent_tier: SupportTier, ticket_tier: SupportTier, priority: TicketPriority) -> bool:
    """Check if an agent can handle a ticket based on tier and priority."""
    tier_order = {SupportTier.BEGINNER: 1, SupportTier.MID: 2, SupportTier.SENIOR: 3}
    if tier_order[agent_tier] < tier_order[ticket_tier]:
        return False
    # Beginner can only handle low/medium priority
    if agent_tier == SupportTier.BEGINNER and priority in [TicketPriority.HIGH, TicketPriority.URGENT]:
        return False
    return True


# --- Support Ticket CRUD ---
@router.post("/tickets", response_model=SupportTicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: Request,
    ticket_in: SupportTicketCreate,
    db: Session = Depends(get_support_portal_db),
):
    """Create a new support ticket. Can be called by customers or support agents."""
    # Determine user_id - either from authenticated user or from request context
    user_id = None
    
    # Determine initial tier based on priority
    initial_tier = SupportTier.BEGINNER
    if ticket_in.priority in [TicketPriority.HIGH, TicketPriority.URGENT]:
        initial_tier = SupportTier.MID
    
    new_ticket = SupportTicket(
        subject=ticket_in.subject,
        description=ticket_in.description,
        category=ticket_in.category,
        priority=ticket_in.priority,
        support_tier_required=initial_tier,
        user_id=user_id,
        facility_id=ticket_in.facility_id,
        tags=ticket_in.tags or [],
        attachments=ticket_in.attachments or [],
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    # Calculate and set SLA deadlines
    SLAService.update_ticket_sla(db, new_ticket)
    
    # Broadcast WebSocket event
    ticket_dict = SupportTicketOut.model_validate(new_ticket)
    await broadcast_ticket_event("ticket_created", {
        "ticket": ticket_dict.model_dump(),
        "ticket_number": new_ticket.ticket_number,
    })
    
    # Log action if created by admin
    if hasattr(request.state, 'account_id'):
        await log_support_audit_event(
            db=db,
            support_account_id=request.state.account_id,
            action="create_support_ticket",
            target=f"ticket:{new_ticket.id}",
            ip_address=request.client.host if request.client else None,
            details={"ticket_number": new_ticket.ticket_number},
        )
    
    return new_ticket


@router.get("/tickets", response_model=List[SupportTicketOut])
async def list_tickets(
    request: Request,
    status_filter: Optional[TicketStatus] = None,
    priority_filter: Optional[TicketPriority] = None,
    category_filter: Optional[TicketCategory] = None,
    assigned_to_me: bool = False,
    unassigned: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_support_portal_db),
    current_account: Optional[SupportPortalAccount] = Depends(get_current_support_account),
):
    """List support tickets with optional filters."""
    query = db.query(SupportTicket)
    
    # Apply filters
    if status_filter:
        query = query.filter(SupportTicket.status == status_filter)
    if priority_filter:
        query = query.filter(SupportTicket.priority == priority_filter)
    if category_filter:
        query = query.filter(SupportTicket.category == category_filter)
    
    if assigned_to_me and current_account:
        query = query.filter(SupportTicket.assigned_to_account_id == current_account.id)
    elif unassigned:
        query = query.filter(SupportTicket.assigned_to_account_id.is_(None))
    
    # Check tier permissions
    if current_account:
        agent_tier = get_support_tier_from_account(db, current_account.id)
        # Filter out tickets that require higher tier
        if agent_tier == SupportTier.BEGINNER:
            query = query.filter(
                or_(
                    SupportTicket.support_tier_required == SupportTier.BEGINNER,
                    SupportTicket.priority.in_([TicketPriority.LOW, TicketPriority.MEDIUM])
                )
            )
        elif agent_tier == SupportTier.MID:
            query = query.filter(
                SupportTicket.support_tier_required != SupportTier.SENIOR
            )
    
    tickets = query.order_by(desc(SupportTicket.created_at)).offset(skip).limit(limit).all()
    
    # Add assigned_to_username
    result = []
    for ticket in tickets:
        ticket_dict = SupportTicketOut.model_validate(ticket)
        if ticket.assigned_to_account_id:
            admin = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == ticket.assigned_to_account_id).first()
            if admin:
                ticket_dict.assigned_to_username = admin.username
        result.append(ticket_dict)
    
    return result


@router.get("/tickets/{ticket_id}", response_model=SupportTicketOut)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_support_portal_db),
    current_account: Optional[SupportPortalAccount] = Depends(get_current_support_account),
):
    """Get a specific support ticket."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    # Check tier permissions
    if current_account:
        agent_tier = get_support_tier_from_account(db, current_account.id)
        if not can_handle_ticket(agent_tier, ticket.support_tier_required, ticket.priority):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this ticket"
            )
    
    result = SupportTicketOut.model_validate(ticket)
    if ticket.assigned_to_account_id:
        admin = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == ticket.assigned_to_account_id).first()
        if admin:
            result.assigned_to_username = admin.username
    
    return result


@router.get("/tickets/{ticket_id}/customer-context", response_model=CustomerContextOut)
async def get_ticket_customer_context(
    ticket_id: int,
    db: Session = Depends(get_support_portal_db),
    user_db: Session = Depends(get_db),
    current_account: SupportPortalAccount = Depends(get_current_support_account),
):
    """Get customer context data for a support ticket (user, facility, subscription, payment history)."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    if not ticket.user_id:
        return CustomerContextOut()

    ensure_ticket_visibility(ticket, current_account)
    
    # Get user data
    user = user_db.query(User).filter(User.id == ticket.user_id).first()
    user_context = None
    if user:
        user_context = UserContext(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            facility_type=user.facility_type,
            state=user.state,
            phone_number=user.phone_number,
            is_active=user.is_active,
            subscription_status=user.subscription_status,
            user_role=user.user_role.value if user.user_role else None,
            created_at=user.created_at,
        )
    
    # Get facility data
    facility_context = None
    if ticket.facility_id:
        facility = user_db.query(Facility).filter(Facility.id == ticket.facility_id).first()
        if facility:
            facility_context = FacilityContext(
                id=facility.id,
                facility_name=facility.facility_name,
                facility_address=facility.facility_address,
                facility_city=facility.facility_city,
                facility_state=facility.facility_state,
                facility_zip=facility.facility_zip,
                facility_phone=facility.facility_phone,
                facility_email=facility.facility_email,
                is_active=facility.is_active,
                max_users=facility.max_users,
                created_at=facility.created_at,
            )
    elif user and user.facility_id:
        facility = user_db.query(Facility).filter(Facility.id == user.facility_id).first()
        if facility:
            facility_context = FacilityContext(
                id=facility.id,
                facility_name=facility.facility_name,
                facility_address=facility.facility_address,
                facility_city=facility.facility_city,
                facility_state=facility.facility_state,
                facility_zip=facility.facility_zip,
                facility_phone=facility.facility_phone,
                facility_email=facility.facility_email,
                is_active=facility.is_active,
                max_users=facility.max_users,
                created_at=facility.created_at,
            )
    
    # Get subscription data
    subscription_context = None
    if facility_context:
        subscription = user_db.query(Subscription).filter(
            Subscription.facility_id == facility_context.id
        ).order_by(desc(Subscription.created_at)).first()
        if subscription:
            subscription_status = (
                subscription.status.value
                if hasattr(subscription.status, "value")
                else subscription.status
            )
            subscription_context = SubscriptionContext(
                id=subscription.id,
                status=subscription_status,
                current_period_start=subscription.current_period_start,
                current_period_end=subscription.current_period_end,
                seat_count=subscription.seat_count,
                total_amount=str(subscription.total_amount) if subscription.total_amount else None,
                trial_end=subscription.trial_end,
                cancel_at_period_end=subscription.cancel_at_period_end,
            )
    
    # Get ticket counts for this user
    ticket_count = db.query(SupportTicket).filter(SupportTicket.user_id == ticket.user_id).count()
    open_ticket_count = db.query(SupportTicket).filter(
        SupportTicket.user_id == ticket.user_id,
        SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.ESCALATED])
    ).count()
    
    return CustomerContextOut(
        user=user_context,
        facility=facility_context,
        subscription=subscription_context,
        recent_payments=[],  # Payment model not available, can be added later
        ticket_count=ticket_count,
        open_ticket_count=open_ticket_count,
    )


@router.get("/tickets/{ticket_id}/customer-history", response_model=List[Dict[str, Any]])
async def get_customer_ticket_history(
    ticket_id: int,
    db: Session = Depends(get_support_portal_db),
    current_account: SupportPortalAccount = Depends(get_current_support_account),
):
    """Get complete ticket history for the customer associated with this ticket."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    if not ticket.user_id:
        return []
    
    # Get all tickets for this customer
    customer_tickets = db.query(SupportTicket).filter(
        SupportTicket.user_id == ticket.user_id
    ).order_by(desc(SupportTicket.created_at)).all()
    
    # Build timeline events
    timeline = []
    for t in customer_tickets:
        # Ticket creation event
        timeline.append({
            "type": "ticket_created",
            "ticket_id": t.id,
            "ticket_number": t.ticket_number,
            "subject": t.subject,
            "status": t.status.value,
            "priority": t.priority.value,
            "category": t.category.value,
            "timestamp": t.created_at.isoformat() if t.created_at else None,
            "description": f"Ticket {t.ticket_number} created: {t.subject}",
        })
        
        # Status changes
        if t.status == TicketStatus.RESOLVED and t.resolved_at:
            timeline.append({
                "type": "ticket_resolved",
                "ticket_id": t.id,
                "ticket_number": t.ticket_number,
                "timestamp": t.resolved_at.isoformat() if t.resolved_at else None,
                "description": f"Ticket {t.ticket_number} resolved",
            })
        
        if t.status == TicketStatus.ESCALATED:
            timeline.append({
                "type": "ticket_escalated",
                "ticket_id": t.id,
                "ticket_number": t.ticket_number,
                "timestamp": t.updated_at.isoformat() if t.updated_at else None,
                "description": f"Ticket {t.ticket_number} escalated: {t.escalation_reason or 'No reason provided'}",
            })
        
        # Get comments for this ticket
        comments = db.query(SupportTicketComment).filter(
            SupportTicketComment.ticket_id == t.id
        ).order_by(SupportTicketComment.created_at).all()
        
        for comment in comments:
            timeline.append({
                "type": "comment_added",
                "ticket_id": t.id,
                "ticket_number": t.ticket_number,
                "commenter_type": comment.commenter_type.value,
                "is_internal": comment.is_internal,
                "timestamp": comment.created_at.isoformat() if comment.created_at else None,
                "description": f"{'Internal' if comment.is_internal else 'Public'} comment on ticket {t.ticket_number}",
            })
    
    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    
    return timeline


@router.put("/tickets/{ticket_id}", response_model=SupportTicketOut)
async def update_ticket(
    ticket_id: int,
    ticket_update: SupportTicketUpdate,
    request: Request,
    db: Session = Depends(get_support_portal_db),
    current_account: SupportPortalAccount = Depends(get_current_support_account),
):
    """Update a support ticket."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    # Check tier permissions
    agent_tier = get_support_tier_from_account(db, current_account.id)
    if not can_handle_ticket(agent_tier, ticket.support_tier_required, ticket.priority):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this ticket"
        )
    
    # Update fields
    update_data = ticket_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(ticket, field):
            setattr(ticket, field, value)
    
    # Handle status changes
    if ticket_update.status == TicketStatus.RESOLVED and not ticket.resolved_at:
        ticket.resolved_at = datetime.utcnow()
    elif ticket_update.status != TicketStatus.RESOLVED:
        ticket.resolved_at = None
    
    db.commit()
    db.refresh(ticket)
    
    await log_support_audit_event(
        db=db,
        support_account_id=current_account.id,
        action="update_support_ticket",
        target=f"ticket:{ticket.id}",
        ip_address=request.client.host if request.client else None,
        details={"changes": update_data},
    )
    
    result = SupportTicketOut.model_validate(ticket)
    if ticket.assigned_to_account_id:
        admin = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == ticket.assigned_to_account_id).first()
        if admin:
            result.assigned_to_username = admin.username
    
    return result


# --- Ticket Comments ---
@router.post("/tickets/{ticket_id}/comments", response_model=SupportTicketCommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    ticket_id: int,
    comment_in: SupportTicketCommentCreate,
    request: Request,
    db: Session = Depends(get_support_portal_db),
    current_account: Optional[SupportPortalAccount] = Depends(get_current_support_account),
):
    """Add a comment to a support ticket."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    commenter_type = CommenterType.SUPPORT if current_account else CommenterType.CUSTOMER
    commenter_id = current_account.id if current_account else None
    
    new_comment = SupportTicketComment(
        ticket_id=ticket_id,
        commenter_type=commenter_type,
        commenter_id=commenter_id,
        comment_text=comment_in.comment_text,
        is_internal=comment_in.is_internal,
    )
    db.add(new_comment)
    
    # Update ticket timestamps
    if commenter_type == CommenterType.CUSTOMER:
        ticket.last_customer_reply_at = datetime.utcnow()
    else:
        ticket.last_support_reply_at = datetime.utcnow()
        # Mark first response if this is the first support comment
        if not ticket.first_response_at:
            SLAService.mark_first_response(db, ticket)
    
    # Update SLA status
    SLAService.update_ticket_sla(db, ticket)
    
    db.commit()
    db.refresh(new_comment)
    
    # Broadcast WebSocket event
    await broadcast_ticket_event("ticket_comment", {
        "ticket_id": ticket_id,
        "ticket_number": ticket.ticket_number,
        "comment_id": new_comment.id,
        "commenter_type": commenter_type.value,
        "is_internal": comment_in.is_internal,
    }, target_account_id=ticket.assigned_to_account_id if ticket.assigned_to_account_id else None)
    
    # Notify customer if support agent commented (non-internal comments only)
    if current_account and not comment_in.is_internal:
        try:
            user_db = SessionLocal()
            await SupportTicketNotificationService.notify_ticket_comment(
                db,
                ticket,
                commenter_type="support",
                commenter_id=current_account.id,
                user_db=user_db,
            )
        except Exception as e:
            logger.error(f"Failed to send ticket comment notification: {e}")
    
    result = SupportTicketCommentOut.model_validate(new_comment)
    if current_account:
        result.commenter_name = current_account.username
    
    return result


@router.get("/tickets/{ticket_id}/comments", response_model=List[SupportTicketCommentOut])
async def list_comments(
    ticket_id: int,
    include_internal: bool = False,
    db: Session = Depends(get_support_portal_db),
    current_account: Optional[SupportPortalAccount] = Depends(get_current_support_account),
):
    """List comments for a support ticket."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    query = db.query(SupportTicketComment).filter(SupportTicketComment.ticket_id == ticket_id)
    
    # Filter internal comments for non-admin users
    if not current_account or not include_internal:
        query = query.filter(SupportTicketComment.is_internal == False)
    
    comments = query.order_by(SupportTicketComment.created_at).all()
    
    result = []
    for comment in comments:
        comment_dict = SupportTicketCommentOut.model_validate(comment)
        if comment.commenter_type == CommenterType.SUPPORT and comment.commenter_id:
            admin = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == comment.commenter_id).first()
            if admin:
                comment_dict.commenter_name = admin.username
        result.append(comment_dict)
    
    return result


# --- Ticket Assignment & Escalation ---
@router.post("/tickets/{ticket_id}/assign", response_model=SupportTicketOut)
async def assign_ticket(
    ticket_id: int,
    assignment: TicketAssignmentRequest,
    request: Request,
    db: Session = Depends(get_support_portal_db),
    current_account: SupportPortalAccount = Depends(get_current_support_account),
):
    """Assign a ticket to a support agent."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    # Verify agent exists and is active
    agent_profile = db.query(SupportAgentProfile).filter(
        SupportAgentProfile.account_id == assignment.assigned_to_account_id
    ).first()
    if not agent_profile or not agent_profile.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or inactive agent")
    
    # Check if agent can handle this ticket
    if not can_handle_ticket(agent_profile.support_tier, ticket.support_tier_required, ticket.priority):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent tier is insufficient for this ticket"
        )
    
    ticket.assigned_to_account_id = assignment.assigned_to_account_id
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
    db.commit()
    db.refresh(ticket)
    
    # Broadcast WebSocket event
    ticket_dict = SupportTicketOut.model_validate(ticket)
    admin = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == ticket.assigned_to_account_id).first()
    if admin:
        ticket_dict.assigned_to_username = admin.username
    
    await broadcast_ticket_event("ticket_assigned", {
        "ticket": ticket_dict.model_dump(),
        "ticket_number": ticket.ticket_number,
        "assigned_to_account_id": assignment.assigned_to_account_id,
    }, target_account_id=assignment.assigned_to_account_id)
    
    await log_support_audit_event(
        db=db,
        support_account_id=current_account.id,
        action="assign_support_ticket",
        target=f"ticket:{ticket.id}",
        ip_address=request.client.host if request.client else None,
        details={"assigned_to": assignment.assigned_to_account_id},
    )
    
    # Notify assigned agent
    try:
        await SupportTicketNotificationService.notify_ticket_assigned(
            db,
            ticket,
            assignment.assigned_to_account_id,
        )
    except Exception as e:
        logger.error(f"Failed to send ticket assignment notification: {e}")
    
    result = SupportTicketOut.model_validate(ticket)
    admin = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == ticket.assigned_to_account_id).first()
    if admin:
        result.assigned_to_username = admin.username
    
    return result


@router.post("/tickets/{ticket_id}/escalate", response_model=SupportTicketOut)
async def escalate_ticket(
    ticket_id: int,
    escalation: TicketEscalationRequest,
    request: Request,
    db: Session = Depends(get_support_portal_db),
    current_account: SupportPortalAccount = Depends(get_current_support_account),
):
    """Escalate a ticket to a higher tier."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    target_tier = escalation.target_tier or SupportTier.SENIOR
    tier_order = {SupportTier.BEGINNER: 1, SupportTier.MID: 2, SupportTier.SENIOR: 3}
    
    if tier_order[target_tier] <= tier_order[ticket.support_tier_required]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target tier must be higher than current tier"
        )
    
    ticket.support_tier_required = target_tier
    ticket.status = TicketStatus.ESCALATED
    ticket.escalation_reason = escalation.escalation_reason
    ticket.assigned_to_account_id = None  # Unassign on escalation
    db.commit()
    db.refresh(ticket)
    
    # Broadcast WebSocket event
    ticket_dict = SupportTicketOut.model_validate(ticket)
    await broadcast_ticket_event("ticket_escalated", {
        "ticket": ticket_dict.model_dump(),
        "ticket_number": ticket.ticket_number,
        "target_tier": target_tier.value,
        "escalation_reason": escalation.escalation_reason,
    })
    
    await log_support_audit_event(
        db=db,
        support_account_id=current_account.id,
        action="escalate_support_ticket",
        target=f"ticket:{ticket.id}",
        ip_address=request.client.host if request.client else None,
        details={"new_tier": target_tier.value, "reason": escalation.escalation_reason},
    )
    
    # Notify about escalation
    try:
        await SupportTicketNotificationService.notify_ticket_escalated(
            db,
            ticket,
        )
    except Exception as e:
        logger.error(f"Failed to send ticket escalation notification: {e}")
    
    result = SupportTicketOut.model_validate(ticket)
    return result


@router.post("/tickets/{ticket_id}/resolve", response_model=SupportTicketOut)
async def resolve_ticket(
    ticket_id: int,
    resolution: TicketResolutionRequest,
    request: Request,
    db: Session = Depends(get_support_portal_db),
    current_account: SupportPortalAccount = Depends(get_current_support_account),
):
    """Mark a ticket as resolved."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    ticket.status = TicketStatus.RESOLVED
    ticket.resolved_at = datetime.utcnow()
    if resolution.internal_notes:
        ticket.internal_notes = resolution.internal_notes
    db.commit()
    db.refresh(ticket)
    
    # Broadcast WebSocket event
    ticket_dict = SupportTicketOut.model_validate(ticket)
    if ticket.assigned_to_account_id:
        admin = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == ticket.assigned_to_account_id).first()
        if admin:
            ticket_dict.assigned_to_username = admin.username
    
    await broadcast_ticket_event("ticket_resolved", {
        "ticket": ticket_dict.model_dump(),
        "ticket_number": ticket.ticket_number,
    }, target_account_id=ticket.assigned_to_account_id if ticket.assigned_to_account_id else None)
    
    await log_support_audit_event(
        db=db,
        support_account_id=current_account.id,
        action="resolve_support_ticket",
        target=f"ticket:{ticket.id}",
        ip_address=request.client.host if request.client else None,
    )
    
    # Notify customer of resolution
    try:
        user_db = SessionLocal()
        await SupportTicketNotificationService.notify_ticket_resolved(
            db,
            ticket,
            user_db=user_db,
        )
    except Exception as e:
        logger.error(f"Failed to send ticket resolution notification: {e}")
    
    result = SupportTicketOut.model_validate(ticket)
    if ticket.assigned_to_account_id:
        admin = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == ticket.assigned_to_account_id).first()
        if admin:
            result.assigned_to_username = admin.username
    
    return result


# --- Support Agent Management ---
@router.get("/agents", response_model=List[SupportAgentProfileOut])
async def list_agents(
    db: Session = Depends(get_support_portal_db),
    current_account: SupportPortalAccount = Depends(get_current_support_account),
):
    """List all support agents."""
    profiles = db.query(SupportAgentProfile).all()
    result = []
    for profile in profiles:
        profile_dict = SupportAgentProfileOut.model_validate(profile)
        account = (
            db.query(SupportPortalAccount)
            .filter(SupportPortalAccount.id == profile.account_id)
            .first()
        )
        if account:
            profile_dict.account_username = account.username
            profile_dict.account_email = account.email
        result.append(profile_dict)
    return result


@router.post("/agents", response_model=SupportAgentProfileOut, status_code=status.HTTP_201_CREATED)
async def create_agent_profile(
    agent_in: SupportAgentProfileCreate,
    request: Request,
    db: Session = Depends(get_support_portal_db),
    current_account: SupportPortalAccount = Depends(require_senior_role),
):
    """Create a support agent profile."""
    # Verify support account exists
    support_account = (
        db.query(SupportPortalAccount)
        .filter(SupportPortalAccount.id == agent_in.account_id)
        .first()
    )
    if not support_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Support account not found"
        )
    
    # Check if profile already exists
    existing = db.query(SupportAgentProfile).filter(
        SupportAgentProfile.account_id == agent_in.account_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent profile already exists")
    
    new_profile = SupportAgentProfile(
        account_id=agent_in.account_id,
        support_tier=agent_in.support_tier,
        specialization_tags=agent_in.specialization_tags or [],
        max_concurrent_tickets=agent_in.max_concurrent_tickets,
        is_active=agent_in.is_active,
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    await log_support_audit_event(
        db=db,
        support_account_id=current_account.id,
        action="create_support_agent_profile",
        target=f"agent:{new_profile.id}",
        ip_address=request.client.host if request.client else None,
    )
    
    result = SupportAgentProfileOut.model_validate(new_profile)
    result.account_username = support_account.username
    result.account_email = support_account.email
    return result


@router.put("/agents/{agent_id}", response_model=SupportAgentProfileOut)
async def update_agent_profile(
    agent_id: int,
    agent_update: SupportAgentProfileUpdate,
    request: Request,
    db: Session = Depends(get_support_portal_db),
    current_account: SupportPortalAccount = Depends(require_agent_role),
):
    """Update a support agent profile."""
    profile = db.query(SupportAgentProfile).filter(SupportAgentProfile.id == agent_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent profile not found")
    
    update_data = agent_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(profile, field):
            setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    await log_support_audit_event(
        db=db,
        support_account_id=current_account.id,
        action="update_support_agent_profile",
        target=f"agent:{agent_id}",
        ip_address=request.client.host if request.client else None,
    )
    
    result = SupportAgentProfileOut.model_validate(profile)
    account = (
        db.query(SupportPortalAccount)
        .filter(SupportPortalAccount.id == profile.account_id)
        .first()
    )
    if account:
        result.account_username = account.username
        result.account_email = account.email
    return result


# --- Analytics ---
@router.get("/analytics", response_model=SupportAnalyticsOut)
async def get_analytics(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_support_portal_db),
    current_account: SupportPortalAccount = Depends(get_current_support_account),
):
    """Get support ticket analytics with optional date range filtering."""
    from datetime import datetime as dt
    
    # Build base query with optional date filtering
    base_query = db.query(SupportTicket)
    
    if date_from:
        try:
            date_from_obj = dt.fromisoformat(date_from.replace('Z', '+00:00'))
            base_query = base_query.filter(SupportTicket.created_at >= date_from_obj)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    if date_to:
        try:
            date_to_obj = dt.fromisoformat(date_to.replace('Z', '+00:00'))
            base_query = base_query.filter(SupportTicket.created_at <= date_to_obj)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    total = base_query.count()
    open_count = base_query.filter(SupportTicket.status == TicketStatus.OPEN).count()
    in_progress_count = base_query.filter(SupportTicket.status == TicketStatus.IN_PROGRESS).count()
    resolved_count = base_query.filter(SupportTicket.status == TicketStatus.RESOLVED).count()
    closed_count = base_query.filter(SupportTicket.status == TicketStatus.CLOSED).count()
    escalated_count = base_query.filter(SupportTicket.status == TicketStatus.ESCALATED).count()
    
    # Tickets by priority
    priority_counts = {}
    for priority in TicketPriority:
        count = base_query.filter(SupportTicket.priority == priority).count()
        priority_counts[priority.value] = count
    
    # Tickets by category
    category_counts = {}
    for category in TicketCategory:
        count = base_query.filter(SupportTicket.category == category).count()
        category_counts[category.value] = count
    
    # Tickets by tier
    tier_counts = {}
    for tier in SupportTier:
        count = base_query.filter(SupportTicket.support_tier_required == tier).count()
        tier_counts[tier.value] = count
    
    # Average resolution time
    resolved_tickets = base_query.filter(
        SupportTicket.status == TicketStatus.RESOLVED,
        SupportTicket.resolved_at.isnot(None)
    ).all()
    
    avg_resolution_hours = None
    if resolved_tickets:
        total_hours = 0
        for ticket in resolved_tickets:
            if ticket.resolved_at and ticket.created_at:
                delta = ticket.resolved_at - ticket.created_at
                total_hours += delta.total_seconds() / 3600
        avg_resolution_hours = total_hours / len(resolved_tickets)
    
    # Tickets by agent
    agent_counts = {}
    assigned_tickets = base_query.filter(
        SupportTicket.assigned_to_account_id.isnot(None)
    ).all()
    for ticket in assigned_tickets:
        admin = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == ticket.assigned_to_account_id).first()
        if admin:
            agent_counts[admin.username] = agent_counts.get(admin.username, 0) + 1
    
    # Recent tickets
    recent_tickets = base_query.order_by(desc(SupportTicket.created_at)).limit(10).all()
    recent_ticket_outs = []
    for ticket in recent_tickets:
        ticket_dict = SupportTicketOut.model_validate(ticket)
        if ticket.assigned_to_account_id:
            admin = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == ticket.assigned_to_account_id).first()
            if admin:
                ticket_dict.assigned_to_username = admin.username
        recent_ticket_outs.append(ticket_dict)
    
    # SLA metrics
    sla_breached_count = base_query.filter(
        SupportTicket.sla_breached == True,
        SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.ESCALATED])
    ).count()
    
    # Calculate average response time
    tickets_with_response = base_query.filter(
        SupportTicket.first_response_at.isnot(None)
    ).all()
    avg_response_hours = None
    if tickets_with_response:
        total_response_hours = 0
        for ticket in tickets_with_response:
            if ticket.first_response_at and ticket.created_at:
                delta = ticket.first_response_at - ticket.created_at
                total_response_hours += delta.total_seconds() / 3600
        avg_response_hours = total_response_hours / len(tickets_with_response)
    
    # Calculate SLA compliance rate
    sla_compliance_rate = None
    if total > 0:
        compliant_tickets = total - sla_breached_count
        sla_compliance_rate = (compliant_tickets / total) * 100
    
    # Tickets requiring attention (breached or stale)
    stale_cutoff = datetime.utcnow() - timedelta(hours=48)
    tickets_requiring_attention = base_query.filter(
        or_(
            SupportTicket.sla_breached == True,
            and_(
                SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS]),
                SupportTicket.updated_at < stale_cutoff
            )
        ),
        SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.ESCALATED])
    ).count()
    
    return SupportAnalyticsOut(
        total_tickets=total,
        open_tickets=open_count,
        in_progress_tickets=in_progress_count,
        resolved_tickets=resolved_count,
        closed_tickets=closed_count,
        escalated_tickets=escalated_count,
        tickets_by_priority=priority_counts,
        tickets_by_category=category_counts,
        tickets_by_tier=tier_counts,
        average_resolution_time_hours=avg_resolution_hours,
        tickets_by_agent=agent_counts,
        recent_tickets=recent_ticket_outs,
        sla_breached_tickets=sla_breached_count,
        average_response_time_hours=avg_response_hours,
        sla_compliance_rate=sla_compliance_rate,
        tickets_requiring_attention=tickets_requiring_attention,
    )

