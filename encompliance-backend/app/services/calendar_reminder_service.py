"""
Description: Calendar reminder service for handling scheduled notifications.
Purpose: Provides background task functionality for sending calendar reminders using database persistence.
Educational Note: Implements scheduled task system for time-based notifications with SQLAlchemy ORM.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.calendar_event import CalendarEvent as CalendarEventModel
from app.services.notification_service import NotificationService
from app.models.notification_settings import NotificationSettings

logger = logging.getLogger(__name__)

class CalendarReminderService:
    @staticmethod
    async def check_and_send_reminders():
        """Check for upcoming calendar events and send reminders using database."""
        try:
            db = next(get_db())
            current_time = datetime.now()
            
            # Get all events that need reminders or start notifications
            events_to_remind = []
            events_to_notify_start = []
            
            # Query all calendar events from database
            all_events = db.query(CalendarEventModel).all()
            
            for event in all_events:
                # Parse event start time
                try:
                    event_start = datetime.fromisoformat(event.start.replace('Z', '+00:00'))
                    if event_start.tzinfo:
                        event_start = event_start.replace(tzinfo=None)
                except:
                    continue
                
                # Get user's reminder offset (default 15 minutes)
                user_id = event.user_id
                if not user_id:
                    continue
                    
                settings = await NotificationService.get_user_notification_settings(db, user_id)
                reminder_offset = settings.calendar_reminder_offset_minutes if settings else 15
                
                # Check if pre-event reminder should be sent
                if not event.reminder_sent:
                    reminder_time = event_start - timedelta(minutes=reminder_offset)
                    if current_time >= reminder_time and current_time < event_start:
                        events_to_remind.append(event)
                
                # Check if event start notification should be sent
                if not event.start_notification_sent:
                    # Send notification within 2 minutes of event start
                    if abs((current_time - event_start).total_seconds()) <= 120:
                        events_to_notify_start.append(event)
            
            # Send pre-event reminders
            for event in events_to_remind:
                await NotificationService.create_calendar_notification(
                    db=db,
                    user_id=event.user_id,
                    event_id=event.id,
                    action="reminder",
                    event_title=event.title
                )
                
                # Mark reminder as sent in database
                event.reminder_sent = True
                db.commit()
                logger.info(f"Sent reminder for event {event.id}: {event.title}")
            
            # Send event start notifications
            for event in events_to_notify_start:
                await NotificationService.create_calendar_notification(
                    db=db,
                    user_id=event.user_id,
                    event_id=event.id,
                    action="started",
                    event_title=event.title
                )
                
                # Mark start notification as sent in database
                event.start_notification_sent = True
                db.commit()
                logger.info(f"Sent start notification for event {event.id}: {event.title}")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error checking calendar reminders: {e}")

    @staticmethod
    async def start_reminder_scheduler():
        """Start the background task for checking reminders."""
        logger.info("Starting calendar reminder scheduler")
        
        while True:
            try:
                await CalendarReminderService.check_and_send_reminders()
                # Check every 5 minutes
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Error in reminder scheduler: {e}")
                # Wait 1 minute before retrying on error
                await asyncio.sleep(60) 