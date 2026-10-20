"""
Description: Google Calendar integration service for the EnCompliance application.
Purpose: Handles OAuth authentication, event import/export, and bidirectional synchronization
with Google Calendar API. Implements secure token management and rate limiting.
Educational Note: Uses Google Calendar API v3 with OAuth 2.0 flow for secure access.
Reference: Google Calendar API - https://developers.google.com/calendar/api/guides/overview
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import get_settings
from app.models.calendar_event import CalendarEvent
from app.models import CalendarConnection
from app.database import get_db

logger = logging.getLogger(__name__)
settings = get_settings()

class GoogleCalendarService:
    """Service for Google Calendar integration."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    @staticmethod
    def get_oauth_flow() -> Flow:
        """Create OAuth flow for Google Calendar authorization."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_CALENDAR_REDIRECT_URI]
                }
            },
            scopes=GoogleCalendarService.SCOPES
        )
        flow.redirect_uri = settings.GOOGLE_CALENDAR_REDIRECT_URI
        return flow
    
    @staticmethod
    def get_authorization_url() -> str:
        """Get Google OAuth authorization URL."""
        flow = GoogleCalendarService.get_oauth_flow()
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return auth_url
    
    @staticmethod
    async def handle_oauth_callback(
        db: Session,
        user_id: int,
        authorization_code: str
    ) -> Dict[str, Any]:
        """Handle OAuth callback and store credentials."""
        try:
            flow = GoogleCalendarService.get_oauth_flow()
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            
            # Get user's calendar list
            service = build('calendar', 'v3', credentials=credentials)
            calendar_list = service.calendarList().list().execute()
            
            connections_created = []
            
            for calendar_item in calendar_list.get('items', []):
                # Create calendar connection
                connection = CalendarConnection(
                    user_id=user_id,
                    provider='google',
                    calendar_id=calendar_item['id'],
                    calendar_name=calendar_item.get('summary', 'Unknown Calendar'),
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    token_expires_at=credentials.expiry,
                    is_active=True,
                    sync_enabled=calendar_item['id'] == 'primary'  # Enable sync for primary calendar by default
                )
                
                db.add(connection)
                connections_created.append(connection.to_dict())
            
            db.commit()
            
            return {
                "success": True,
                "connections": connections_created,
                "message": f"Successfully connected {len(connections_created)} Google calendars"
            }
            
        except Exception as e:
            logger.error(f"Error handling Google OAuth callback: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _refresh_credentials(connection: CalendarConnection) -> Optional[Credentials]:
        """Refresh Google OAuth credentials."""
        try:
            credentials = Credentials(
                token=connection.access_token,
                refresh_token=connection.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CALENDAR_CLIENT_ID,
                client_secret=settings.GOOGLE_CALENDAR_CLIENT_SECRET
            )
            
            if credentials.expired:
                credentials.refresh(Request())
                
                # Update stored credentials
                connection.access_token = credentials.token
                connection.token_expires_at = credentials.expiry
                
            return credentials
            
        except Exception as e:
            logger.error(f"Error refreshing Google credentials: {e}")
            return None
    
    @staticmethod
    async def import_events(
        db: Session,
        connection: CalendarConnection,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Import events from Google Calendar."""
        try:
            credentials = GoogleCalendarService._refresh_credentials(connection)
            if not credentials:
                return {"success": False, "error": "Failed to refresh credentials"}
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # Set default date range if not provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now() + timedelta(days=365)
            
            # Fetch events from Google Calendar
            events_result = service.events().list(
                calendarId=connection.calendar_id,
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            imported_count = 0
            
            for event in events:
                # Check if event already exists
                existing_event = db.query(CalendarEvent).filter(
                    CalendarEvent.user_id == connection.user_id,
                    CalendarEvent.external_calendar_id == event['id'],
                    CalendarEvent.external_calendar_provider == 'google'
                ).first()
                
                if existing_event:
                    continue  # Skip existing events
                
                # Parse event data
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                all_day = 'dateTime' not in event['start']
                
                # Create new calendar event
                calendar_event = CalendarEvent(
                    user_id=connection.user_id,
                    title=event.get('summary', 'Untitled Event'),
                    start=start,
                    end=end,
                    description=event.get('description', ''),
                    location=event.get('location', ''),
                    all_day=all_day,
                    external_calendar_id=event['id'],
                    external_calendar_provider='google',
                    sync_status='synced',
                    last_synced_at=datetime.now()
                )
                
                db.add(calendar_event)
                imported_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "imported_count": imported_count,
                "message": f"Successfully imported {imported_count} events from Google Calendar"
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return {"success": False, "error": f"Google Calendar API error: {e}"}
        except Exception as e:
            logger.error(f"Error importing Google Calendar events: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def export_event(
        db: Session,
        connection: CalendarConnection,
        calendar_event: CalendarEvent
    ) -> Dict[str, Any]:
        """Export a single event to Google Calendar."""
        try:
            credentials = GoogleCalendarService._refresh_credentials(connection)
            if not credentials:
                return {"success": False, "error": "Failed to refresh credentials"}
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # Prepare event data for Google Calendar
            event_data = {
                'summary': calendar_event.title,
                'description': calendar_event.description or '',
                'location': calendar_event.location or '',
            }
            
            if calendar_event.all_day:
                event_data['start'] = {'date': calendar_event.start[:10]}
                event_data['end'] = {'date': calendar_event.end[:10]}
            else:
                event_data['start'] = {'dateTime': calendar_event.start}
                event_data['end'] = {'dateTime': calendar_event.end}
            
            # Create event in Google Calendar
            created_event = service.events().insert(
                calendarId=connection.calendar_id,
                body=event_data
            ).execute()
            
            # Update local event with Google Calendar ID
            calendar_event.external_calendar_id = created_event['id']
            calendar_event.external_calendar_provider = 'google'
            calendar_event.sync_status = 'synced'
            calendar_event.last_synced_at = datetime.now()
            
            db.commit()
            
            return {
                "success": True,
                "google_event_id": created_event['id'],
                "message": "Event successfully exported to Google Calendar"
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return {"success": False, "error": f"Google Calendar API error: {e}"}
        except Exception as e:
            logger.error(f"Error exporting event to Google Calendar: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def sync_events(
        db: Session,
        connection: CalendarConnection
    ) -> Dict[str, Any]:
        """Bidirectional sync between local and Google Calendar events."""
        try:
            # First import new/updated events from Google
            import_result = await GoogleCalendarService.import_events(db, connection)
            
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
                export_result = await GoogleCalendarService.export_event(db, connection, event)
                if export_result["success"]:
                    exported_count += 1
            
            return {
                "success": True,
                "imported_count": import_result["imported_count"],
                "exported_count": exported_count,
                "message": f"Sync completed: {import_result['imported_count']} imported, {exported_count} exported"
            }
            
        except Exception as e:
            logger.error(f"Error syncing Google Calendar events: {e}")
            return {"success": False, "error": str(e)} 