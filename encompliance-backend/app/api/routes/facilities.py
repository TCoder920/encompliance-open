"""
Facility Management API Routes Module

This module defines API endpoints for facility administrators to manage their facilities.
It provides comprehensive Pro Mode functionality including user management, invitations,
subscription oversight, and facility-wide operations.

Note: Facility administrators are users with a pro subscription who manage facility operations.

Key functionalities:
- Facility dashboard with analytics
- User invitation and management
- Subscription and billing oversight
- Training assignment management
- Calendar event management for facilities
- Facility settings and configuration

Dependencies:
- fastapi: Web framework for API endpoints
- sqlalchemy: Database operations
- stripe: Payment processing integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import logging

from app.database import get_db
from app.auth.dependencies import get_current_user, require_facility_admin
from app.services.admin_sync_service import AdminSyncService
from app.models import (
    User, Facility, Subscription, FacilityInvitation, 
    TrainingAssignment, CalendarEvent, Notification
)
from app.models.user import UserRole
from app.models.facility_invitation import InvitationStatus
from app.models.subscription import SubscriptionStatus
from app.schemas.facility import (
    FacilityResponse, FacilityUpdate, InvitationCreate, InvitationResponse,
    UserInviteRequest, FacilityUserResponse, FacilityDashboardResponse,
    SubscriptionResponse
)
from app.services.stripe_service import StripeService
from app.auth.otp_utils import send_email_otp, generate_otp
from app.models.otp import OTPType
from app.core.email_service import send_facility_invitation_email

router = APIRouter(prefix="/facilities", tags=["facility_management"])
logger = logging.getLogger(__name__)


# Overview and Analytics
@router.get("/overview", response_model=FacilityDashboardResponse)
async def get_facility_overview(
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive facility overview data for administrators only.
    
    This endpoint is restricted to facility administrators and provides complete
    overview of their facility's operations, users, billing, and analytics.
    Team members cannot access this sensitive administrative information.
    
    Note: Facility administrators are users with a pro subscription who manage facility operations.
    """
    try:
        facility = current_user.administered_facility
        
        if not facility:
            # Pro user doesn't have a facility yet - auto-create one
            from app.models.facility import Facility
            
            # Create a default facility for the Pro user
            facility = Facility(
                facility_name=current_user.facility_name or f"{current_user.username}'s Practice",
                admin_user_id=current_user.id,
                is_active=True
            )
            
            db.add(facility)
            db.commit()
            db.refresh(facility)
            
            # Link user to the facility
            current_user.facility_id = facility.id
            db.commit()
            
            logger.info(f"Auto-created facility {facility.id} for Pro user {current_user.id}")
        
        # Get subscription information
        subscription = db.query(Subscription).filter(
            Subscription.facility_id == facility.id
        ).order_by(desc(Subscription.created_at)).first()
        
        # Get facility users (excluding admin)
        facility_users = db.query(User).filter(
            and_(
                User.facility_id == facility.id,
                User.id != current_user.id
            )
        ).all()
        
        # Get active invitations
        active_invitations = db.query(FacilityInvitation).filter(
            and_(
                FacilityInvitation.facility_id == facility.id,
                FacilityInvitation.status == InvitationStatus.PENDING.value
            )
        ).order_by(desc(FacilityInvitation.created_at)).all()
        
        # Calculate training completion stats
        total_assignments = db.query(TrainingAssignment).filter(
            TrainingAssignment.facility_id == facility.id
        ).count()
        
        completed_assignments = db.query(TrainingAssignment).filter(
            and_(
                TrainingAssignment.facility_id == facility.id,
                TrainingAssignment.status == "completed"
            )
        ).count()
        
        completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
        
        # Get upcoming calendar events
        upcoming_events_query = db.query(CalendarEvent).filter(
            and_(
                CalendarEvent.facility_id == facility.id,
                CalendarEvent.start >= datetime.now().isoformat(),
                CalendarEvent.created_by_admin == True
            )
        ).order_by(CalendarEvent.start).limit(5)
        
        upcoming_events = [
            {
                "id": event.id,
                "title": event.title,
                "start_date": event.start,
                "end_date": event.end,
                "description": event.description
            }
            for event in upcoming_events_query.all()
        ]
        
        # Prepare training stats
        training_stats = {
            "total_assignments": total_assignments,
            "completed_assignments": completed_assignments,
            "completion_rate": round(completion_rate, 1),
            "overdue_assignments": db.query(TrainingAssignment).filter(
                and_(
                    TrainingAssignment.facility_id == facility.id,
                    TrainingAssignment.due_date < datetime.now(),
                    TrainingAssignment.status != "completed"
                )
            ).count()
        }
        
        return FacilityDashboardResponse(
            facility=FacilityResponse.from_orm(facility),
            subscription=SubscriptionResponse.from_orm(subscription) if subscription else None,
            users=[FacilityUserResponse.from_orm(user) for user in facility_users],
            active_invitations=[InvitationResponse.from_orm(inv) for inv in active_invitations],
            training_completion_stats=training_stats,
            upcoming_events=upcoming_events
        )
        
    except Exception as e:
        logger.error(f"Error retrieving facility overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve facility overview"
        )


