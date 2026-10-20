# Calendar Events and Notes Context Integration

## Overview

This document describes the implementation of calendar events and notes integration into the AI assistant context, enabling users to ask questions about their personal schedule and notes directly in the chat interface.

## Implementation Summary

### ✅ What Was Implemented

1. **Context Service** (`app/services/context_service.py`)
   - Fetches user calendar events and notes
   - Formats data for AI consumption
   - Respects subscription tier access controls
   - Handles errors gracefully

2. **Enhanced Chat Utils** (`app/core/chat_utils.py`)
   - Updated `get_compliance_system_message()` to accept user context
   - Integrates personal context into system instructions

3. **Enhanced LLM Service** (`app/services/llm_service.py`)
   - Fetches user context before generating responses
   - Includes calendar events and notes in AI assistant context
   - Maintains backward compatibility

4. **Comprehensive Testing** (`tests/unit/services/test_context_service.py`)
   - Unit tests for all context service functionality
   - Validates subscription tier access controls
   - Tests context formatting and integration

## Features

### Calendar Events Integration
- **Access Control**: Only Pro and Enterprise users can access calendar features
- **Time Range**: Includes events from 7 days ago to 30 days in the future
- **Data Included**: Title, start/end times, description, location, all-day status
- **User Isolation**: Only shows events belonging to the current user

### Notes Integration
- **Access Control**: Only Pro and Enterprise users can access notes features
- **Recent Notes**: Fetches up to 20 most recently updated notes
- **Data Included**: Title, content (truncated if long), pinned status, timestamps
- **Archived Filter**: Excludes archived notes from context

### AI Context Format
```
=== USER'S CALENDAR EVENTS ===
Recent and upcoming calendar events:
• Compliance Review Meeting - 2025-05-29 21:05 | Monthly compliance review with legal team | Location: Conference Room A
• Safety Inspection - 2025-05-31 21:05 | Annual safety inspection by state regulators | Location: Main Facility

=== USER'S NOTES ===
Recent notes and important information:
• Important Compliance Reminder [PINNED] | Remember to update the safety protocols document before the next inspection. | Updated: 2025-05-27
• Staff Training Notes | New staff members need additional training on emergency procedures. Schedule training session for next week. | Updated: 2025-05-25

=== CONTEXT USAGE INSTRUCTIONS ===
Use the above calendar events and notes to provide more personalized and relevant responses.
Reference specific events or notes when relevant to the user's questions.
If the user asks about their schedule, meetings, or notes, use this information directly.
```

## Technical Architecture

### Context Service (`ContextService`)

#### Key Methods:
- `get_user_calendar_events()`: Fetches and filters calendar events
- `get_user_notes()`: Fetches and formats user notes
- `format_context_for_ai()`: Formats data for AI consumption
- `get_full_user_context()`: Orchestrates full context gathering

#### Access Control:
```python
# Check subscription tier before accessing features
user_tier = get_tier_from_subscription_status(user_subscription_status)
if not can_access_feature(user_tier, "calendar"):
    return []  # No access for free users
```

### LLM Service Integration

#### Context Gathering:
```python
# Fetch user context (calendar events and notes)
user_context = await ContextService.get_full_user_context(
    db=db,
    user_id=current_user_id,
    user_subscription_status=user.subscription_status,
    calendar_events_storage=calendar_events
)
```

#### System Message Enhancement:
```python
# Include user context in system message
system_message = get_compliance_system_message(operation_type, user_context)
```

## Usage Examples

### User Queries That Now Work:
1. **"What meetings do I have this week?"**
   - AI can reference calendar events directly
   - Provides specific dates, times, and locations

2. **"Remind me about my compliance notes"**
   - AI can reference pinned and recent notes
   - Highlights important reminders

3. **"When is my next safety inspection?"**
   - AI can find specific events by type/title
   - Provides preparation reminders based on notes

4. **"What did I note about staff training?"**
   - AI can search through note content
   - Provides relevant information from notes

## Error Handling

### Graceful Degradation:
- If context fetching fails, AI continues without personal context
- Subscription tier restrictions are enforced at the service level
- Invalid calendar event dates are skipped with warnings
- Database errors don't break the chat functionality

### Logging:
```python
logger.info(f"Retrieved user context for user {user_id}: {len(calendar_events)} events, {len(notes)} notes")
logger.warning(f"Error parsing event {event_id}: {e}")
logger.error(f"Error fetching user context for user {user_id}: {e}")
```

## Performance Considerations

### Optimization Strategies:
1. **Limited Data Scope**: Only recent/upcoming events and notes
2. **Content Truncation**: Long note content is truncated to 200 characters
3. **Subscription Filtering**: Early return for users without access
4. **Error Isolation**: Context failures don't impact core chat functionality

### Memory Usage:
- Calendar events: In-memory storage (production should use database)
- Notes: Database queries with LIMIT clauses
- Context string: Formatted efficiently for AI consumption

## Security & Privacy

### Data Protection:
- User isolation: Only shows data belonging to the authenticated user
- Subscription enforcement: Access control at multiple levels
- No data leakage: Failed context fetching doesn't expose other users' data

### Access Control Matrix:
| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Calendar Events | ❌ | ✅ | ✅ |
| Notes | ❌ | ✅ | ✅ |
| AI Context | ❌ | ✅ | ✅ |

## Testing

### Test Coverage:
- ✅ Pro user calendar access
- ✅ Free user calendar restriction
- ✅ Pro user notes access
- ✅ Free user notes restriction
- ✅ Context formatting
- ✅ Empty context handling
- ✅ Full context integration

### Test Command:
```bash
python -m pytest tests/unit/services/test_context_service.py -v
```

## Future Enhancements

### Potential Improvements:
1. **Database Storage**: Move calendar events from in-memory to database
2. **Caching**: Cache user context for short periods to improve performance
3. **Smart Filtering**: AI-driven relevance filtering of context data
4. **Context Summarization**: Summarize large amounts of context data
5. **Real-time Updates**: WebSocket integration for live context updates

## Deployment Notes

### Requirements:
- No additional dependencies required
- Backward compatible with existing chat functionality
- Works with current subscription tier system
- Integrates with existing calendar and notes APIs

### Configuration:
- No additional configuration required
- Uses existing subscription tier settings
- Leverages current access control system

## Conclusion

The calendar events and notes context integration successfully enables personalized AI responses based on user's personal data. The implementation:

- ✅ Respects subscription tiers and access controls
- ✅ Provides comprehensive context to the AI assistant
- ✅ Maintains system performance and security
- ✅ Includes thorough testing and error handling
- ✅ Enables natural language queries about personal data

Users can now ask questions about their schedule and notes directly in the chat interface, receiving personalized and contextually relevant responses from the AI assistant. 