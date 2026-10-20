"""
Description: Apple Calendar integration service for the EnCompliance application.
Purpose: Handles CalDAV authentication, event import/export, and bidirectional synchronization
with Apple Calendar (iCloud). Implements iCal format conversion and secure credential management.
Educational Note: Uses CalDAV protocol with iCal format for Apple Calendar integration.
Reference: CalDAV RFC 4791 - https://tools.ietf.org/html/rfc4791
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import caldav
from icalendar import Calendar, Event as ICalEvent
from urllib.parse import urlparse

from app.core.config import get_settings
from app.models.calendar_event import CalendarEvent
from app.models import CalendarConnection
from app.database import get_db

logger = logging.getLogger(__name__)
settings = get_settings()

class AppleCalendarService:
    """Service for Apple Calendar (CalDAV) integration."""
    
    @staticmethod
    async def create_connection(
        db: Session,
        user_id: int,
        username: str,
        password: str,
        server_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create CalDAV connection to Apple Calendar."""
        try:
            if not server_url:
                server_url = settings.CALDAV_DEFAULT_SERVER
            
            # Create CalDAV client
            client = caldav.DAVClient(
                url=server_url,
                username=username,
                password=password
            )
            
            # Test connection and get principal
            principal = client.principal()
            calendars = principal.calendars()
            
            if not calendars:
                return {
                    "success": False,
                    "error": "No calendars found or invalid credentials"
                }
            
            connections_created = []
            
            for calendar in calendars:
                # Get calendar properties
                calendar_props = calendar.get_properties([
                    caldav.dav.DisplayName(),
                    caldav.dav.ResourceType()
                ])
                
                calendar_name = str(calendar_props.get(caldav.dav.DisplayName(), 'Unknown Calendar'))
                
                # Create calendar connection
                connection = CalendarConnection(
                    user_id=user_id,
                    provider='apple',
                    calendar_id=calendar.url,
                    calendar_name=calendar_name,
                    access_token=username,  # Store username as access token
                    refresh_token=password,  # Store password as refresh token (encrypted)
                    is_active=True,
                    sync_enabled=True
                )
                
                db.add(connection)
                connections_created.append(connection.to_dict())
            
            db.commit()
            
            return {
                "success": True,
                "connections": connections_created,
                "message": f"Successfully connected {len(connections_created)} Apple calendars"
            }
            
        except Exception as e:
            logger.error(f"Error creating Apple Calendar connection: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _get_caldav_client(connection: CalendarConnection) -> Optional[caldav.Calendar]:
        """Get CalDAV client for the connection."""
        try:
            # Parse server URL from calendar_id if it's a full URL
            parsed_url = urlparse(connection.calendar_id)
            if parsed_url.scheme:
                server_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                calendar_path = parsed_url.path
            else:
                server_url = settings.CALDAV_DEFAULT_SERVER
                calendar_path = connection.calendar_id
            
            client = caldav.DAVClient(
                url=server_url,
                username=connection.access_token,
                password=connection.refresh_token
            )
            
            # Get the specific calendar
            calendar = client.calendar(url=connection.calendar_id)
            return calendar
            
        except Exception as e:
            logger.error(f"Error creating CalDAV client: {e}")
            return None
    
    @staticmethod
    def _convert_to_ical_event(calendar_event: CalendarEvent) -> ICalEvent:
        """Convert CalendarEvent to iCal Event."""
        event = ICalEvent()
        event.add('uid', calendar_event.external_calendar_id or str(uuid.uuid4()))
        event.add('summary', calendar_event.title)
        event.add('description', calendar_event.description or '')
        event.add('location', calendar_event.location or '')
        
        if calendar_event.all_day:
            start_date = datetime.fromisoformat(calendar_event.start[:10]).date()
            end_date = datetime.fromisoformat(calendar_event.end[:10]).date()
            event.add('dtstart', start_date)
            event.add('dtend', end_date)
        else:
            start_datetime = datetime.fromisoformat(calendar_event.start.replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(calendar_event.end.replace('Z', '+00:00'))
            event.add('dtstart', start_datetime)
            event.add('dtend', end_datetime)
        
        event.add('dtstamp', datetime.now())
        event.add('created', calendar_event.created_at or datetime.now())
        event.add('last-modified', calendar_event.updated_at or datetime.now())
        
        return event
    
    @staticmethod
    def _convert_from_ical_event(ical_event: ICalEvent, user_id: int) -> CalendarEvent:
        """Convert iCal Event to CalendarEvent."""
        # Extract event data
        uid = str(ical_event.get('uid', ''))
        summary = str(ical_event.get('summary', 'Untitled Event'))
        description = str(ical_event.get('description', ''))
        location = str(ical_event.get('location', ''))
        
        dtstart = ical_event.get('dtstart')
        dtend = ical_event.get('dtend')
        
        # Handle date/datetime conversion
        if hasattr(dtstart.dt, 'date'):  # All-day event
            start = dtstart.dt.isoformat()
            end = dtend.dt.isoformat()
            all_day = True
        else:  # Timed event
            start = dtstart.dt.isoformat()
            end = dtend.dt.isoformat()
            all_day = False
        
        return CalendarEvent(
            user_id=user_id,
            title=summary,
            start=start,
            end=end,
            description=description,
            location=location,
            all_day=all_day,
            external_calendar_id=uid,
            external_calendar_provider='apple',
            sync_status='synced',
            last_synced_at=datetime.now()
        )
    
    @staticmethod
    async def import_events(
        db: Session,
        connection: CalendarConnection,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Import events from Apple Calendar via CalDAV."""
        try:
            calendar = AppleCalendarService._get_caldav_client(connection)
            if not calendar:
                return {"success": False, "error": "Failed to connect to Apple Calendar"}
            
            # Set default date range if not provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now() + timedelta(days=365)
            
            # Fetch events from Apple Calendar
            events = calendar.date_search(start=start_date, end=end_date)
            imported_count = 0
            
            for event in events:
                try:
                    # Parse iCal data
                    ical_data = Calendar.from_ical(event.data)
                    
                    for component in ical_data.walk():
                        if component.name == "VEVENT":
                            uid = str(component.get('uid', ''))
                            
                            # Check if event already exists
                            existing_event = db.query(CalendarEvent).filter(
                                CalendarEvent.user_id == connection.user_id,
                                CalendarEvent.external_calendar_id == uid,
                                CalendarEvent.external_calendar_provider == 'apple'
                            ).first()
                            
                            if existing_event:
                                continue  # Skip existing events
                            
                            # Convert and save event
                            calendar_event = AppleCalendarService._convert_from_ical_event(
                                component, connection.user_id
                            )
                            
                            db.add(calendar_event)
                            imported_count += 1
                            
                except Exception as e:
                    logger.warning(f"Error parsing Apple Calendar event: {e}")
                    continue
            
            db.commit()
            
            return {
                "success": True,
                "imported_count": imported_count,
                "message": f"Successfully imported {imported_count} events from Apple Calendar"
            }
            
        except Exception as e:
            logger.error(f"Error importing Apple Calendar events: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def export_event(
        db: Session,
        connection: CalendarConnection,
        calendar_event: CalendarEvent
    ) -> Dict[str, Any]:
        """Export a single event to Apple Calendar via CalDAV."""
        try:
            calendar = AppleCalendarService._get_caldav_client(connection)
            if not calendar:
                return {"success": False, "error": "Failed to connect to Apple Calendar"}
            
            # Convert to iCal format
            ical_event = AppleCalendarService._convert_to_ical_event(calendar_event)
            
            # Create iCal calendar container
            ical_calendar = Calendar()
            ical_calendar.add('prodid', '-//EnCompliance//Calendar//EN')
            ical_calendar.add('version', '2.0')
            ical_calendar.add_component(ical_event)
            
            # Save to Apple Calendar
            event_uid = str(ical_event.get('uid'))
            calendar.save_event(ical_calendar.to_ical().decode('utf-8'))
            
            # Update local event
            calendar_event.external_calendar_id = event_uid
            calendar_event.external_calendar_provider = 'apple'
            calendar_event.sync_status = 'synced'
            calendar_event.last_synced_at = datetime.now()
            
            db.commit()
            
            return {
                "success": True,
                "apple_event_id": event_uid,
                "message": "Event successfully exported to Apple Calendar"
            }
            
        except Exception as e:
            logger.error(f"Error exporting event to Apple Calendar: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def sync_events(
        db: Session,
        connection: CalendarConnection
    ) -> Dict[str, Any]:
        """Bidirectional sync between local and Apple Calendar events."""
        try:
            # First import new/updated events from Apple Calendar
            import_result = await AppleCalendarService.import_events(db, connection)
            
            if not import_result["success"]:
                return import_result
            
            # Then export local events that aren't synced
            local_events = db.query(CalendarEvent).filter(
                CalendarEvent.user_id == connection.user_id,
                CalendarEvent.external_calendar_provider.is_(None),
                CalendarEvent.sync_status == 'local'
            ).all()
            
            exported_count = 0
            for event in local_events:
                export_result = await AppleCalendarService.export_event(db, connection, event)
                if export_result["success"]:
                    exported_count += 1
            
            return {
                "success": True,
                "imported_count": import_result["imported_count"],
                "exported_count": exported_count,
                "message": f"Sync completed: {import_result['imported_count']} imported, {exported_count} exported"
            }
            
        except Exception as e:
            logger.error(f"Error syncing Apple Calendar events: {e}")
            return {"success": False, "error": str(e)} 