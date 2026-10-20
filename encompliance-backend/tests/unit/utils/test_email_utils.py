"""
Email Utils Unit Tests
---------------------
Tests for email utility functions
"""

import pytest
from unittest.mock import patch, MagicMock

from app.utils.email_utils import send_email


class TestEmailUtils:
    """Test email utility functions"""
    
    @patch('app.utils.email_utils.settings.SMTP_HOST', 'smtp.example.com')
    @patch('app.utils.email_utils.settings.SMTP_FROM_EMAIL', 'noreply@example.com')
    @patch('app.utils.email_utils.emails.message')
    def test_send_email_success(self, mock_message):
        """Test successful email sending"""
        mock_msg = MagicMock()
        mock_message.return_value = mock_msg
        mock_msg.send.return_value = True
        
        result = send_email(
            subject="Test Subject",
            recipient="test@example.com",
            template_name="test_template",
            context={"key": "value"}
        )
        
        assert result == True
    
    @patch('app.utils.email_utils.settings.SMTP_HOST', None)
    def test_send_email_no_smtp_config(self):
        """Test email sending when SMTP is not configured"""
        result = send_email(
            subject="Test Subject",
            recipient="test@example.com",
            template_name="test_template",
            context={"key": "value"}
        )
        
        # Should return True in development mode
        assert result == True
    
    @patch('app.utils.email_utils.settings.SMTP_HOST', 'smtp.example.com')
    @patch('app.utils.email_utils.settings.SMTP_FROM_EMAIL', 'noreply@example.com')
    @patch('app.utils.email_utils.emails.message')
    def test_send_email_with_template_override(self, mock_message):
        """Test email sending with template override"""
        mock_msg = MagicMock()
        mock_message.return_value = mock_msg
        mock_msg.send.return_value = True
        
        context = {
            "__template_override__": "<html>Custom Template</html>",
            "key": "value"
        }
        
        result = send_email(
            subject="Test Subject",
            recipient="test@example.com",
            template_name="test_template",
            context=context
        )
        
        assert result == True

