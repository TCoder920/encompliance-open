"""
Subscription Downgrade Service Unit Tests
-----------------------------------------
Tests for subscription downgrade and grace period management
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.services.subscription_downgrade_service import SubscriptionDowngradeService
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User


class TestSubscriptionDowngradeService:
    """Test SubscriptionDowngradeService methods"""
    
    def test_initiate_grace_period_success(self, db: Session):
        """Test successful grace period initiation"""
        subscription = Subscription(
            id=1,
            facility_id=1,
            stripe_subscription_id="sub_test123",
            status=SubscriptionStatus.ACTIVE
        )
        db.add(subscription)
        db.commit()
        
        result = SubscriptionDowngradeService.initiate_grace_period(subscription, db)
        
        assert result == True
        db.refresh(subscription)
        assert subscription.status == SubscriptionStatus.GRACE_PERIOD
    
    def test_immediate_downgrade_success(self, db: Session):
        """Test successful immediate downgrade"""
        subscription = Subscription(
            id=1,
            facility_id=1,
            stripe_subscription_id="sub_test123",
            status=SubscriptionStatus.ACTIVE
        )
        db.add(subscription)
        db.commit()
        
        result = SubscriptionDowngradeService.immediate_downgrade(subscription, db, "Test reason")
        
        assert result == True
        db.refresh(subscription)
        assert subscription.status == SubscriptionStatus.CANCELLED
    
    @patch('app.services.subscription_downgrade_service.datetime')
    def test_process_expired_grace_periods_success(self, mock_datetime, db: Session):
        """Test processing expired grace periods"""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 10)
        
        subscription = Subscription(
            id=1,
            facility_id=1,
            stripe_subscription_id="sub_test123",
            status=SubscriptionStatus.GRACE_PERIOD,
            grace_period_ends_at=datetime(2024, 1, 1)  # Expired
        )
        db.add(subscription)
        db.commit()
        
        result = SubscriptionDowngradeService.process_expired_grace_periods(db)
        
        assert "processed" in result
        assert result["processed"] >= 0
    
    def test_check_subscription_status_active(self, db: Session):
        """Test checking active subscription status"""
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            subscription_status="pro"
        )
        db.add(user)
        
        subscription = Subscription(
            id=1,
            facility_id=1,
            stripe_subscription_id="sub_test123",
            status=SubscriptionStatus.ACTIVE
        )
        db.add(subscription)
        db.commit()
        
        result = SubscriptionDowngradeService.check_subscription_status(user, db)
        
        assert "status" in result
        assert result["status"] == "active"

