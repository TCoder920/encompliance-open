"""
Access Control Utility Tests
----------------------------
Tests for access control utilities
"""

import pytest

from app.utils.access_control import can_access_feature


class TestCanAccessFeature:
    """Test feature access control"""
    
    def test_free_user_calendar_access(self):
        """Test free user calendar access"""
        assert can_access_feature("free", "calendar") == False
    
    def test_pro_user_calendar_access(self):
        """Test pro user calendar access"""
        assert can_access_feature("pro", "calendar") == True
    
    def test_enterprise_user_calendar_access(self):
        """Test enterprise user calendar access"""
        assert can_access_feature("enterprise", "calendar") == True
    
    def test_free_user_training_access(self):
        """Test free user training access"""
        assert can_access_feature("free", "training_certification") == False
    
    def test_pro_user_training_access(self):
        """Test pro user training access"""
        assert can_access_feature("pro", "training_certification") == True
    
    def test_unknown_feature(self):
        """Test access to unknown feature"""
        # Should default to False for unknown features
        assert can_access_feature("pro", "unknown_feature") == False
