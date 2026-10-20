"""
Tiers Utility Tests
-------------------
Tests for subscription tier utilities including:
- Tier detection from subscription status
- Feature access control
"""

import pytest

from app.utils.tiers import get_tier_from_subscription_status
from app.utils.access_control import can_access_feature


class TestGetTierFromSubscriptionStatus:
    """Test tier detection from subscription status"""
    
    def test_get_tier_free(self):
        """Test free tier detection"""
        tier = get_tier_from_subscription_status("free")
        assert tier == "free"
    
    def test_get_tier_pro(self):
        """Test pro tier detection"""
        tier = get_tier_from_subscription_status("pro")
        assert tier == "pro"
    
    def test_get_tier_enterprise(self):
        """Test enterprise tier detection"""
        tier = get_tier_from_subscription_status("enterprise")
        assert tier == "enterprise"
    
    def test_get_tier_none(self):
        """Test tier detection with None"""
        tier = get_tier_from_subscription_status(None)
        assert tier == "free"  # Should default to free
    
    def test_get_tier_unknown(self):
        """Test tier detection with unknown status"""
        tier = get_tier_from_subscription_status("unknown")
        assert tier == "free"  # Should default to free


class TestCanAccessFeature:
    """Test feature access control"""
    
    def test_can_access_feature_free_user(self):
        """Test feature access for free users"""
        # Free users should not access pro features
        assert can_access_feature("free", "calendar") == False
        assert can_access_feature("free", "training_certification") == False
    
    def test_can_access_feature_pro_user(self):
        """Test feature access for pro users"""
        # Pro users should access pro features
        assert can_access_feature("pro", "calendar") == True
        assert can_access_feature("pro", "training_certification") == True
    
    def test_can_access_feature_enterprise_user(self):
        """Test feature access for enterprise users"""
        # Enterprise users should access all features
        assert can_access_feature("enterprise", "calendar") == True
        assert can_access_feature("enterprise", "training_certification") == True
    
    def test_can_access_feature_basic_features(self):
        """Test access to basic features (available to all)"""
        # Basic features should be available to all tiers
        assert can_access_feature("free", "basic_feature") == True
        assert can_access_feature("pro", "basic_feature") == True

