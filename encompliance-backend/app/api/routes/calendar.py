"""
Description: Calendar API endpoints for the EnCompliance application.
Purpose: Provides REST API endpoints for managing calendar events and AI-driven scheduling.
Implements paywall restrictions to limit access to Pro and Enterprise subscription tiers.
Uses database persistence for calendar events with proper user association.
"""

"""
Calendar API Routes
------------------
This module defines the calendar API endpoints for the EnCompliance system.
It provides:
- Calendar event CRUD operations with database persistence
- AI-powered scheduling features
- Paywall enforcement for feature access based on user tier
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import json
import uuid
from openai import AsyncOpenAI
from fastapi.responses import JSONResponse
import os

from app.database import get_db
from app.models.user import User
from app.models.calendar_event import CalendarEvent as CalendarEventModel
from app.auth.dependencies import get_current_active_user
from app.utils.tiers import get_tier_from_subscription_status
from app.utils.access_control import can_access_feature
from app.core.config import get_settings
from app.schemas.settings import UserLLMSettings
from app.services.notification_service import NotificationService
from app.services.calendar_reminder_service import CalendarReminderService
from app.utils.preview_data import get_sample_calendar_events
from app.models.training import TrainingAssignment as TrainingAssignmentModel
from functools import lru_cache
from time import time

# Set up logging
logger = logging.getLogger(__name__)

# Simple in-memory cache for training settings to prevent excessive DB calls
_training_settings_cache = {}
_training_stats_cache = {}
_request_counts = {}  # Track request counts per user
_circuit_breaker = {"broken": False, "break_time": 0, "failure_count": 0}  # Circuit breaker state
CACHE_TTL = 30  # 30 seconds cache
RATE_LIMIT_WINDOW = 60  # 1 minute window
RATE_LIMIT_MAX_REQUESTS = 5  # Max requests per window (reduced from 20)
AGGRESSIVE_RATE_LIMIT = 3  # Block after 3 requests in 10 seconds
AGGRESSIVE_WINDOW = 10  # 10 second window for aggressive limiting
CIRCUIT_BREAKER_THRESHOLD = 10  # Break circuit after 10 rapid failures
CIRCUIT_BREAKER_TIMEOUT = 300  # Keep circuit broken for 5 minutes

# Initialize settings and OpenAI client
settings = get_settings()
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# -------------------------------------------------------------
# Development flags
# -------------------------------------------------------------
# Set DISABLE_TRAINING_RATE_LIMITS=true in your environment (or .env) to
# completely bypass the aggressive rate-limit / circuit-breaker logic while
# you are running the frontend in dev/hot-reload mode.  Production instances
# should never set this flag.

DISABLE_TRAINING_RATE_LIMITS = os.getenv("DISABLE_TRAINING_RATE_LIMITS", "false").lower() in ("1", "true", "yes")

# Define schema models
class CalendarEventBase(BaseModel):
    title: str
    start: str
    end: str
    description: Optional[str] = None
    location: Optional[str] = None
    allDay: Optional[bool] = False

class CalendarEventCreate(CalendarEventBase):
    pass

class CalendarEvent(CalendarEventBase):
    id: str

    class Config:
        from_attributes = True

class AIScheduleRequest(BaseModel):
    prompt: str = Field(..., description="Natural language prompt describing the event to schedule")

class AIScheduleResponse(BaseModel):
    event: CalendarEventBase

class TrainingSettings(BaseModel):
    """Training calendar settings schema."""
    show_training_events: bool = True
    show_certification_deadlines: bool = True
    show_assignment_deadlines: bool = True
    reminder_days_before: int = 7

class TrainingStats(BaseModel):
    """Training statistics schema."""
    total_assignments: int = 0
    completed_assignments: int = 0
    overdue_assignments: int = 0
    upcoming_deadlines: int = 0
    completion_rate: float = 0.0

# Initialize router
router = APIRouter(prefix="/calendar", tags=["Calendar"])

# Add OPTIONS handler for CORS preflight requests
@router.options("/events")
@router.options("/events/{event_id}")
@router.options("/preview/events")
async def options_calendar():
    """
    Handle OPTIONS requests for calendar endpoints.
    """
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:5174",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, x-token",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(content={}, headers=headers)

@router.get("/preview/events")
async def get_preview_events():
    """
    Get sample calendar events for preview mode.
    Available to all users regardless of subscription tier.
    """
    return get_sample_calendar_events()

@router.get("/events", response_model=List[CalendarEvent])
async def get_events(
    include_training: Optional[bool] = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all calendar events for the current user.
    If include_training is True and user is facility admin, includes training events they created.
    """
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access calendar feature
    # For freemium model, we now allow preview access
    if not can_access_feature(user_tier, "calendar"):
        # Return preview data instead of blocking access
        return get_sample_calendar_events()
    
    # Get events for this user from database
    user_events_filter = CalendarEventModel.user_id == current_user.id
    
    # If user is facility admin and wants training events, include those they created
    if include_training and hasattr(current_user, 'administered_facility') and current_user.administered_facility:
        facility_id = current_user.administered_facility.id
        
        # Create a combined filter for user events OR training events from their facility
        training_events_filter = (
            (CalendarEventModel.facility_id == facility_id) &
            (CalendarEventModel.created_by_admin == True) &
            (CalendarEventModel.event_type.in_(['training_assignment', 'certification_renewal', 'training_deadline']))
        )
        
        # Combine filters with OR
        combined_filter = user_events_filter | training_events_filter
        db_events = db.query(CalendarEventModel).filter(combined_filter).all()
    else:
        db_events = db.query(CalendarEventModel).filter(user_events_filter).all()
    
    # Convert to response format
    user_events = []
    for event in db_events:
        user_events.append({
            "id": event.id,
            "title": event.title,
            "start": event.start,
            "end": event.end,
            "description": event.description,
            "location": event.location,
            "allDay": event.all_day,
            "eventType": getattr(event, 'event_type', 'general'),
            "trainingProgramId": getattr(event, 'training_program_id', None),
            "trainingAssignmentId": getattr(event, 'training_assignment_id', None),
            "trainingCompletionId": getattr(event, 'training_completion_id', None),
            "createdByAdmin": getattr(event, 'created_by_admin', False),
            "isEditableByUser": getattr(event, 'is_editable_by_user', True)
        })
    
    return user_events

