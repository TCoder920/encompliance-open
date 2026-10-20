# Calendar Integration Setup Guide

This guide explains how to set up Google Calendar and Apple Calendar integration for the EnCompliance application.

## Features

- **Google Calendar Integration**: OAuth-based connection to sync events bidirectionally
- **Apple Calendar Integration**: CalDAV-based connection for iCloud calendars
- **Event Import/Export**: Import existing events and export new ones
- **Bidirectional Sync**: Keep calendars in sync between EnCompliance and external calendars
- **Access Control**: Feature restricted to Pro and Enterprise subscription tiers

## Google Calendar Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

### 2. Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure the OAuth consent screen if prompted
4. Choose "Web application" as the application type
5. Add authorized redirect URIs:
   - `http://localhost:5174/auth/google/callback` (development)
   - `https://yourdomain.com/auth/google/callback` (production)
6. Save the Client ID and Client Secret

### 3. Environment Configuration

Add the following variables to your `.env` file:

```env
# Google Calendar Integration
GOOGLE_CALENDAR_CLIENT_ID=your_google_client_id_here
GOOGLE_CALENDAR_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:5174/auth/google/callback
```

## Apple Calendar Setup

Apple Calendar integration uses CalDAV protocol and requires app-specific passwords.

### 1. Generate App-Specific Password

1. Sign in to [appleid.apple.com](https://appleid.apple.com/)
2. Go to "Security" section
3. Under "App-Specific Passwords", click "Generate Password"
4. Enter a label (e.g., "EnCompliance Calendar")
5. Save the generated password

### 2. Environment Configuration

Add the following variable to your `.env` file:

```env
# Apple Calendar Integration
CALDAV_DEFAULT_SERVER=https://caldav.icloud.com
```

## Database Migration

Run the database migration to add calendar integration tables:

```bash
cd encompliance-backend
alembic upgrade head
```

## API Endpoints

### Google Calendar

- `GET /api/calendar/integration/google/auth` - Get OAuth authorization URL
- `POST /api/calendar/integration/google/callback` - Handle OAuth callback
- `GET /api/calendar/integration/connections` - List calendar connections
- `POST /api/calendar/integration/import/google` - Import events from Google Calendar
- `POST /api/calendar/integration/sync/google` - Bidirectional sync with Google Calendar

### Apple Calendar

- `POST /api/calendar/integration/apple/connect` - Connect to Apple Calendar via CalDAV
- `POST /api/calendar/integration/import/apple` - Import events from Apple Calendar
- `POST /api/calendar/integration/sync/apple` - Bidirectional sync with Apple Calendar

### General

- `DELETE /api/calendar/integration/connections/{id}` - Disconnect calendar
- `GET /api/calendar/integration/sync/status` - Get sync status for all connections

## Frontend Usage

### Calendar Settings Page

Users can access calendar integration through the Calendar Settings page at `/calendar-settings`.

Features include:
- Connect Google Calendar (OAuth flow)
- Connect Apple Calendar (CalDAV credentials)
- View connected calendars
- Import events from external calendars
- Sync events bidirectionally
- Disconnect calendars

### Calendar Component

The main calendar component includes:
- "Calendar Settings" button to access integration features
- Display of events from all connected calendars
- Sync status indicators

## Security Considerations

1. **OAuth Tokens**: Google OAuth tokens are stored securely and refreshed automatically
2. **CalDAV Credentials**: Apple Calendar credentials should be encrypted in production
3. **Access Control**: Calendar integration is restricted to Pro/Enterprise tiers
4. **Rate Limiting**: Implement rate limiting for external API calls
5. **Error Handling**: Graceful handling of API failures and token expiration

## Troubleshooting

### Google Calendar Issues

- **Invalid credentials**: Check Client ID and Secret in environment variables
- **Redirect URI mismatch**: Ensure redirect URI matches Google Cloud Console configuration
- **Token expired**: Tokens are automatically refreshed; check refresh token validity

### Apple Calendar Issues

- **Authentication failed**: Verify Apple ID and app-specific password
- **No calendars found**: Check CalDAV server URL and credentials
- **Connection timeout**: Verify network connectivity to iCloud servers

### General Issues

- **Feature not available**: Ensure user has Pro or Enterprise subscription
- **Database errors**: Run database migrations and check table structure
- **Import failures**: Check external calendar permissions and API limits

## Development Notes

### Backend Services

- `GoogleCalendarService`: Handles OAuth flow and Google Calendar API interactions
- `AppleCalendarService`: Manages CalDAV connections and iCal format conversion
- `CalendarConnection` model: Stores external calendar connection details
- `CalendarEvent` model: Enhanced with external calendar sync fields

### Frontend Components

- `CalendarSettings`: Main interface for managing calendar connections
- `Calendar`: Enhanced calendar component with integration features
- Access control utilities for subscription tier checking

### Database Schema

New tables and fields:
- `calendar_connections`: Stores external calendar connection details
- `calendar_events.external_calendar_id`: Links to external calendar events
- `calendar_events.external_calendar_provider`: Identifies the external provider
- `calendar_events.sync_status`: Tracks synchronization status
- `calendar_events.last_synced_at`: Timestamp of last sync

## Future Enhancements

1. **Outlook Calendar**: Add Microsoft Outlook/Office 365 integration
2. **Automatic Sync**: Background synchronization on a schedule
3. **Conflict Resolution**: Handle conflicting events between calendars
4. **Calendar Selection**: Allow users to choose which calendars to sync
5. **Event Filtering**: Filter events by type, category, or keywords
6. **Webhook Support**: Real-time updates via webhooks where supported 