"""
Description: Real-time synchronization API endpoints for team member account synchronization.
Purpose: Provides Server-Sent Events (SSE) streams and sync endpoints to keep team member accounts 
synchronized with facility administrator changes in real-time.

Educational Note: Server-Sent Events (SSE) provide a standardized way to stream real-time updates 
from server to client over HTTP. Unlike WebSockets, SSE is unidirectional and uses standard HTTP, 
making it ideal for real-time notifications and data synchronization scenarios.
Reference: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database import get_db
from app.auth.dependencies import get_current_user, require_facility_admin, require_team_member
from app.models.user import User
from app.models.sync_event import SyncEvent
from app.services.sync_service import SyncService
from app.schemas.sync import SyncEventResponse, SyncDataResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Global dictionary to track active SSE connections
# Key: user_id, Value: asyncio.Queue for sending events
active_connections: Dict[int, asyncio.Queue] = {}


@router.get("/events")
async def stream_sync_events(
    request: Request,
    user_id: int,
    facility_id: int,
    current_user: User = Depends(require_team_member),
    db: Session = Depends(get_db)
):
    """
    Description: SSE endpoint that streams real-time synchronization events to team members.
    Purpose: Establishes Server-Sent Events connection for a team member to receive real-time 
    updates when facility administrator makes changes affecting their account.
    
    Educational Note: SSE connections are persistent HTTP connections that allow server to push 
    data to client. The connection stays open until client disconnects or server closes it.
    """
    
    # Verify user has access to this facility
    if current_user.id != user_id or current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail="Access denied to facility data")
    
    # Verify user is team member
    if current_user.user_role != "team_member":
        raise HTTPException(status_code=403, detail="SSE sync only available for team members")
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for the connected team member"""
        
        # Create event queue for this connection
        event_queue = asyncio.Queue()
        active_connections[user_id] = event_queue
        
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connection', 'status': 'connected', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
            
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client {user_id} disconnected from SSE stream")
                    break
                
                try:
                    # Wait for event with timeout to allow disconnect checks
                    event_data = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
                except Exception as e:
                    logger.error(f"Error in SSE stream for user {user_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"SSE connection error for user {user_id}: {e}")
        finally:
            # Clean up connection
            if user_id in active_connections:
                del active_connections[user_id]
            logger.info(f"SSE connection closed for user {user_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.get("/account-overview")
async def sync_account_overview(
    facility_id: int,
    current_user: User = Depends(require_team_member),
    db: Session = Depends(get_db)
) -> SyncDataResponse:
    """
    Description: Force sync endpoint for account overview data.
    Purpose: Provides current facility account data for team member synchronization.
    """
    
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail="Access denied to facility data")
    
    sync_service = SyncService(db)
    # Pass user_id to update team member's state and facility_type
    account_data = await sync_service.get_account_overview(facility_id, current_user.id)
    
    return SyncDataResponse(
        type="account_update",
        data=account_data,
        timestamp=datetime.now(timezone.utc).isoformat(),
        facility_id=facility_id
    )


@router.get("/document-library")
async def sync_document_library(
    facility_id: int,
    current_user: User = Depends(require_team_member),
    db: Session = Depends(get_db)
) -> SyncDataResponse:
    """
    Description: Force sync endpoint for document library data.
    Purpose: Provides current document library state for team member synchronization.
    """
    
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail="Access denied to facility data")
    
    sync_service = SyncService(db)
    # Pass user_id to get user-specific documents based on their associations
    document_data = await sync_service.get_document_library(facility_id, current_user.id)
    
    return SyncDataResponse(
        type="document_update",
        data=document_data,
        timestamp=datetime.now(timezone.utc).isoformat(),
        facility_id=facility_id
    )