# Facility Information Management
@router.get("/info", response_model=FacilityResponse)
async def get_facility_info(
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Get current facility information."""
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    return FacilityResponse.from_orm(facility)


@router.put("/info", response_model=FacilityResponse)
async def update_facility_info(
    facility_data: FacilityUpdate,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Update facility information."""
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    # Update facility fields
    update_data = facility_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(facility, field, value)
    
    try:
        db.commit()
        db.refresh(facility)
        logger.info(f"Updated facility {facility.id} information")
        
        # Trigger account sync for team members
        try:
            admin_sync_service = AdminSyncService(db)
            await admin_sync_service.trigger_account_sync(facility.id, current_user.id)
        except Exception as sync_error:
            logger.error(f"Failed to trigger account sync: {sync_error}")
        
        return FacilityResponse.from_orm(facility)
        
    except Exception as e:
        logger.error(f"Error updating facility information: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update facility information"
        )


# User Management
@router.get("/users", response_model=List[FacilityUserResponse])
async def get_facility_users(
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db),
    include_admin: bool = Query(False, description="Include facility administrator in results")
):
    """Get all users in the current facility."""
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    # Build query
    query = db.query(User).filter(User.facility_id == facility.id)
    
    if not include_admin:
        query = query.filter(User.id != current_user.id)
    
    users = query.order_by(User.created_at).all()
    
    return [FacilityUserResponse.from_orm(user) for user in users]


@router.get("/staff-members", response_model=List[dict])
async def get_facility_staff_members(
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Get all staff members for assignment purposes."""
    from app.models.staff_member import StaffMember, StaffStatus
    
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    # Get staff members for this facility administrator
    staff_members = db.query(StaffMember).filter(
        StaffMember.facility_administrator_id == current_user.id,
        StaffMember.status == StaffStatus.ACTIVE.value
    ).order_by(StaffMember.first_name, StaffMember.last_name).all()
    
    # Format for assignment interface
    result = []
    for staff in staff_members:
        result.append({
            "id": staff.id,
            "first_name": staff.first_name,
            "last_name": staff.last_name,
            "full_name": f"{staff.first_name} {staff.last_name}",
            "email": staff.email,
            "role": staff.role,
            "department": staff.department,
            "age": staff.age if hasattr(staff, 'age') else None,
            "is_active": staff.status == StaffStatus.ACTIVE.value
        })
    
    return result


@router.delete("/users/{user_id}")
async def remove_facility_user(
    user_id: int,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Remove a user from the facility."""
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    # Get the user to remove
    user_to_remove = db.query(User).filter(
        and_(
            User.id == user_id,
            User.facility_id == facility.id,
            User.id != current_user.id  # Cannot remove admin
        )
    ).first()
    
    if not user_to_remove:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in facility or cannot be removed"
        )
    
    try:
        # Remove user from facility (set facility_id to None)
        user_to_remove.facility_id = None
        
        # Update subscription seat count
        subscription = db.query(Subscription).filter(
            Subscription.facility_id == facility.id
        ).order_by(desc(Subscription.created_at)).first()
        
        if subscription:
            new_seat_count = max(1, facility.current_user_count - 1)
            
            # Update Stripe subscription
            stripe_service = StripeService()
            stripe_service.update_subscription_seats(
                subscription.stripe_subscription_id,
                new_seat_count
            )
            
            # Update local subscription record
            subscription.seat_count = new_seat_count
            subscription.total_amount = stripe_service.calculate_subscription_amount(new_seat_count)
        
        db.commit()
        
        # Send notification to removed user
        from app.models.notification import Notification, NotificationType
        notification = Notification(
            user_id=user_to_remove.id,
            sender_id=current_user.id,
            title="Removed from Facility",
            message=f"You have been removed from {facility.facility_name}.",
            type=NotificationType.FACILITY_UPDATE.value
        )
        db.add(notification)
        db.commit()
        
        logger.info(f"Removed user {user_id} from facility {facility.id}")
        
        return {"message": "User removed from facility successfully"}
        
    except Exception as e:
        logger.error(f"Error removing user from facility: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove user from facility"
        )


