"""
Stripe Service Unit Tests
-------------------------
Tests for Stripe payment integration including:
- Customer creation
- Subscription management
- Seat calculations
- Webhook processing
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
import stripe

from app.services.stripe_service import StripeService
from app.models.facility import Facility
from app.models.subscription import Subscription
from app.models.subscription import SubscriptionStatus


class TestStripeService:
    """Test StripeService class"""
    
    def test_create_customer_success(self):
        """Test successful customer creation"""
        with patch('stripe.Customer.create') as mock_create:
            mock_customer = MagicMock()
            mock_customer.id = "cus_test123"
            mock_create.return_value = mock_customer
            
            service = StripeService()
            customer = service.create_customer(
                email="test@example.com",
                name="Test User",
                facility_name="Test Facility"
            )
            
            assert customer.id == "cus_test123"
            mock_create.assert_called_once()
    
    def test_create_customer_with_metadata(self):
        """Test customer creation with custom metadata"""
        with patch('stripe.Customer.create') as mock_create:
            mock_customer = MagicMock()
            mock_customer.id = "cus_test123"
            mock_create.return_value = mock_customer
            
            service = StripeService()
            customer = service.create_customer(
                email="test@example.com",
                name="Test User",
                facility_name="Test Facility",
                metadata={"custom_key": "custom_value"}
            )
            
            assert customer.id == "cus_test123"
            call_args = mock_create.call_args[1]
            assert "custom_key" in call_args["metadata"]
    
    def test_create_customer_stripe_error(self):
        """Test customer creation with Stripe error"""
        with patch('stripe.Customer.create') as mock_create:
            mock_create.side_effect = stripe.error.StripeError("Stripe API error")
            
            service = StripeService()
            
            with pytest.raises(stripe.error.StripeError):
                service.create_customer(
                    email="test@example.com",
                    name="Test User",
                    facility_name="Test Facility"
                )
    
    def test_calculate_subscription_amount_base(self):
        """Test subscription amount calculation for base subscription"""
        service = StripeService()
        amount = service.calculate_subscription_amount(seat_count=1)
        
        assert amount == service.BASE_PRICE
    
    def test_calculate_subscription_amount_with_seats(self):
        """Test subscription amount calculation with additional seats"""
        service = StripeService()
        amount = service.calculate_subscription_amount(seat_count=5)
        
        expected = service.BASE_PRICE + (service.PER_SEAT_PRICE * 4)
        assert amount == expected
    
    def test_calculate_subscription_amount_zero_seats(self):
        """Test subscription amount calculation with zero seats (should default to 1)"""
        service = StripeService()
        amount = service.calculate_subscription_amount(seat_count=0)
        
        # Should default to base price
        assert amount == service.BASE_PRICE
    
    @patch('stripe.Subscription.create')
    def test_create_subscription_success(self, mock_create):
        """Test successful subscription creation"""
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_test123"
        mock_subscription.status = "active"
        mock_create.return_value = mock_subscription
        
        with patch('app.services.stripe_service.get_settings') as mock_settings:
            mock_settings.return_value.STRIPE_PRO_BASE_PRICE_ID = "price_base"
            mock_settings.return_value.STRIPE_USER_SEAT_PRICE_ID = "price_seat"
            
            service = StripeService()
            subscription = service.create_subscription(
                customer_id="cus_test123",
                facility_id=1,
                seat_count=3
            )
            
            assert subscription.id == "sub_test123"
            mock_create.assert_called_once()
    
    @patch('stripe.Subscription.retrieve')
    def test_get_subscription_success(self, mock_retrieve):
        """Test successful subscription retrieval"""
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_test123"
        mock_subscription.status = "active"
        mock_retrieve.return_value = mock_subscription
        
        service = StripeService()
        subscription = service.get_subscription("sub_test123")
        
        assert subscription.id == "sub_test123"
        mock_retrieve.assert_called_once_with("sub_test123")
    
    @patch('stripe.Subscription.modify')
    def test_update_subscription_seats_success(self, mock_modify):
        """Test successful subscription seat update"""
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_test123"
        mock_modify.return_value = mock_subscription
        
        with patch('app.services.stripe_service.get_settings') as mock_settings:
            mock_settings.return_value.STRIPE_USER_SEAT_PRICE_ID = "price_seat"
            
            service = StripeService()
            result = service.update_subscription_seats("sub_test123", new_seat_count=5)
            
            assert result is not None
            mock_modify.assert_called_once()
    
    @patch('stripe.Subscription.delete')
    def test_cancel_subscription_success(self, mock_delete):
        """Test successful subscription cancellation"""
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_test123"
        mock_delete.return_value = mock_subscription
        
        service = StripeService()
        result = service.cancel_subscription("sub_test123")
        
        assert result is not None
        mock_delete.assert_called_once_with("sub_test123")
    
    @patch('stripe.Customer.retrieve')
    def test_get_customer_success(self, mock_retrieve):
        """Test successful customer retrieval"""
        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"
        mock_retrieve.return_value = mock_customer
        
        service = StripeService()
        customer = service.get_customer("cus_test123")
        
        assert customer.id == "cus_test123"
        mock_retrieve.assert_called_once_with("cus_test123")
    
    @patch('stripe.Customer.modify')
    def test_update_customer_success(self, mock_modify):
        """Test successful customer update"""
        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"
        mock_modify.return_value = mock_customer
        
        service = StripeService()
        result = service.update_customer("cus_test123", email="newemail@example.com")
        
        assert result is not None
        mock_modify.assert_called_once()

