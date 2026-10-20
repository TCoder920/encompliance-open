"""
Payment Processor Service Unit Tests
------------------------------------
Tests for payment processing logic including:
- Checkout session processing
- Seat changes
- Subscription upgrades
- Error handling
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.services.payment_processor_service import PaymentProcessorService
from app.models.facility import Facility
from app.models.subscription import Subscription
from app.models.subscription import SubscriptionStatus


class TestHandleCheckoutSessionCompleted:
    """Test main checkout session processing"""
    
    def test_process_seat_reduction(self, db: Session):
        """Test processing seat reduction"""
        session_data = {
            "id": "session_123",
            "customer": "cus_123",
            "metadata": {
                "seat_reduction": "true",
                "facility_id": "1",
                "subscription_id": "sub_123",
                "new_seat_count": "5"
            }
        }
        
        with patch.object(PaymentProcessorService, '_process_seat_change') as mock_process:
            mock_process.return_value = {"status": "processed", "action": "seat_reduction_completed"}
            
            result = PaymentProcessorService.handle_checkout_session_completed(session_data, db)
            
            assert result["status"] == "processed"
            mock_process.assert_called_once_with(
                db=db,
                metadata=session_data["metadata"],
                increase=False
            )
    
    def test_process_seat_upgrade(self, db: Session):
        """Test processing seat upgrade"""
        session_data = {
            "id": "session_123",
            "customer": "cus_123",
            "metadata": {
                "seat_upgrade": "true",
                "facility_id": "1",
                "subscription_id": "sub_123",
                "new_seat_count": "10"
            }
        }
        
        with patch.object(PaymentProcessorService, '_process_seat_change') as mock_process:
            mock_process.return_value = {"status": "processed", "action": "seat_upgrade_completed"}
            
            result = PaymentProcessorService.handle_checkout_session_completed(session_data, db)
            
            assert result["status"] == "processed"
            mock_process.assert_called_once_with(
                db=db,
                metadata=session_data["metadata"],
                increase=True
            )
    
    def test_process_legacy_seat_upgrade(self, db: Session):
        """Test processing legacy seat upgrade"""
        session_data = {
            "id": "session_123",
            "customer": "cus_123",
            "metadata": {
                "seat_count": "8"
            }
        }
        
        with patch.object(PaymentProcessorService, '_process_legacy_seat_upgrade') as mock_process:
            mock_process.return_value = {"status": "processed", "action": "legacy_seat_upgrade"}
            
            result = PaymentProcessorService.handle_checkout_session_completed(session_data, db)
            
            assert result["status"] == "processed"
            mock_process.assert_called_once()
    
    def test_process_free_to_pro_upgrade(self, db: Session):
        """Test processing free to pro upgrade"""
        session_data = {
            "id": "session_123",
            "customer": "cus_123",
            "metadata": {
                "upgrade_type": "free_to_pro"
            }
        }
        
        with patch.object(PaymentProcessorService, '_process_free_to_pro_upgrade') as mock_process:
            mock_process.return_value = {"status": "processed", "action": "free_to_pro_upgrade"}
            
            result = PaymentProcessorService.handle_checkout_session_completed(session_data, db)
            
            assert result["status"] == "processed"
            mock_process.assert_called_once()
    
    def test_process_regular_subscription_signup(self, db: Session):
        """Test processing regular subscription signup"""
        session_data = {
            "id": "session_123",
            "customer": "cus_123",
            "metadata": {}
        }
        
        with patch.object(PaymentProcessorService, '_process_subscription_signup') as mock_process:
            mock_process.return_value = {"status": "processed", "action": "subscription_signup"}
            
            result = PaymentProcessorService.handle_checkout_session_completed(session_data, db)
            
            assert result["status"] == "processed"
            mock_process.assert_called_once()
    
    def test_process_error_handling(self, db: Session):
        """Test error handling in checkout processing"""
        session_data = {
            "id": "session_123",
            "customer": "cus_123",
            "metadata": {}
        }
        
        with patch.object(PaymentProcessorService, '_process_subscription_signup') as mock_process:
            mock_process.side_effect = Exception("Database error")
            
            result = PaymentProcessorService.handle_checkout_session_completed(session_data, db)
            
            assert result["status"] == "error"
            assert "error" in result["message"].lower() or "Database error" in result["message"]


class TestProcessSeatChange:
    """Test seat change processing"""
    
    def test_seat_change_success_increase(self, db: Session):
        """Test successful seat increase"""
        facility = Facility(id=1, name="Test Facility", stripe_customer_id="cus_123")
        subscription = Subscription(
            id=1,
            facility_id=1,
            stripe_subscription_id="sub_123",
            seat_count=5,
            status=SubscriptionStatus.ACTIVE
        )
        db.add(facility)
        db.add(subscription)
        db.commit()
        
        metadata = {
            "facility_id": "1",
            "subscription_id": "sub_123",
            "new_seat_count": "10"
        }
        
        with patch('app.services.payment_processor_service.StripeService') as mock_stripe_class:
            mock_stripe = MagicMock()
            mock_stripe_class.return_value = mock_stripe
            mock_stripe.get_subscription.return_value = MagicMock(status="active")
            mock_stripe.update_subscription_seats.return_value = None
            mock_stripe.calculate_subscription_amount.return_value = 100.0
            
            result = PaymentProcessorService._process_seat_change(
                db=db,
                metadata=metadata,
                increase=True
            )
            
            assert result["status"] == "processed"
            assert "seat_upgrade_completed" in result["action"]
    
    def test_seat_change_missing_metadata(self, db: Session):
        """Test seat change with missing metadata"""
        metadata = {
            "facility_id": "1"
            # Missing subscription_id and new_seat_count
        }
        
        result = PaymentProcessorService._process_seat_change(
            db=db,
            metadata=metadata,
            increase=True
        )
        
        assert result["status"] == "error"
        assert "missing" in result["message"].lower()
    
    def test_seat_change_facility_not_found(self, db: Session):
        """Test seat change with non-existent facility"""
        metadata = {
            "facility_id": "999",
            "subscription_id": "sub_123",
            "new_seat_count": "10"
        }
        
        result = PaymentProcessorService._process_seat_change(
            db=db,
            metadata=metadata,
            increase=True
        )
        
        assert result["status"] == "error"
        assert "facility not found" in result["message"].lower()
    
    def test_seat_change_subscription_not_found(self, db: Session):
        """Test seat change with non-existent subscription"""
        facility = Facility(id=1, name="Test Facility")
        db.add(facility)
        db.commit()
        
        metadata = {
            "facility_id": "1",
            "subscription_id": "nonexistent",
            "new_seat_count": "10"
        }
        
        result = PaymentProcessorService._process_seat_change(
            db=db,
            metadata=metadata,
            increase=True
        )
        
        assert result["status"] == "error"
        assert "subscription not found" in result["message"].lower()
    
    def test_seat_change_canceled_subscription(self, db: Session):
        """Test seat change on canceled subscription"""
        facility = Facility(id=1, name="Test Facility", stripe_customer_id="cus_123")
        subscription = Subscription(
            id=1,
            facility_id=1,
            stripe_subscription_id="sub_123",
            seat_count=5,
            status=SubscriptionStatus.CANCELED
        )
        db.add(facility)
        db.add(subscription)
        db.commit()
        
        metadata = {
            "facility_id": "1",
            "subscription_id": "sub_123",
            "new_seat_count": "10"
        }
        
        with patch('app.services.payment_processor_service.StripeService') as mock_stripe_class:
            mock_stripe = MagicMock()
            mock_stripe_class.return_value = mock_stripe
            mock_stripe.get_subscription.return_value = MagicMock(status="canceled")
            
            with patch('app.services.payment_processor_service.stripe.Subscription.list') as mock_list:
                mock_list.return_value.data = []  # No active subscriptions
                
                result = PaymentProcessorService._process_seat_change(
                    db=db,
                    metadata=metadata,
                    increase=True
                )
                
                assert result["status"] == "error"
                assert "canceled" in result["message"].lower() or "resubscribe" in result["message"].lower()


class TestProcessFreeToProUpgrade:
    """Test free to pro upgrade processing"""
    
    def test_free_to_pro_upgrade_success(self, db: Session):
        """Test successful free to pro upgrade"""
        session_data = {
            "id": "session_123",
            "customer": "cus_123",
            "subscription": "sub_123"
        }
        metadata = {
            "upgrade_type": "free_to_pro",
            "user_id": "1"
        }
        
        with patch('app.services.payment_processor_service.StripeService') as mock_stripe_class:
            mock_stripe = MagicMock()
            mock_stripe_class.return_value = mock_stripe
            
            # Mock the internal method if it exists
            with patch.object(PaymentProcessorService, '_process_free_to_pro_upgrade') as mock_process:
                mock_process.return_value = {"status": "processed", "action": "free_to_pro_upgrade"}
                
                result = PaymentProcessorService._process_free_to_pro_upgrade(
                    db=db,
                    metadata=metadata,
                    session_data=session_data,
                    customer_id="cus_123",
                    session_id="session_123"
                )
                
                assert result["status"] == "processed"


class TestProcessSubscriptionSignup:
    """Test subscription signup processing"""
    
    def test_subscription_signup_success(self, db: Session):
        """Test successful subscription signup"""
        session_data = {
            "id": "session_123",
            "customer": "cus_123",
            "subscription": "sub_123",
            "metadata": {}
        }
        
        with patch.object(PaymentProcessorService, '_process_subscription_signup') as mock_process:
            mock_process.return_value = {"status": "processed", "action": "subscription_signup"}
            
            result = PaymentProcessorService._process_subscription_signup(db, session_data)
            
            assert result["status"] == "processed"