@router.put("/users/{user_id}/role")
async def update_team_member_role(
    user_id: int,
    role_data: dict,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Update a team member's role description (facility administrators only)."""
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    # Find the team member
    team_member = db.query(User).filter(
        and_(
            User.id == user_id,
            User.facility_id == facility.id,
            User.user_role == UserRole.TEAM_MEMBER
        )
    ).first()
    
    if not team_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found in your facility"
        )
    
    # Validate role_description
    role_description = role_data.get("role_description", "").strip()
    if not role_description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role description is required"
        )
    
    if len(role_description) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role description must be 100 characters or less"
        )
    
    try:
        # Update team member's role description
        team_member.role_description = role_description
        db.commit()
        
        logger.info(f"Updated team member {user_id} role to: {role_description}")
        
        return {
            "message": "Team member role updated successfully",
            "user_id": user_id,
            "role_description": role_description
        }
        
    except Exception as e:
        logger.error(f"Error updating team member role: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update team member role"
        )


# Invitation Management
@router.get("/invitations", response_model=List[InvitationResponse])
async def get_facility_invitations(
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by invitation status")
):
    """Get all invitations for the current facility."""
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    query = db.query(FacilityInvitation).filter(
        FacilityInvitation.facility_id == facility.id
    )
    
    if status_filter:
        query = query.filter(FacilityInvitation.status == status_filter)
    
    invitations = query.order_by(desc(FacilityInvitation.created_at)).all()
    
    return [InvitationResponse.from_orm(inv) for inv in invitations]


