"""
Description: Calendar integration API endpoints for the EnCompliance application.
Purpose: Provides REST API endpoints for connecting, importing, and syncing external calendars
(Google Calendar and Apple Calendar). Implements OAuth flows and CalDAV connections.
Educational Note: Demonstrates secure external API integration with proper error handling.
Reference: OAuth 2.0 - https://oauth.net/2/, CalDAV - https://tools.ietf.org/html/rfc4791
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from app.database import get_db
from app.models.user import User
from app.models import CalendarConnection
from app.auth.dependencies import get_current_active_user
from app.utils.tiers import get_tier_from_subscription_status
from app.utils.access_control import can_access_feature
from app.services.google_calendar_service import GoogleCalendarService
from app.services.apple_calendar_service import AppleCalendarService

logger = logging.getLogger(__name__)

# Pydantic schemas
class GoogleOAuthResponse(BaseModel):
    authorization_url: str

class GoogleCallbackRequest(BaseModel):
    code: str

class AppleCalendarRequest(BaseModel):
    username: str
    password: str
    server_url: Optional[str] = None

class CalendarConnectionResponse(BaseModel):
    id: int
    provider: str
    calendar_id: str
    calendar_name: Optional[str]
    is_active: bool
    sync_enabled: bool
    token_expires_at: Optional[str]
    created_at: Optional[str]

class SyncRequest(BaseModel):
    connection_id: int

class SyncResponse(BaseModel):
    success: bool
    imported_count: Optional[int] = 0
    exported_count: Optional[int] = 0
    message: str
    error: Optional[str] = None

# Initialize router
router = APIRouter(prefix="/calendar/integration", tags=["Calendar Integration"])

@router.get("/google/auth", response_model=GoogleOAuthResponse)
async def initiate_google_oauth(
    current_user: User = Depends(get_current_active_user)
):
    """Initiate Google Calendar OAuth flow."""
    # Check user tier access
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    if not can_access_feature(user_tier, "calendar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calendar integration requires a Pro or Enterprise subscription."
        )
    
    try:
        auth_url = GoogleCalendarService.get_authorization_url()
        return GoogleOAuthResponse(authorization_url=auth_url)
    except Exception as e:
        logger.error(f"Error initiating Google OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Google Calendar authorization"
        )

@router.post("/google/callback")
async def handle_google_callback(
    request: GoogleCallbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Handle Google Calendar OAuth callback."""
    # Check user tier access
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    if not can_access_feature(user_tier, "calendar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calendar integration requires a Pro or Enterprise subscription."
        )
    
    result = await GoogleCalendarService.handle_oauth_callback(
        db=db,
        user_id=current_user.id,
        authorization_code=request.code
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/apple/connect")
async def connect_apple_calendar(
    request: AppleCalendarRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Connect to Apple Calendar via CalDAV."""
    # Check user tier access
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    if not can_access_feature(user_tier, "calendar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calendar integration requires a Pro or Enterprise subscription."
        )
    
    result = await AppleCalendarService.create_connection(
        db=db,
        user_id=current_user.id,
        username=request.username,
        password=request.password,
        server_url=request.server_url
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/connections", response_model=List[CalendarConnectionResponse])
async def get_calendar_connections(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all calendar connections for the current user."""
    # Check user tier access
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    if not can_access_feature(user_tier, "calendar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calendar integration requires a Pro or Enterprise subscription."
        )
    
    connections = db.query(CalendarConnection).filter(
        CalendarConnection.user_id == current_user.id,
        CalendarConnection.is_active == True
    ).all()
    
    return [
        CalendarConnectionResponse(
            id=conn.id,
            provider=conn.provider,
            calendar_id=conn.calendar_id,
            calendar_name=conn.calendar_name,
            is_active=conn.is_active,
            sync_enabled=conn.sync_enabled,
            token_expires_at=conn.token_expires_at.isoformat() if conn.token_expires_at else None,
            created_at=conn.created_at.isoformat() if conn.created_at else None
        )
        for conn in connections
    ]

@router.delete("/connections/{connection_id}")
async def disconnect_calendar(
    connection_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disconnect a calendar connection."""
    # Check user tier access
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    if not can_access_feature(user_tier, "calendar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calendar integration requires a Pro or Enterprise subscription."
        )
    
    connection = db.query(CalendarConnection).filter(
        CalendarConnection.id == connection_id,
        CalendarConnection.user_id == current_user.id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar connection not found"
        )
    
    # Soft delete by marking as inactive
    connection.is_active = False
    db.commit()
    
    return {"message": "Calendar connection disconnected successfully"}

@router.post("/import/{provider}")
async def import_calendar_events(
    provider: str,
    connection_id: int = Query(..., description="Calendar connection ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Import events from external calendar."""
    # Check user tier access
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    if not can_access_feature(user_tier, "calendar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calendar integration requires a Pro or Enterprise subscription."
        )
    
    # Validate provider
    if provider not in ["google", "apple"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider. Must be 'google' or 'apple'"
        )
    
    # Get connection
    connection = db.query(CalendarConnection).filter(
        CalendarConnection.id == connection_id,
        CalendarConnection.user_id == current_user.id,
        CalendarConnection.provider == provider,
        CalendarConnection.is_active == True
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar connection not found"
        )
    
    # Import events based on provider
    if provider == "google":
        result = await GoogleCalendarService.import_events(db, connection)
    else:  # apple
        result = await AppleCalendarService.import_events(db, connection)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/sync/{provider}", response_model=SyncResponse)
async def sync_calendar_events(
    provider: str,
    connection_id: int = Query(..., description="Calendar connection ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sync events bidirectionally with external calendar."""
    # Check user tier access
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    if not can_access_feature(user_tier, "calendar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calendar integration requires a Pro or Enterprise subscription."
        )
    
    # Validate provider
    if provider not in ["google", "apple"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider. Must be 'google' or 'apple'"
        )
    
    # Get connection
    connection = db.query(CalendarConnection).filter(
        CalendarConnection.id == connection_id,
        CalendarConnection.user_id == current_user.id,
        CalendarConnection.provider == provider,
        CalendarConnection.is_active == True
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar connection not found"
        )
    
    # Sync events based on provider
    if provider == "google":
        result = await GoogleCalendarService.sync_events(db, connection)
    else:  # apple
        result = await AppleCalendarService.sync_events(db, connection)
    
    return SyncResponse(
        success=result["success"],
        imported_count=result.get("imported_count", 0),
        exported_count=result.get("exported_count", 0),
        message=result["message"],
        error=result.get("error")
    )

@router.get("/sync/status")
async def get_sync_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get sync status for all calendar connections."""
    # Check user tier access
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    if not can_access_feature(user_tier, "calendar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calendar integration requires a Pro or Enterprise subscription."
        )
    
    connections = db.query(CalendarConnection).filter(
        CalendarConnection.user_id == current_user.id,
        CalendarConnection.is_active == True
    ).all()
    
    status_info = []
    for conn in connections:
        # Count synced events
        from app.models.calendar_event import CalendarEvent
        synced_events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.external_calendar_provider == conn.provider,
            CalendarEvent.sync_status == 'synced'
        ).count()
        
        status_info.append({
            "connection_id": conn.id,
            "provider": conn.provider,
            "calendar_name": conn.calendar_name,
            "sync_enabled": conn.sync_enabled,
            "synced_events_count": synced_events,
            "last_sync": None  # TODO: Add last sync timestamp to connection model
        })
    
    return {"connections": status_info} 