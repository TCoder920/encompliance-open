"""
Integration test for AI context with calendar events and notes.
Purpose: Demonstrates end-to-end functionality of personal context integration.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.core.chat_utils import get_compliance_system_message
from app.services.context_service import ContextService


class TestAIContextIntegration:
    """Integration tests for AI context with personal data."""

    @pytest.mark.asyncio
    async def test_full_context_integration_pro_user(self):
        """Test complete context integration for a Pro user."""
        # Mock calendar events
        mock_calendar_events = {
            "event_1": {
                "user_id": 1,
                "title": "Compliance Review Meeting",
                "start": (datetime.now() + timedelta(days=1)).isoformat(),
                "end": (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
                "description": "Monthly compliance review with legal team",
                "location": "Conference Room A",
                "allDay": False
            },
            "event_2": {
                "user_id": 1,
                "title": "Safety Inspection",
                "start": (datetime.now() + timedelta(days=3)).isoformat(),
                "end": (datetime.now() + timedelta(days=3, hours=2)).isoformat(),
                "description": "Annual safety inspection by state regulators",
                "location": "Main Facility",
                "allDay": False
            }
        }

        # Mock notes
        class MockNote:
            def __init__(self, id, title, content, is_pinned, created_at, updated_at):
                self.id = id
                self.title = title
                self.content = content
                self.is_pinned = is_pinned
                self.created_at = created_at
                self.updated_at = updated_at

        mock_notes = [
            MockNote(
                id=1,
                title="Important Compliance Reminder",
                content="Remember to update the safety protocols document before the next inspection.",
                is_pinned=True,
                created_at=datetime.now() - timedelta(days=2),
                updated_at=datetime.now() - timedelta(days=1)
            ),
            MockNote(
                id=2,
                title="Staff Training Notes",
                content="New staff members need additional training on emergency procedures. Schedule training session for next week.",
                is_pinned=False,
                created_at=datetime.now() - timedelta(days=5),
                updated_at=datetime.now() - timedelta(days=3)
            )
        ]

        # Mock database
        mock_db = Mock()

        # Test full context integration
        with patch('app.services.context_service.NoteService.get_notes') as mock_get_notes:
            mock_get_notes.return_value = {"notes": mock_notes, "total": 2}
            
            # Get full user context
            context = await ContextService.get_full_user_context(
                db=mock_db,
                user_id=1,
                user_subscription_status="pro",
                calendar_events_storage=mock_calendar_events
            )

            # Verify context contains expected data
            assert "USER'S CALENDAR EVENTS" in context
            assert "USER'S NOTES" in context
            assert "Compliance Review Meeting" in context
            assert "Safety Inspection" in context
            assert "Important Compliance Reminder" in context
            assert "Staff Training Notes" in context
            assert "[PINNED]" in context
            assert "CONTEXT USAGE INSTRUCTIONS" in context

            # Test system message integration
            system_message = get_compliance_system_message("daycare", context)
            
            # Verify system message includes context
            assert "USER PERSONAL CONTEXT" in system_message
            assert "Compliance Review Meeting" in system_message
            assert "Important Compliance Reminder" in system_message
            assert "childcare" in system_message.lower()

            # Verify system message structure
            assert len(system_message) > 1000  # Should be substantial
            assert "compliance" in system_message.lower()

    @pytest.mark.asyncio
    async def test_context_integration_free_user(self):
        """Test that free users get no personal context."""
        # Mock calendar events (should be ignored for free users)
        mock_calendar_events = {
            "event_1": {
                "user_id": 1,
                "title": "Should Not Appear",
                "start": (datetime.now() + timedelta(days=1)).isoformat(),
                "end": (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
                "description": "This should not appear in context",
                "location": "Nowhere",
                "allDay": False
            }
        }

        mock_db = Mock()

        # Test free user context (should be empty)
        context = await ContextService.get_full_user_context(
            db=mock_db,
            user_id=1,
            user_subscription_status="free",
            calendar_events_storage=mock_calendar_events
        )

        # Verify no personal context for free users
        assert context == ""

        # Test system message without context
        system_message = get_compliance_system_message("daycare", context)
        
        # Should not contain personal context
        assert "USER PERSONAL CONTEXT" not in system_message
        assert "Should Not Appear" not in system_message
        
        # But should still contain operation-specific instructions
        assert "childcare" in system_message.lower()

    def test_context_enhances_ai_responses(self):
        """Test that context enables better AI responses."""
        # Sample calendar events
        calendar_events = [
            {
                "title": "Fire Safety Drill",
                "start": "2025-06-01T10:00:00",
                "description": "Monthly fire safety drill for all staff",
                "location": "Main Building"
            }
        ]

        # Sample notes
        notes = [
            {
                "title": "Fire Safety Checklist",
                "content": "Ensure all exits are clear, check fire extinguishers, test alarm system",
                "is_pinned": True,
                "updated_at": "2025-05-28T09:00:00"
            }
        ]

        # Format context
        context = ContextService.format_context_for_ai(calendar_events, notes)

        # Create system message with context
        system_message = get_compliance_system_message("daycare", context)

        # Verify the AI now has access to:
        # 1. Upcoming fire safety drill information
        assert "Fire Safety Drill" in system_message
        assert "2025-06-01" in system_message
        
        # 2. Related safety checklist from notes
        assert "Fire Safety Checklist" in system_message
        assert "fire extinguishers" in system_message
        
        # 3. Instructions to use this information
        assert "Use the above calendar events and notes" in system_message
        assert "Reference specific events or notes when relevant" in system_message

        # This enables the AI to answer questions like:
        # - "When is my next fire drill?"
        # - "What should I check before the fire drill?"
        # - "Do I have any safety-related events coming up?"

    @pytest.mark.asyncio
    async def test_error_handling_in_context_integration(self):
        """Test that context integration handles errors gracefully."""
        # Test with invalid calendar events
        invalid_calendar_events = {
            "bad_event": {
                "user_id": 1,
                "title": "Bad Event",
                "start": "invalid-date",  # Invalid date format
                "end": "also-invalid",
                "description": "This should be skipped",
                "location": "Nowhere",
                "allDay": False
            },
            "good_event": {
                "user_id": 1,
                "title": "Good Event",
                "start": (datetime.now() + timedelta(days=1)).isoformat(),
                "end": (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
                "description": "This should work",
                "location": "Conference Room",
                "allDay": False
            }
        }

        mock_db = Mock()

        # Mock notes service to raise an exception
        with patch('app.services.context_service.NoteService.get_notes') as mock_get_notes:
            mock_get_notes.side_effect = Exception("Database error")
            
            # Should handle errors gracefully and return partial context
            context = await ContextService.get_full_user_context(
                db=mock_db,
                user_id=1,
                user_subscription_status="pro",
                calendar_events_storage=invalid_calendar_events
            )

            # Should include valid calendar events despite notes error
            assert "Good Event" in context
            assert "Bad Event" not in context  # Invalid event should be skipped
            
            # Should not include notes section due to error
            assert "USER'S NOTES" not in context

        # System message should still work with partial context
        system_message = get_compliance_system_message("daycare", context)
        assert "Good Event" in system_message
        assert len(system_message) > 500  # Should still be substantial 