@router.post("/invitations", response_model=InvitationResponse)
async def create_facility_invitation(
    invitation_data: InvitationCreate,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Create a new facility invitation."""
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    # Check seat capacity
    subscription = db.query(Subscription).filter(
        Subscription.facility_id == facility.id
    ).order_by(desc(Subscription.created_at)).first()
    
    if subscription:
        current_users = facility.current_user_count
        available_seats = subscription.seat_count
        
        if current_users >= available_seats:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Cannot invite more users. You have {current_users} users but only {available_seats} seats. Please upgrade your subscription to add more seats."
            )
    
    # Check if email is already invited or is a user
    if invitation_data.email:
        existing_user = db.query(User).filter(User.email == invitation_data.email).first()
        if existing_user:
            if existing_user.facility_id == facility.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already part of this facility"
                )
        
        existing_invitation = db.query(FacilityInvitation).filter(
            and_(
                FacilityInvitation.email == invitation_data.email,
                FacilityInvitation.facility_id == facility.id,
                FacilityInvitation.status == InvitationStatus.PENDING.value
            )
        ).first()
        
        if existing_invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a pending invitation"
            )
    
    try:
        # Create invitation
        invitation = FacilityInvitation.create_invitation(
            facility_id=facility.id,
            created_by_user_id=current_user.id,
            email=invitation_data.email,
            expires_in_days=invitation_data.expires_in_days,
            personal_message=invitation_data.personal_message
        )
        invitation.role_description = invitation_data.role_description
        
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        
        # Send invitation email if email provided
        if invitation_data.email:
            try:
                send_facility_invitation_email(
                    email=invitation_data.email,
                    facility_name=facility.facility_name,
                    invitation_code=invitation.invitation_code,
                    admin_name=current_user.full_name,
                    personal_message=invitation_data.personal_message
                )
                logger.info(f"Sent invitation email to {invitation_data.email}")
            except Exception as e:
                logger.error(f"Failed to send invitation email: {str(e)}")
                # Don't fail the invitation creation if email fails
        
        logger.info(f"Created facility invitation {invitation.id}")
        
        return InvitationResponse.from_orm(invitation)
        
    except Exception as e:
        logger.error(f"Error creating facility invitation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invitation"
        )


@router.post("/invitations/{invitation_id}/resend")
async def resend_facility_invitation(
    invitation_id: int,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Resend a pending facility invitation email."""
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    invitation = db.query(FacilityInvitation).filter(
        and_(
            FacilityInvitation.id == invitation_id,
            FacilityInvitation.facility_id == facility.id
        )
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    if invitation.status != InvitationStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only resend pending invitations"
        )
    
    if not invitation.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot resend invitation without email address"
        )
    
    try:
        # Resend invitation email
        send_facility_invitation_email(
            email=invitation.email,
            facility_name=facility.facility_name,
            invitation_code=invitation.invitation_code,
            admin_name=current_user.full_name,
            personal_message=invitation.personal_message
        )
        
        logger.info(f"Resent invitation email for invitation {invitation_id} to {invitation.email}")
        
        return {"message": "Invitation email resent successfully"}
        
    except Exception as e:
        logger.error(f"Error resending invitation email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend invitation email"
        )


