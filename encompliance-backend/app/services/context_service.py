"""
Description: Context service for gathering user data for AI assistant context.
Purpose: Provides functions to fetch and format user calendar events, notes, and training data
for inclusion in AI assistant conversations using database persistence.
Educational Note: Implements context aggregation pattern for enhanced AI responses with SQLAlchemy ORM.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.services.note_service import NoteService
from app.services.training_context_service import TrainingContextService
from app.models.calendar_event import CalendarEvent as CalendarEventModel
from app.utils.tiers import get_tier_from_subscription_status
from app.utils.access_control import can_access_feature
import logging

logger = logging.getLogger(__name__)

class ContextService:
    @staticmethod
    async def get_user_calendar_events(
        user_id: int,
        user_subscription_status: str,
        db: Optional[Session] = None,
        calendar_events_storage: Optional[Dict[str, Dict[str, Any]]] = None,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get user's calendar events for AI context using database.
        
        Args:
            db: Database session
            user_id: ID of the user
            user_subscription_status: User's subscription status for access control
            calendar_events_storage: Optional in-memory storage for calendar events (testing/cache)
            days_ahead: Number of days ahead to fetch events
            
        Returns:
            List of formatted calendar events
        """
        try:
            # Check if user can access calendar feature
            user_tier = get_tier_from_subscription_status(user_subscription_status)
            if not can_access_feature(user_tier, "calendar"):
                logger.info(f"User {user_id} cannot access calendar feature")
                return []
            
            # Get current time and future cutoff
            current_time = datetime.now()
            future_cutoff = current_time + timedelta(days=days_ahead)
            past_cutoff = current_time - timedelta(days=7)
            
            # Pull events from provided storage (tests/cache) or database fallback
            if calendar_events_storage is not None:
                raw_events = list(calendar_events_storage.values())
            else:
                if db is None:
                    logger.info("No database session provided for calendar events fetch")
                    return []
                raw_events = db.query(CalendarEventModel).filter(CalendarEventModel.user_id == user_id).all()
            
            # Filter events within the time range
            user_events = []
            for event in raw_events:
                try:
                    # Support dict or ORM object shapes
                    event_user_id = event.get("user_id") if isinstance(event, dict) else getattr(event, "user_id", None)
                    if event_user_id != user_id:
                        continue

                    event_start_raw = event.get("start") if isinstance(event, dict) else getattr(event, "start", None)
                    if not event_start_raw:
                        continue

                    # Parse event start time
                    event_start = datetime.fromisoformat(str(event_start_raw).replace('Z', '+00:00'))
                    if event_start.tzinfo:
                        event_start = event_start.replace(tzinfo=None)
                    
                    # Include events from past 7 days to current + days_ahead
                    if past_cutoff <= event_start <= future_cutoff:
                        formatted_event = {
                            "id": getattr(event, "id", None) if not isinstance(event, dict) else event.get("id"),
                            "title": event.get("title") if isinstance(event, dict) else getattr(event, "title", ""),
                            "start": event_start_raw,
                            "end": event.get("end") if isinstance(event, dict) else getattr(event, "end", None),
                            "description": event.get("description", "") if isinstance(event, dict) else (event.description or ""),
                            "location": event.get("location", "") if isinstance(event, dict) else (event.location or ""),
                            "allDay": event.get("allDay") if isinstance(event, dict) else getattr(event, "all_day", False)
                        }
                        user_events.append(formatted_event)
                except Exception as e:
                    event_identifier = event.get("id") if isinstance(event, dict) else getattr(event, "id", "<unknown>")
                    logger.warning(f"Error parsing event {event_identifier}: {e}")
                    continue
            
            # Sort events by start time
            user_events.sort(key=lambda x: x["start"])
            
            logger.info(f"Retrieved {len(user_events)} calendar events for user {user_id}")
            return user_events
            
        except Exception as e:
            logger.error(f"Error fetching calendar events for user {user_id}: {e}")
            return []

    @staticmethod
    async def get_user_notes(
        db: Session,
        user_id: int,
        user_subscription_status: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get user's recent notes for AI context.
        
        Args:
            db: Database session
            user_id: ID of the user
            user_subscription_status: User's subscription status for access control
            limit: Maximum number of notes to retrieve
            
        Returns:
            List of formatted notes
        """
        try:
            # Check if user can access notes feature
            user_tier = get_tier_from_subscription_status(user_subscription_status)
            if not can_access_feature(user_tier, "notes"):
                logger.info(f"User {user_id} cannot access notes feature")
                return []
            
            # Get recent notes (non-archived, sorted by updated_at)
            notes_result = await NoteService.get_notes(
                db=db,
                user_id=user_id,
                skip=0,
                limit=limit,
                sort_by="updated_at",
                sort_order="desc",
                show_archived=False
            )
            
            # Format notes for AI context
            formatted_notes = []
            for note in notes_result["notes"]:
                formatted_note = {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content or "",
                    "is_pinned": note.is_pinned,
                    "created_at": note.created_at.isoformat() if note.created_at else "",
                    "updated_at": note.updated_at.isoformat() if note.updated_at else ""
                }
                formatted_notes.append(formatted_note)
            
            logger.info(f"Retrieved {len(formatted_notes)} notes for user {user_id}")
            return formatted_notes
            
        except Exception as e:
            logger.error(f"Error fetching notes for user {user_id}: {e}")
            return []

    @staticmethod
    def format_context_for_ai(
        calendar_events: List[Dict[str, Any]],
        notes: List[Dict[str, Any]],
        training_context: str = ""
    ) -> str:
        """
        Format calendar events, notes, and training data into a context string for AI.
        
        Args:
            calendar_events: List of calendar events
            notes: List of notes
            training_context: Formatted training context string
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add calendar events context
        if calendar_events:
            context_parts.append("=== USER'S CALENDAR EVENTS ===")
            context_parts.append("Recent and upcoming calendar events:")
            
            for event in calendar_events:
                event_info = f"• {event.get('title', 'Untitled Event')}"
                if event.get('start'):
                    try:
                        start_dt = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                        event_info += f" - {start_dt.strftime('%Y-%m-%d %H:%M')}"
                    except:
                        event_info += f" - {event['start']}"
                
                if event.get('description'):
                    event_info += f" | {event['description']}"
                if event.get('location'):
                    event_info += f" | Location: {event['location']}"
                
                context_parts.append(event_info)
            
            context_parts.append("")  # Empty line for separation
        
        # Add notes context
        if notes:
            context_parts.append("=== USER'S NOTES ===")
            context_parts.append("Recent notes and important information:")
            
            for note in notes:
                note_info = f"• {note.get('title', 'Untitled Note')}"
                if note.get('is_pinned'):
                    note_info += " [PINNED]"
                
                if note.get('content'):
                    # Truncate long content for context
                    content = note['content']
                    if len(content) > 200:
                        content = content[:200] + "..."
                    note_info += f" | {content}"
                
                if note.get('updated_at'):
                    try:
                        updated_dt = datetime.fromisoformat(note['updated_at'].replace('Z', '+00:00'))
                        note_info += f" | Updated: {updated_dt.strftime('%Y-%m-%d')}"
                    except:
                        pass
                
                context_parts.append(note_info)
            
            context_parts.append("")  # Empty line for separation
        
        # Add training context if provided
        if training_context and training_context.strip():
            context_parts.append(training_context)
        
        # Add instructions for AI
        if calendar_events or notes or training_context:
            context_parts.append("=== CONTEXT USAGE INSTRUCTIONS ===")
            context_parts.append("Use the above calendar events and notes to provide more personalized and relevant responses. If training information is available, include it as supporting context.")
            context_parts.append("Reference specific events or notes when relevant to the user's questions, and incorporate training assignments or certifications when they help.")
            context_parts.append("If the user asks about their schedule, meetings, notes, training, or certifications, use this information directly.")
            context_parts.append("")
        
        return "\n".join(context_parts)

    @staticmethod
    async def get_full_user_context(
        db: Session,
        user_id: int,
        user_subscription_status: str,
        calendar_events_storage: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """
        Get complete user context including calendar events, notes, and training data.
        
        Args:
            db: Database session
            user_id: ID of the user
            user_subscription_status: User's subscription status
            calendar_events_storage: Optional in-memory calendar events storage (testing/cache)
            
        Returns:
            Formatted context string for AI
        """
        try:
            # Fetch calendar events, notes, and training data
            calendar_events = await ContextService.get_user_calendar_events(
                db=db,
                user_id=user_id,
                user_subscription_status=user_subscription_status,
                calendar_events_storage=calendar_events_storage
            )
            
            notes = await ContextService.get_user_notes(
                db=db,
                user_id=user_id,
                user_subscription_status=user_subscription_status
            )
            
            # Fetch training context with error handling
            training_context = ""
            try:
                training_context = await TrainingContextService.get_full_training_context(
                    db=db,
                    user_id=user_id,
                    user_subscription_status=user_subscription_status
                )
            except Exception as e:
                logger.warning(f"Error fetching training context for user {user_id}: {e}")
                # Continue with empty training context
            
            # Format context for AI
            context = ContextService.format_context_for_ai(calendar_events, notes, training_context)
            
            logger.info(f"Generated context for user {user_id}: {len(calendar_events)} events, {len(notes)} notes, training context included")
            return context
            
        except Exception as e:
            logger.error(f"Error generating user context for user {user_id}: {e}")
            return "" 