@router.get("/calendar-events")
async def sync_calendar_events(
    facility_id: int,
    current_user: User = Depends(require_team_member),
    db: Session = Depends(get_db)
) -> SyncDataResponse:
    """
    Description: Force sync endpoint for calendar events data.
    Purpose: Provides current calendar events for team member synchronization.
    """
    
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail="Access denied to facility data")
    
    sync_service = SyncService(db)
    calendar_data = await sync_service.get_calendar_events(facility_id, current_user.id)
    
    return SyncDataResponse(
        type="calendar_update",
        data=calendar_data,
        timestamp=datetime.now(timezone.utc).isoformat(),
        facility_id=facility_id
    )


@router.get("/training-data")
async def sync_training_data(
    facility_id: int,
    current_user: User = Depends(require_team_member),
    db: Session = Depends(get_db)
) -> SyncDataResponse:
    """
    Description: Force sync endpoint for training data.
    Purpose: Provides current training assignments and progress for team member synchronization.
    """
    
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail="Access denied to facility data")
    
    sync_service = SyncService(db)
    training_data = await sync_service.get_training_data(facility_id, current_user.id)
    
    return SyncDataResponse(
        type="training_update",
        data=training_data,
        timestamp=datetime.now(timezone.utc).isoformat(),
        facility_id=facility_id
    )


@router.get("/updates")
async def get_sync_updates(
    user_id: int,
    facility_id: int,
    since: Optional[int] = None,
    current_user: User = Depends(require_team_member),
    db: Session = Depends(get_db)
) -> Dict[str, List[SyncEventResponse]]:
    """
    Description: Polling endpoint for sync updates.
    Purpose: Fallback mechanism for clients that cannot maintain SSE connections.
    """
    
    if current_user.id != user_id or current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail="Access denied to facility data")
    
    since_datetime = None
    if since:
        since_datetime = datetime.fromtimestamp(since / 1000, tz=timezone.utc)
    
    sync_service = SyncService(db)
    updates = await sync_service.get_recent_updates(facility_id, user_id, since_datetime)
    
    return {"updates": updates}


async def broadcast_sync_event(
    facility_id: int, 
    event_type: str, 
    data: dict, 
    target_user_ids: Optional[List[int]] = None
):
    """
    Description: Broadcast sync event to connected team members.
    Purpose: Sends real-time updates to all connected team members in a facility
    when administrator makes changes.
    
    Educational Note: This function pushes events to active SSE connections
    using asyncio queues for efficient async communication.
    """
    
    event_data = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "facility_id": facility_id
    }
    
    # If specific users targeted, send only to them
    if target_user_ids:
        target_connections = {
            user_id: queue for user_id, queue in active_connections.items() 
            if user_id in target_user_ids
        }
    else:
        # Send to all connected users from this facility
        # Note: In production, we'd query DB to filter by facility_id
        target_connections = active_connections
    
    # Send event to all target connections
    for user_id, queue in target_connections.items():
        try:
            await queue.put(event_data)
            logger.info(f"Sent sync event {event_type} to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send sync event to user {user_id}: {e}")
            # Remove failed connection
            if user_id in active_connections:
                del active_connections[user_id]


@router.post("/trigger-sync")
async def trigger_facility_sync(
    facility_id: int,
    event_type: str,
    data: dict,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """
    Description: Endpoint for facility administrators to trigger sync events.
    Purpose: Allows admin actions to immediately notify team members of changes.
    """
    
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail="Access denied to facility")
    
    # Get all team members for this facility
    team_members = db.query(User).filter(
        and_(
            User.facility_id == facility_id,
            User.user_role == "team_member"
        )
    ).all()
    
    target_user_ids = [member.id for member in team_members]
    
    # Broadcast to connected team members
    await broadcast_sync_event(facility_id, event_type, data, target_user_ids)
    
    # Store sync event in database for polling fallback
    sync_service = SyncService(db)
    await sync_service.create_sync_event(facility_id, event_type, data, target_user_ids)
    
    return {"status": "success", "notified_users": len(target_user_ids)} 