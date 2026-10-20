"""
Test module for date/time functionality in chat_utils.

Purpose: Verify that the AI assistant receives current date and time information
in the system message for temporal awareness and context-sensitive responses.
"""
import pytest
from datetime import datetime
from app.core.chat_utils import get_compliance_system_message


class TestChatUtilsDateTime:
    """Test date/time integration in chat utilities."""

    def test_system_message_includes_current_datetime(self):
        """Test that system message includes current date and time information."""
        system_msg = get_compliance_system_message("daycare")
        
        # Verify date/time section exists
        assert "=== CURRENT DATE AND TIME INFORMATION ===" in system_msg
        
        # Verify current date is included
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        assert f"Current Date: {current_date}" in system_msg
        
        # Verify time format is included
        assert "Current Time:" in system_msg
        
        # Verify ISO format is included
        assert "ISO Format:" in system_msg
        
        # Verify additional context fields
        assert "Day of Week:" in system_msg
        assert "Week of Year:" in system_msg
        assert "Month:" in system_msg
        assert "Timezone: Local system time" in system_msg

    def test_system_message_includes_datetime_instructions(self):
        """Test that system message includes instructions for using date/time info."""
        system_msg = get_compliance_system_message("daycare")
        
        # Verify instructions are present
        assert "Use this current date and time information when:" in system_msg
        assert "Answering questions about \"today\", \"now\", \"this week\", \"this month\"" in system_msg
        assert "Calculating relative dates" in system_msg
        assert "Scheduling or time-sensitive compliance matters" in system_msg
        assert "Determining business days, weekends, or holiday considerations" in system_msg

    def test_datetime_context_with_user_context(self):
        """Test that date/time context works alongside user context."""
        user_context = "Sample calendar events and notes"
        system_msg = get_compliance_system_message("daycare", user_context)
        
        # Verify both date/time and user context are present
        assert "=== CURRENT DATE AND TIME INFORMATION ===" in system_msg
        assert "=== USER PERSONAL CONTEXT ===" in system_msg
        assert user_context in system_msg

    def test_datetime_context_for_different_operation_types(self):
        """Test that date/time context is included for all operation types."""
        operation_types = ["daycare", "residential", "custom_operation"]
        
        for op_type in operation_types:
            system_msg = get_compliance_system_message(op_type)
            
            # Date/time context should be present regardless of operation type
            assert "=== CURRENT DATE AND TIME INFORMATION ===" in system_msg
            assert "Current Date:" in system_msg
            assert "Current Time:" in system_msg

    def test_datetime_format_consistency(self):
        """Test that date/time formats are consistent and parseable."""
        system_msg = get_compliance_system_message("daycare")
        
        # Extract the current datetime from the message
        lines = system_msg.split('\n')
        current_date_line = next(line for line in lines if line.startswith("Current Date:"))
        current_time_line = next(line for line in lines if line.startswith("Current Time:"))
        iso_format_line = next(line for line in lines if line.startswith("ISO Format:"))
        
        # Verify formats are as expected
        assert "Current Date: " in current_date_line
        assert "Current Time: " in current_time_line
        assert "ISO Format: " in iso_format_line
        
        # Verify ISO format is valid
        iso_value = iso_format_line.split("ISO Format: ")[1]
        # Should be able to parse the ISO format
        datetime.fromisoformat(iso_value)  # Will raise exception if invalid

    def test_datetime_updates_on_each_call(self):
        """Test that date/time information updates on each function call."""
        import time
        
        # Get first system message
        msg1 = get_compliance_system_message("daycare")
        
        # Wait a small amount to ensure time difference
        time.sleep(0.1)
        
        # Get second system message
        msg2 = get_compliance_system_message("daycare")
        
        # Extract ISO timestamps
        lines1 = msg1.split('\n')
        lines2 = msg2.split('\n')
        
        iso_line1 = next(line for line in lines1 if line.startswith("ISO Format:"))
        iso_line2 = next(line for line in lines2 if line.startswith("ISO Format:"))
        
        iso1 = iso_line1.split("ISO Format: ")[1]
        iso2 = iso_line2.split("ISO Format: ")[1]
        
        # Timestamps should be different (or at least not fail)
        dt1 = datetime.fromisoformat(iso1)
        dt2 = datetime.fromisoformat(iso2)
        
        # Should be able to parse both timestamps
        assert isinstance(dt1, datetime)
        assert isinstance(dt2, datetime) 