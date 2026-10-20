"""
Description: API routes for notes.
Purpose: Provides endpoints for creating, retrieving, updating, and deleting notes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.note import Note, NoteCreate, NoteUpdate, NoteList, BulkOperationResponse
from app.services.note_service import NoteService
from app.services.notification_service import NotificationService
from app.utils.tiers import get_tier_from_subscription_status
from app.utils.access_control import can_access_feature, can_use_feature
from app.utils.preview_data import get_sample_notes

router = APIRouter()

# Educational Note: CORS OPTIONS handlers are required for preflight requests
# Reference: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS#preflighted_requests

@router.options("/")
@router.options("/{note_id}")
@router.options("/{note_id}/archive")
@router.options("/{note_id}/unarchive")
@router.options("/{note_id}/pin")
@router.options("/{note_id}/unpin")
@router.options("/bulk/delete-all")
@router.options("/bulk/archive-all")
@router.options("/preview")
async def options_notes():
    """
    Handle OPTIONS requests for all notes endpoints.
    Required for CORS preflight requests from the frontend.
    """
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:5174",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, x-token",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(content={}, headers=headers)


@router.post("/", response_model=Note, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new note for the authenticated user."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access notes feature
    if not can_access_feature(user_tier, "notes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notes feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    note = await NoteService.create_note(db, note_data, current_user.id)
    
    # Create notification for note creation
    await NotificationService.create_note_notification(
        db,
        current_user.id,
        note.id,
        "created",
        "Note Created",
        note.title
    )
    
    return note


@router.get("/preview")
async def get_preview_notes():
    """
    Get sample notes for preview mode.
    Available to all users regardless of subscription tier.
    """
    return {
        "notes": get_sample_notes(),
        "total": len(get_sample_notes()),
        "skip": 0,
        "limit": 100
    }


@router.get("/", response_model=NoteList)
async def get_notes(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    show_archived: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all notes for the authenticated user.
    
    - **skip**: Number of notes to skip (for pagination)
    - **limit**: Maximum number of notes to return (for pagination)
    - **search**: Optional search term to filter notes by title or content
    - **sort_by**: Field to sort by (created_at, updated_at, title)
    - **sort_order**: Sort order (asc, desc)
    - **show_archived**: Whether to include archived notes
    """
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access notes feature
    # For freemium model, we now allow preview access
    if not can_use_feature(user_tier, "notes"):
        # Return preview data instead of blocking access
        sample_notes = get_sample_notes()
        return {
            "notes": sample_notes,
            "total": len(sample_notes),
            "skip": skip,
            "limit": limit
        }
    
    # Validate sort_by parameter
    valid_sort_fields = ["created_at", "updated_at", "title"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by parameter. Must be one of: {', '.join(valid_sort_fields)}"
        )
    
    # Validate sort_order parameter
    valid_sort_orders = ["asc", "desc"]
    if sort_order.lower() not in valid_sort_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_order parameter. Must be one of: {', '.join(valid_sort_orders)}"
        )
    
    result = await NoteService.get_notes(
        db, 
        current_user.id, 
        skip, 
        limit, 
        search, 
        sort_by, 
        sort_order,
        show_archived
    )
    
    return result


@router.get("/{note_id}", response_model=Note)
async def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific note by ID."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access notes feature
    if not can_access_feature(user_tier, "notes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notes feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    note = await NoteService.get_note(db, note_id, current_user.id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return note


@router.put("/{note_id}", response_model=Note)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a specific note by ID."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access notes feature
    if not can_access_feature(user_tier, "notes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notes feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    note = await NoteService.update_note(db, note_id, note_data, current_user.id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Create notification for note update
    await NotificationService.create_note_notification(
        db,
        current_user.id,
        note.id,
        "updated",
        "Note Updated",
        note.title
    )
    
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific note by ID."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access notes feature
    if not can_access_feature(user_tier, "notes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notes feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    # Get the note first to have access to its title for the notification
    note = await NoteService.get_note(db, note_id, current_user.id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    note_title = note.title
    
    # Delete the note
    result = await NoteService.delete_note(db, note_id, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Create notification for note deletion
    await NotificationService.create_note_notification(
        db,
        current_user.id,
        note_id,
        "deleted",
        "Note Deleted",
        note_title
    )
    
    return None


@router.post("/{note_id}/archive", response_model=Note)
async def archive_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive a specific note by ID."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access notes feature
    if not can_access_feature(user_tier, "notes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notes feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    note = await NoteService.archive_note(db, note_id, current_user.id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Create notification for note archiving
    await NotificationService.create_note_notification(
        db,
        current_user.id,
        note.id,
        "archived",
        "Note Archived",
        note.title
    )
    
    return note


@router.post("/{note_id}/unarchive", response_model=Note)
async def unarchive_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unarchive a specific note by ID."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access notes feature
    if not can_access_feature(user_tier, "notes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notes feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    note = await NoteService.unarchive_note(db, note_id, current_user.id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Create notification for note unarchiving
    await NotificationService.create_note_notification(
        db,
        current_user.id,
        note.id,
        "unarchived",
        "Note Unarchived",
        note.title
    )
    
    return note


@router.post("/{note_id}/pin", response_model=Note)
async def pin_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pin a specific note by ID."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access notes feature
    if not can_access_feature(user_tier, "notes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notes feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    note = await NoteService.pin_note(db, note_id, current_user.id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return note


@router.post("/{note_id}/unpin", response_model=Note)
async def unpin_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unpin a specific note by ID."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access notes feature
    if not can_access_feature(user_tier, "notes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notes feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    note = await NoteService.unpin_note(db, note_id, current_user.id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return note


@router.delete("/bulk/delete-all", response_model=BulkOperationResponse)
async def delete_all_notes(
    archived_only: bool = Query(False, description="Delete only archived notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete all notes for the authenticated user."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access notes feature
    if not can_access_feature(user_tier, "notes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notes feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    count = await NoteService.delete_all_notes(db, current_user.id, archived_only)
    
    # Create notification for bulk deletion
    if count > 0:
        message = f"Deleted {count} {'archived ' if archived_only else ''}notes"
        await NotificationService.create_note_notification(
            db,
            current_user.id,
            None,  # No specific note ID for bulk operations
            "bulk_deleted",
            "Bulk Delete Completed",
            message
        )
    
    return BulkOperationResponse(
        count=count,
        message=f"Successfully deleted {count} {'archived ' if archived_only else ''}notes"
    )


@router.post("/bulk/archive-all", response_model=BulkOperationResponse)
async def archive_all_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive all non-archived notes for the authenticated user."""
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access notes feature
    if not can_access_feature(user_tier, "notes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Notes feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    count = await NoteService.archive_all_notes(db, current_user.id)
    
    # Create notification for bulk archiving
    if count > 0:
        await NotificationService.create_note_notification(
            db,
            current_user.id,
            None,  # No specific note ID for bulk operations
            "bulk_archived",
            "Bulk Archive Completed",
            f"Archived {count} notes"
        )
    
    return BulkOperationResponse(
        count=count,
        message=f"Successfully archived {count} notes"
    ) 