@router.delete("/invitations/{invitation_id}")
async def cancel_facility_invitation(
    invitation_id: int,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Cancel a pending facility invitation."""
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    invitation = db.query(FacilityInvitation).filter(
        and_(
            FacilityInvitation.id == invitation_id,
            FacilityInvitation.facility_id == facility.id
        )
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    if invitation.status != InvitationStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending invitations"
        )
    
    try:
        invitation.cancel()
        db.commit()
        
        logger.info(f"Cancelled facility invitation {invitation_id}")
        
        return {"message": "Invitation cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Error cancelling invitation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel invitation"
        )


# Public invitation endpoints (for invited users)
@router.get("/join/{invitation_code}")
async def get_invitation_details(
    invitation_code: str,
    db: Session = Depends(get_db)
):
    """Get details for a facility invitation (public endpoint)."""
    invitation = db.query(FacilityInvitation).options(
        joinedload(FacilityInvitation.facility),
        joinedload(FacilityInvitation.created_by)
    ).filter(
        FacilityInvitation.invitation_code == invitation_code
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    if not invitation.is_valid:
        status_reason = "expired" if invitation.is_expired else "already used or cancelled"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation is {status_reason}"
        )
    
    return {
        "facility_name": invitation.facility.facility_name,
        "invited_by": invitation.created_by.full_name,
        "role_description": invitation.role_description,
        "personal_message": invitation.personal_message,
        "expires_at": invitation.expires_at.isoformat(),
        "days_remaining": invitation.days_until_expiry,
        "email": invitation.email  # Include email for pre-filling signup
    }


@router.post("/join/{invitation_code}")
async def join_facility_via_invitation(
    invitation_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a facility using an invitation code."""
    invitation = db.query(FacilityInvitation).options(
        joinedload(FacilityInvitation.facility)
    ).filter(
        FacilityInvitation.invitation_code == invitation_code
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    if not invitation.is_valid:
        status_reason = "expired" if invitation.is_expired else "already used or cancelled"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation is {status_reason}"
        )
    
    # Check if user is already part of a facility
    if current_user.facility_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already part of a facility"
        )
    
    try:
        # Get facility admin to inherit profile settings
        facility_admin = invitation.facility.admin_user
        
        # Add user to facility and inherit admin's profile settings
        current_user.facility_id = invitation.facility.id
        current_user.user_role = UserRole.TEAM_MEMBER
        current_user.state = facility_admin.state
        current_user.facility_type = facility_admin.facility_type
        
        # Mark invitation as used
        invitation.mark_as_used(current_user.id)
        
        # Set custom role description if provided in invitation
        if invitation.role_description:
            current_user.role_description = invitation.role_description
        
        # Commit user updates first
        db.commit()
        db.refresh(current_user)
        
        # Associate documents based on inherited profile
        if current_user.state and current_user.facility_type:
            from app.services.document_association_service import associate_user_documents
            
            facility_types = []
            if current_user.facility_type:
                facility_types = [ft.strip() for ft in current_user.facility_type.split(',') if ft.strip()]
            
            await associate_user_documents(db, current_user.id, current_user.state, facility_types)
        db.commit()
        
        # Send welcome notification
        from app.models.notification import Notification, NotificationType
        notification = Notification(
            user_id=current_user.id,
            sender_id=invitation.created_by_user_id,
            title="Welcome to the Facility",
            message=f"Welcome to {invitation.facility.facility_name}! You now have access to facility-wide training and compliance resources.",
            type=NotificationType.FACILITY_JOINED.value
        )
        db.add(notification)
        
        # Notify admin
        admin_notification = Notification(
            user_id=invitation.created_by_user_id,
            sender_id=current_user.id,
            title="User Joined Facility",
            message=f"{current_user.full_name} has joined {invitation.facility.facility_name}.",
            type=NotificationType.FACILITY_UPDATE.value
        )
        db.add(admin_notification)
        
        db.commit()
        
        logger.info(f"User {current_user.id} joined facility {invitation.facility.id} via invitation")
        
        return {
            "message": "Successfully joined facility",
            "facility_name": invitation.facility.facility_name
        }
        
    except Exception as e:
        logger.error(f"Error joining facility via invitation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join facility"
        )


# Subscription Management
@router.get("/subscription", response_model=SubscriptionResponse)
async def get_facility_subscription(
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Get current facility subscription details."""
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    subscription = db.query(Subscription).filter(
        Subscription.facility_id == facility.id
    ).order_by(desc(Subscription.created_at)).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for facility"
        )
    
    return SubscriptionResponse.from_orm(subscription)


@router.get("/analytics")
async def get_facility_analytics(
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, description="Number of days for analytics data")
):
    """Get facility analytics and insights."""
    facility = current_user.administered_facility
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # User activity analytics
    new_users = db.query(User).filter(
        and_(
            User.facility_id == facility.id,
            User.created_at >= start_date,
            User.created_at <= end_date
        )
    ).count()
    
    # Training completion analytics
    training_completions = db.query(TrainingAssignment).filter(
        and_(
            TrainingAssignment.facility_id == facility.id,
            TrainingAssignment.completed_at >= start_date,
            TrainingAssignment.completed_at <= end_date,
            TrainingAssignment.status == "completed"
        )
    ).count()
    
    # Calendar event analytics
    events_created = db.query(CalendarEvent).filter(
        and_(
            CalendarEvent.facility_id == facility.id,
            CalendarEvent.created_at >= start_date,
            CalendarEvent.created_at <= end_date,
            CalendarEvent.created_by_admin == True
        )
    ).count()
    
    return {
        "period_days": days,
        "new_users": new_users,
        "training_completions": training_completions,
        "events_created": events_created,
        "current_user_count": facility.current_user_count,
        "available_seats": 999999,  # Large number to represent unlimited seats
        "utilization_rate": 0  # Pro users have unlimited capacity
    } 