@router.post("/events", response_model=CalendarEvent, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: CalendarEventCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new calendar event.
    """
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access calendar feature
    # paywall check for calendar
    if not can_access_feature(user_tier, "calendar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calendar feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    # Create a new event with a unique ID
    event_id = str(uuid.uuid4())
    
    # Create database event
    db_event = CalendarEventModel(
        id=event_id,
        user_id=current_user.id,
        facility_id=current_user.facility_id,  # Associate with user's facility
        title=event.title,
        start=event.start,
        end=event.end,
        description=event.description,
        location=event.location,
        all_day=event.allDay
    )
    
    # Save to database
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Create notification for calendar event creation (handle errors gracefully)
    try:
        await NotificationService.create_calendar_notification(
            db=db,
            user_id=current_user.id,
            event_id=event_id,
            action="created",
            event_title=event.title
        )
    except Exception as e:
        logger.error(f"Failed to create calendar notification: {e}")
        # Don't fail the entire request if notification creation fails
    
    # Return the created event
    return {
        "id": db_event.id,
        "title": db_event.title,
        "start": db_event.start,
        "end": db_event.end,
        "description": db_event.description,
        "location": db_event.location,
        "allDay": db_event.all_day
    }

@router.put("/events/{event_id}", response_model=CalendarEvent)
async def update_event(
    event_id: str,
    event: CalendarEventCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing calendar event.
    """
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access calendar feature
    # paywall check for calendar
    if not can_access_feature(user_tier, "calendar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calendar feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    # Check if the event exists and belongs to the current user
    db_event = db.query(CalendarEventModel).filter(
        CalendarEventModel.id == event_id,
        CalendarEventModel.user_id == current_user.id
    ).first()
    
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Update the event
    db_event.title = event.title
    db_event.start = event.start
    db_event.end = event.end
    db_event.description = event.description
    db_event.location = event.location
    db_event.all_day = event.allDay
    
    # Save changes
    db.commit()
    db.refresh(db_event)
    
    # Create notification for calendar event update (handle errors gracefully)
    try:
        await NotificationService.create_calendar_notification(
            db=db,
            user_id=current_user.id,
            event_id=event_id,
            action="updated",
            event_title=event.title
        )
    except Exception as e:
        logger.error(f"Failed to create calendar notification: {e}")
        # Don't fail the entire request if notification creation fails
    
    # Return the updated event
    return {
        "id": db_event.id,
        "title": db_event.title,
        "start": db_event.start,
        "end": db_event.end,
        "description": db_event.description,
        "location": db_event.location,
        "allDay": db_event.all_day
    }

@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a calendar event.
    """
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access calendar feature
    # paywall check for calendar
    if not can_access_feature(user_tier, "calendar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calendar feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )
    
    # Check if the event exists and belongs to the current user
    db_event = db.query(CalendarEventModel).filter(
        CalendarEventModel.id == event_id,
        CalendarEventModel.user_id == current_user.id
    ).first()
    
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Get event title before deletion for notification
    event_title = db_event.title
    
    # Delete the event
    db.delete(db_event)
    db.commit()
    
    # Create notification for calendar event deletion (handle errors gracefully)
    try:
        await NotificationService.create_calendar_notification(
            db=db,
            user_id=current_user.id,
            event_id=event_id,
            action="deleted",
            event_title=event_title
        )
    except Exception as e:
        logger.error(f"Failed to create calendar notification: {e}")
        # Don't fail the entire request if notification creation fails
    
    # No content response
    return None

@router.post("/ai-schedule", response_model=AIScheduleResponse)
async def ai_schedule(
    request: AIScheduleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Use AI to parse a natural language scheduling request and create an event.
    """
    # Get user tier
    user_tier = get_tier_from_subscription_status(current_user.subscription_status)
    
    # Check if user can access AI pro mode feature
    # paywall check for ai_pro_mode
    if not can_access_feature(user_tier, "ai_pro_mode"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI scheduling feature requires a Pro or Enterprise subscription. Please upgrade your plan."
        )

    # Get user's selected LLM model from settings
    def get_user_selected_model(user) -> str:
        import json
        try:
            if user.encrypted_settings:
                settings_dict = json.loads(user.encrypted_settings.decode())
                model = settings_dict.get('model') or settings_dict.get('selectedModel')
                if model:
                    return model
        except Exception:
            pass
        # Fallback default
        return "gpt-4.1-nano"

    model = get_user_selected_model(current_user)
    
    try:
        # Use OpenAI to parse the natural language request
        prompt = f"""
        Parse the following scheduling request into a structured event format.
        Request: \"{request.prompt}\"
        
        Provide a JSON response with the following fields:
        - title: The title of the event
        - start: The start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        - end: The end time in ISO format (YYYY-MM-DDTHH:MM:SS)
        - description: A brief description of the event
        - location: The location of the event (if specified)
        - allDay: Boolean indicating if this is an all-day event
        
        Current date and time: {datetime.now().isoformat()}
        """
        
        response = await openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an AI assistant that helps schedule events."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        # Extract the JSON response
        ai_response = response.choices[0].message.content.strip()
        
        # Try to find and parse the JSON object in the response
        import re
        json_match = re.search(r'({.*})', ai_response, re.DOTALL)
        
        if json_match:
            event_data = json.loads(json_match.group(1))
        else:
            # Fallback if JSON parsing fails
            event_data = {
                "title": "AI Scheduled Event",
                "start": datetime.now().isoformat(),
                "end": datetime.now().isoformat(),
                "description": request.prompt,
                "location": "",
                "allDay": False
            }
        
        # Return the parsed event
        return {"event": event_data}
        
    except Exception as e:
        logger.error(f"Error in AI scheduling: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing AI scheduling request: {str(e)}"
        ) 

def check_circuit_breaker():
    """Check if circuit breaker should be triggered or reset."""
    current_time = time()
    
    # Check if circuit should be reset
    if _circuit_breaker["broken"] and (current_time - _circuit_breaker["break_time"]) > CIRCUIT_BREAKER_TIMEOUT:
        _circuit_breaker["broken"] = False
        _circuit_breaker["failure_count"] = 0
        logger.info("Circuit breaker reset - training endpoints re-enabled")
    
    return _circuit_breaker["broken"]

def trigger_circuit_breaker():
    """Trigger the circuit breaker."""
    _circuit_breaker["failure_count"] += 1
    if _circuit_breaker["failure_count"] >= CIRCUIT_BREAKER_THRESHOLD:
        _circuit_breaker["broken"] = True
        _circuit_breaker["break_time"] = time()
        logger.error(f"CIRCUIT BREAKER TRIGGERED! Training endpoints disabled for {CIRCUIT_BREAKER_TIMEOUT} seconds due to excessive requests.")

@router.get("/settings/training", response_model=TrainingSettings)
async def get_training_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get training calendar settings for the current user.
    """
    # In development mode we optionally bypass rate-limit / circuit-breaker logic entirely.
    # This prevents 429/503 noise when the frontend hot-reloads.
    if DISABLE_TRAINING_RATE_LIMITS:
        return TrainingSettings(
            show_training_events=True,
            show_certification_deadlines=True,
            show_assignment_deadlines=True,
            reminder_days_before=7
        )

    # --- regular production path below ---
    # Check circuit breaker first
    if check_circuit_breaker():
        logger.warning(f"Circuit breaker is open - blocking training settings request from user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Training endpoints are temporarily disabled due to excessive requests. "
                   f"Please wait {CIRCUIT_BREAKER_TIMEOUT} seconds and refresh the page. "
                   f"This is likely due to a frontend infinite loop bug."
        )
    
    # Check cache first to prevent excessive calls
    cache_key = f"training_settings_{current_user.id}"
    current_time = time()
    
    # Rate limiting check
    user_key = f"settings_{current_user.id}"
    if user_key not in _request_counts:
        _request_counts[user_key] = []
    
    # Clean old requests outside the window
    _request_counts[user_key] = [req_time for req_time in _request_counts[user_key] 
                                if current_time - req_time < RATE_LIMIT_WINDOW]
    
    # Aggressive rate limiting - check for rapid requests
    recent_aggressive_requests = [req_time for req_time in _request_counts[user_key] 
                                 if current_time - req_time < AGGRESSIVE_WINDOW]
    
    if len(recent_aggressive_requests) >= AGGRESSIVE_RATE_LIMIT:
        trigger_circuit_breaker()
        logger.error(f"AGGRESSIVE RATE LIMIT EXCEEDED for training settings by user {current_user.id}. "
                    f"Requests in last {AGGRESSIVE_WINDOW}s: {len(recent_aggressive_requests)}. "
                    f"Triggering circuit breaker.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Training endpoints will be disabled for {CIRCUIT_BREAKER_TIMEOUT} seconds. "
                   f"This appears to be an infinite loop - check your frontend code."
        )
    
    # Check if user is making too many requests in general
    if len(_request_counts[user_key]) >= RATE_LIMIT_MAX_REQUESTS:
        trigger_circuit_breaker()
        logger.warning(f"Rate limit exceeded for training settings by user {current_user.id}. "
                      f"Requests in last {RATE_LIMIT_WINDOW}s: {len(_request_counts[user_key])}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Training endpoints will be disabled for {CIRCUIT_BREAKER_TIMEOUT} seconds."
        )
    
    _request_counts[user_key].append(current_time)
    
    if cache_key in _training_settings_cache:
        cached_data, timestamp = _training_settings_cache[cache_key]
        if current_time - timestamp < CACHE_TTL:
            return cached_data
    
    logger.info(f"Training settings requested by user {current_user.id} (cache miss)")
    
    # Create settings object
    settings = TrainingSettings(
        show_training_events=True,
        show_certification_deadlines=True,
        show_assignment_deadlines=True,
        reminder_days_before=7
    )
    
    # Cache the result
    _training_settings_cache[cache_key] = (settings, current_time)
    
    return settings

@router.put("/settings/training", response_model=TrainingSettings)
async def update_training_settings(
    settings: TrainingSettings,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update training calendar settings for the current user.
    """
    # For now, just return the settings as-is
    # In the future, these could be stored in user preferences
    return settings

@router.get("/training/stats", response_model=TrainingStats)
async def get_training_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get training statistics for the current user or facility.
    """
    if DISABLE_TRAINING_RATE_LIMITS:
        # Return minimal default stats in dev mode without hitting DB or rate limits
        return TrainingStats()

    # Check cache first to prevent excessive DB calls
    cache_key = f"training_stats_{current_user.id}"
    current_time = time()
    
    # Rate limiting check for stats endpoint
    user_key = f"stats_{current_user.id}"
    if user_key not in _request_counts:
        _request_counts[user_key] = []
    
    # Clean old requests outside the window
    _request_counts[user_key] = [req_time for req_time in _request_counts[user_key] 
                                if current_time - req_time < RATE_LIMIT_WINDOW]
    
    # Aggressive rate limiting - check for rapid requests
    recent_aggressive_requests = [req_time for req_time in _request_counts[user_key] 
                                 if current_time - req_time < AGGRESSIVE_WINDOW]
    
    if len(recent_aggressive_requests) >= AGGRESSIVE_RATE_LIMIT:
        logger.error(f"AGGRESSIVE RATE LIMIT EXCEEDED for training stats by user {current_user.id}. "
                    f"Requests in last {AGGRESSIVE_WINDOW}s: {len(recent_aggressive_requests)}. "
                    f"Blocking request to prevent infinite loop.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please wait {AGGRESSIVE_WINDOW} seconds before trying again. "
                   f"This appears to be an infinite loop - check your frontend code."
        )
    
    # Check if user is making too many requests in general
    if len(_request_counts[user_key]) >= RATE_LIMIT_MAX_REQUESTS:
        logger.warning(f"Rate limit exceeded for training stats by user {current_user.id}. "
                      f"Requests in last {RATE_LIMIT_WINDOW}s: {len(_request_counts[user_key])}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please wait before trying again."
        )
    
    _request_counts[user_key].append(current_time)
    
    if cache_key in _training_stats_cache:
        cached_data, timestamp = _training_stats_cache[cache_key]
        if current_time - timestamp < CACHE_TTL:
            return cached_data
    
    logger.info(f"Training stats requested by user {current_user.id} (cache miss)")
    
    try:
        # Initialize stats
        stats = TrainingStats()
        
        # If user is a facility admin, get facility-wide stats
        if hasattr(current_user, 'administered_facility') and current_user.administered_facility:
            facility_id = current_user.administered_facility.id
            
            # Get total assignments for the facility
            total_assignments = db.query(TrainingAssignmentModel).filter(
                TrainingAssignmentModel.facility_id == facility_id
            ).count()
            
            # Get completed assignments
            completed_assignments = db.query(TrainingAssignmentModel).filter(
                TrainingAssignmentModel.facility_id == facility_id,
                TrainingAssignmentModel.status == "completed"
            ).count()
            
            # Get overdue assignments
            overdue_assignments = db.query(TrainingAssignmentModel).filter(
                TrainingAssignmentModel.facility_id == facility_id,
                TrainingAssignmentModel.due_date < datetime.now(),
                TrainingAssignmentModel.status != "completed"
            ).count()
            
            # Get upcoming deadlines (next 30 days)
            from datetime import timedelta
            upcoming_deadline = datetime.now() + timedelta(days=30)
            upcoming_deadlines = db.query(TrainingAssignmentModel).filter(
                TrainingAssignmentModel.facility_id == facility_id,
                TrainingAssignmentModel.due_date <= upcoming_deadline,
                TrainingAssignmentModel.due_date >= datetime.now(),
                TrainingAssignmentModel.status != "completed"
            ).count()
            
            # Calculate completion rate
            completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0.0
            
            stats = TrainingStats(
                total_assignments=total_assignments,
                completed_assignments=completed_assignments,
                overdue_assignments=overdue_assignments,
                upcoming_deadlines=upcoming_deadlines,
                completion_rate=round(completion_rate, 1)
            )
        else:
            # For regular users, get their personal training stats
            user_assignments = db.query(TrainingAssignmentModel).filter(
                TrainingAssignmentModel.assigned_to == current_user.id
            ).count()
            
            user_completed = db.query(TrainingAssignmentModel).filter(
                TrainingAssignmentModel.assigned_to == current_user.id,
                TrainingAssignmentModel.status == "completed"
            ).count()
            
            user_overdue = db.query(TrainingAssignmentModel).filter(
                TrainingAssignmentModel.assigned_to == current_user.id,
                TrainingAssignmentModel.due_date < datetime.now(),
                TrainingAssignmentModel.status != "completed"
            ).count()
            
            from datetime import timedelta
            upcoming_deadline = datetime.now() + timedelta(days=30)
            user_upcoming = db.query(TrainingAssignmentModel).filter(
                TrainingAssignmentModel.assigned_to == current_user.id,
                TrainingAssignmentModel.due_date <= upcoming_deadline,
                TrainingAssignmentModel.due_date >= datetime.now(),
                TrainingAssignmentModel.status != "completed"
            ).count()
            
            user_completion_rate = (user_completed / user_assignments * 100) if user_assignments > 0 else 0.0
            
            stats = TrainingStats(
                total_assignments=user_assignments,
                completed_assignments=user_completed,
                overdue_assignments=user_overdue,
                upcoming_deadlines=user_upcoming,
                completion_rate=round(user_completion_rate, 1)
            )
        
        # Cache the result
        _training_stats_cache[cache_key] = (stats, current_time)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting training stats: {str(e)}")
        # Return default stats on error
        default_stats = TrainingStats()
        _training_stats_cache[cache_key] = (default_stats, current_time)
        return default_stats

@router.get("/debug/request-counts")
async def get_request_counts(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Debug endpoint to show request counts and help diagnose polling issues.
    Pass `?reset=true` to clear all in-memory counters and circuit-breaker state.
    """
    reset_flag = request.query_params.get('reset', 'false').lower() in ('1', 'true', 'yes')

    if reset_flag:
        _request_counts.clear()
        _circuit_breaker["broken"] = False
        _circuit_breaker["failure_count"] = 0

    current_time = time()
    debug_info = {}
    
    for user_key, requests in _request_counts.items():
        # Clean old requests
        recent_requests = [req_time for req_time in requests 
                          if current_time - req_time < RATE_LIMIT_WINDOW]
        debug_info[user_key] = {
            "recent_requests": len(recent_requests),
            "requests_per_minute": len(recent_requests),
            "last_request_ago": f"{current_time - recent_requests[-1]:.1f}s" if recent_requests else "N/A"
        }
    
    return {
        "current_time": current_time,
        "rate_limit_window": RATE_LIMIT_WINDOW,
        "max_requests_per_window": RATE_LIMIT_MAX_REQUESTS,
        "cache_ttl": CACHE_TTL,
        "request_counts": debug_info,
        "cache_status": {
            "settings_cache_size": len(_training_settings_cache),
            "stats_cache_size": len(_training_stats_cache)
        }
    }

@router.get("/health/training")
async def training_health_check():
    """
    Simple health check endpoint that doesn't require authentication.
    Can be used to test if the training endpoints are responsive.
    """
    return {
        "status": "healthy",
        "message": "Training endpoints are operational",
        "timestamp": time(),
        "endpoints": [
            "/api/v1/calendar/settings/training",
            "/api/v1/calendar/training/stats"
        ]
    } 