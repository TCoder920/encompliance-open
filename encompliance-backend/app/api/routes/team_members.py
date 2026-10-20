"""
Team Member Routes Module

This module defines API routes for team member specific operations including
profile management, name change requests, and role-based restrictions.

Key functionalities:
- Team member profile updates (limited fields)
- Name change request workflow
- Admin approval system for name changes
- Role-based access control

Dependencies:
- fastapi: For API routing and HTTP handling
- sqlalchemy: For database operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User, UserRole
from app.models.team_member_name_change_request import TeamMemberNameChangeRequest, NameChangeStatus
from app.schemas.user import (
    TeamMemberProfileUpdate, 
    TeamMemberNameChangeRequest as TeamMemberNameChangeRequestSchema,
    TeamMemberNameChangeResponse,
    UserUpdate
)
from app.auth.dependencies import get_current_active_user, require_facility_admin
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/team-members", tags=["team-members"])


@router.put("/profile")
async def update_team_member_profile(
    profile_data: TeamMemberProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update team member profile (limited fields only)."""
    if current_user.user_role != UserRole.TEAM_MEMBER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for team members"
        )
    
    try:
        # Team members can only update phone number directly
        if profile_data.phone_number is not None:
            current_user.phone_number = profile_data.phone_number
        
        # Name changes require approval
        if profile_data.full_name is not None and profile_data.full_name != current_user.full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name changes require admin approval. Use the name change request endpoint."
            )
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Team member {current_user.id} updated profile")
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": current_user.id,
                "full_name": current_user.full_name,
                "phone_number": current_user.phone_number,
                "email": current_user.email
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating team member profile: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/name-change-request", response_model=TeamMemberNameChangeResponse)
async def request_name_change(
    request_data: TeamMemberNameChangeRequestSchema,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit a name change request for admin approval."""
    if current_user.user_role != UserRole.TEAM_MEMBER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for team members"
        )
    
    # Check if there's already a pending request
    existing_request = db.query(TeamMemberNameChangeRequest).filter(
        TeamMemberNameChangeRequest.user_id == current_user.id,
        TeamMemberNameChangeRequest.status == NameChangeStatus.PENDING.value
    ).first()
    
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending name change request"
        )
    
    try:
        # Create name change request
        name_change_request = TeamMemberNameChangeRequest(
            user_id=current_user.id,
            current_name=current_user.full_name,
            requested_name=request_data.new_full_name,
            reason=request_data.reason
        )
        
        db.add(name_change_request)
        db.commit()
        db.refresh(name_change_request)
        
        logger.info(f"Team member {current_user.id} requested name change from '{current_user.full_name}' to '{request_data.new_full_name}'")
        
        return TeamMemberNameChangeResponse.from_orm(name_change_request)
        
    except Exception as e:
        logger.error(f"Error creating name change request: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create name change request"
        )


@router.get("/name-change-requests", response_model=List[TeamMemberNameChangeResponse])
async def get_my_name_change_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all name change requests for the current team member."""
    if current_user.user_role != UserRole.TEAM_MEMBER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for team members"
        )
    
    requests = db.query(TeamMemberNameChangeRequest).filter(
        TeamMemberNameChangeRequest.user_id == current_user.id
    ).order_by(TeamMemberNameChangeRequest.requested_at.desc()).all()
    
    return [TeamMemberNameChangeResponse.from_orm(req) for req in requests]


# Admin endpoints for managing name change requests
@router.get("/admin/name-change-requests", response_model=List[TeamMemberNameChangeResponse])
async def get_facility_name_change_requests(
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Get all pending name change requests for the facility (admin only)."""
    if not current_user.administered_facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    # Get all team members in the facility
    facility_team_members = db.query(User).filter(
        User.facility_id == current_user.administered_facility.id,
        User.user_role == UserRole.TEAM_MEMBER
    ).all()
    
    team_member_ids = [member.id for member in facility_team_members]
    
    # Get name change requests for facility team members
    requests = db.query(TeamMemberNameChangeRequest).filter(
        TeamMemberNameChangeRequest.user_id.in_(team_member_ids)
    ).order_by(TeamMemberNameChangeRequest.requested_at.desc()).all()
    
    return [TeamMemberNameChangeResponse.from_orm(req) for req in requests]


@router.post("/admin/name-change-requests/{request_id}/approve")
async def approve_name_change_request(
    request_id: int,
    admin_notes: str = None,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Approve a name change request (admin only)."""
    if not current_user.administered_facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    # Get the request
    name_request = db.query(TeamMemberNameChangeRequest).filter(
        TeamMemberNameChangeRequest.id == request_id
    ).first()
    
    if not name_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Name change request not found"
        )
    
    # Verify the user is in the admin's facility
    user = db.query(User).filter(User.id == name_request.user_id).first()
    if not user or user.facility_id != current_user.administered_facility.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot approve request for user outside your facility"
        )
    
    if not name_request.is_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request has already been reviewed"
        )
    
    try:
        # Approve the request
        name_request.approve(current_user.id, admin_notes)
        
        # Update the user's name
        user.full_name = name_request.requested_name
        
        db.commit()
        
        logger.info(f"Admin {current_user.id} approved name change request {request_id}")
        
        return {"message": "Name change request approved successfully"}
        
    except Exception as e:
        logger.error(f"Error approving name change request: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve name change request"
        )


@router.post("/admin/name-change-requests/{request_id}/reject")
async def reject_name_change_request(
    request_id: int,
    admin_notes: str = None,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """Reject a name change request (admin only)."""
    if not current_user.administered_facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    # Get the request
    name_request = db.query(TeamMemberNameChangeRequest).filter(
        TeamMemberNameChangeRequest.id == request_id
    ).first()
    
    if not name_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Name change request not found"
        )
    
    # Verify the user is in the admin's facility
    user = db.query(User).filter(User.id == name_request.user_id).first()
    if not user or user.facility_id != current_user.administered_facility.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot reject request for user outside your facility"
        )
    
    if not name_request.is_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request has already been reviewed"
        )
    
    try:
        # Reject the request
        name_request.reject(current_user.id, admin_notes)
        
        db.commit()
        
        logger.info(f"Admin {current_user.id} rejected name change request {request_id}")
        
        return {"message": "Name change request rejected"}
        
    except Exception as e:
        logger.error(f"Error rejecting name change request: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject name change request"
        ) 