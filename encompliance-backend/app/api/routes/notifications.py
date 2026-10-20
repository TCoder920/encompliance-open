"""
Description: API routes for notifications.
Purpose: Provides endpoints for retrieving and managing user notifications.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.notification import Notification, NotificationUpdate, NotificationList
from app.schemas.push_subscription import PushSubscriptionCreate, PushSubscriptionResponse, PushSubscriptionDelete
from app.schemas.notification_settings import NotificationSettingsResponse, NotificationSettingsUpdate
from app.services.notification_service import NotificationService

router = APIRouter()

# Add OPTIONS handler for CORS preflight requests
@router.options("/")
@router.options("/{notification_id}")
@router.options("/settings")
@router.options("/unread-count")
@router.options("/{notification_id}/mark-as-read")
@router.options("/mark-all-as-read")
@router.options("/push/subscribe")
@router.options("/push/unsubscribe")
async def options_notifications():
    """
    Handle OPTIONS requests for notification endpoints.
    """
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:5174",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, x-token",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(content={}, headers=headers)


@router.get("/", response_model=NotificationList)
async def get_notifications(
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all notifications for the authenticated user.
    
    - **skip**: Number of notifications to skip (for pagination)
    - **limit**: Maximum number of notifications to return (for pagination)
    - **unread_only**: Whether to return only unread notifications
    """
    try:
        result = await NotificationService.get_notifications(
            db, 
            current_user.id, 
            skip, 
            limit,
            unread_only
        )
        
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get notifications for user {current_user.id}: {e}")
        
        # Return empty result on error
        return {
            "notifications": [],
            "total": 0,
            "unread_count": 0
        }


# Notification Settings Endpoints (must be before /{notification_id} to avoid conflicts)
@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user notification settings."""
    settings = await NotificationService.get_user_notification_settings(db, current_user.id)
    return settings


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings_data: NotificationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user notification settings."""
    # Convert to dict and filter out None values
    update_data = {k: v for k, v in settings_data.dict().items() if v is not None}
    
    settings = await NotificationService.update_notification_settings(
        db, 
        current_user.id, 
        update_data
    )
    return settings


@router.get("/unread-count", response_model=int)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the count of unread notifications for the authenticated user."""
    try:
        return await NotificationService.get_unread_count(db, current_user.id)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get unread count for user {current_user.id}: {e}")
        return 0


@router.get("/{notification_id}", response_model=Notification)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific notification by ID."""
    notification = await NotificationService.get_notification(db, notification_id, current_user.id)
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification


@router.put("/{notification_id}", response_model=Notification)
async def update_notification(
    notification_id: int,
    notification_data: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a specific notification by ID (mark as read/unread)."""
    notification = await NotificationService.get_notification(db, notification_id, current_user.id)
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Only allow updating is_read status
    if notification_data.is_read is not None:
        notification.is_read = notification_data.is_read
        db.commit()
        db.refresh(notification)
    
    return notification


@router.post("/{notification_id}/mark-as-read", response_model=Notification)
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a specific notification as read."""
    notification = await NotificationService.mark_as_read(db, notification_id, current_user.id)
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification


@router.post("/mark-all-as-read", response_model=int)
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read for the authenticated user."""
    count = await NotificationService.mark_all_as_read(db, current_user.id)
    return count


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific notification by ID."""
    result = await NotificationService.delete_notification(db, notification_id, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete all notifications for the authenticated user."""
    await NotificationService.delete_all_notifications(db, current_user.id)
    return None


# Push Subscription Endpoints
@router.post("/push/subscribe", response_model=PushSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_to_push(
    subscription_data: PushSubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Subscribe to push notifications."""
    subscription = await NotificationService.create_push_subscription(
        db, 
        current_user.id, 
        subscription_data.dict()
    )
    return subscription


@router.delete("/push/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_from_push(
    subscription_data: PushSubscriptionDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unsubscribe from push notifications."""
    result = await NotificationService.delete_push_subscription(
        db, 
        current_user.id, 
        subscription_data.endpoint
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push subscription not found"
        )
    return None


