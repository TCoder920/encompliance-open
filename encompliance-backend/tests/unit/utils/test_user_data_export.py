"""
User Data Export Utils Unit Tests
---------------------------------
Tests for user data export utility functions
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from app.utils.user_data_export import serialize_value, export_deleted_user_data
from app.models.user import User
import enum


class TestSerializeValue:
    """Test value serialization"""
    
    def test_serialize_enum(self):
        """Test serializing enum values"""
        class TestEnum(enum.Enum):
            VALUE1 = "value1"
            VALUE2 = "value2"
        
        result = serialize_value(TestEnum.VALUE1)
        assert result == "value1"
    
    def test_serialize_datetime(self):
        """Test serializing datetime values"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = serialize_value(dt)
        assert isinstance(result, str)
        assert "2024-01-01" in result
    
    def test_serialize_string(self):
        """Test serializing string values"""
        result = serialize_value("test_string")
        assert result == "test_string"
    
    def test_serialize_int(self):
        """Test serializing integer values"""
        result = serialize_value(123)
        assert result == 123


class TestExportDeletedUserData:
    """Test user data export"""
    
    @patch('app.utils.user_data_export.get_settings')
    @patch('app.utils.user_data_export.Path.mkdir')
    def test_export_deleted_user_data_success(self, mock_mkdir, mock_settings, db: Session):
        """Test successful user data export"""
        mock_settings.return_value.USER_DATA_EXPORT_PATH = "/tmp/exports"
        
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            subscription_status="pro"
        )
        db.add(user)
        db.commit()
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = export_deleted_user_data(user, db)
            
            assert result is not None
            assert isinstance(result, str)

