"""
Stripe Service Module

This module provides Stripe payment integration services for the EnCompliance Pro Mode system.
It handles subscription creation, billing management, and webhook processing.

Key functionalities:
- Customer creation and management
- Subscription lifecycle management ($50 base + $20 per additional user)
- Seat-based billing calculations
- Webhook event processing
- Payment method management
- Invoice and billing history

Dependencies:
- stripe: Stripe Python SDK for payment processing
- sqlalchemy: Database operations
- decimal: Precise monetary calculations
"""

import stripe
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models import Facility, Subscription, User
from app.models.subscription import SubscriptionStatus
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service class for Stripe payment operations."""
    
    BASE_PRICE = Decimal('50.00')  # Base facility price
    PER_SEAT_PRICE = Decimal('20.00')  # Price per additional user
    
    def __init__(self):
        """Initialize Stripe service with configuration."""
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def create_customer(self, email: str, name: str, facility_name: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> stripe.Customer:
        """Create a Stripe customer for facility administrator.
        
        Note: Facility administrators are users with a pro subscription who manage facility operations.
        """
        try:
            customer_data = {
                'email': email,
                'name': name,
                'description': f'Facility Administrator for {facility_name}',
                'metadata': {
                    'facility_name': facility_name,
                    'user_type': 'facility_admin',
                    **(metadata or {})
                }
            }
            
            customer = stripe.Customer.create(**customer_data)
            logger.info(f"Created Stripe customer {customer.id} for {email}")
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise
    
    def create_subscription(self, customer_id: str, facility_id: int, 
                          seat_count: int = 1, trial_days: int = 7) -> stripe.Subscription:
        """Create a Stripe subscription with seat-based pricing."""
        try:
            from app.core.config import get_settings
            settings = get_settings()
            
            # Use predefined price IDs
            items = []
            
            # Base subscription (always 1)
            items.append({
                'price': settings.STRIPE_PRO_BASE_PRICE_ID,
                'quantity': 1
            })
            
            # Additional seats if needed
            if seat_count > 1:
                additional_seats = seat_count - 1
                items.append({
                    'price': settings.STRIPE_USER_SEAT_PRICE_ID,
                    'quantity': additional_seats
                })
            
            # Create subscription
            subscription_data = {
                'customer': customer_id,
                'items': items,
                'trial_period_days': trial_days,
                'payment_behavior': 'default_incomplete',
                'payment_settings': {'save_default_payment_method': 'on_subscription'},
                'expand': ['latest_invoice.payment_intent'],
                'metadata': {
                    'facility_id': str(facility_id),
                    'seat_count': str(seat_count),
                    'base_price': str(self.BASE_PRICE),
                    'per_seat_price': str(self.PER_SEAT_PRICE)
                }
            }
            
            subscription = stripe.Subscription.create(**subscription_data)
            logger.info(f"Created Stripe subscription {subscription.id} for facility {facility_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe subscription: {str(e)}")
            raise
    
    def update_subscription_seats(self, subscription_id: str, new_seat_count: int) -> stripe.Subscription:
        """Update subscription with new seat count and pricing."""
        try:
            from app.core.config import get_settings
            settings = get_settings()
            
            # Get current subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            current_items = subscription['items']['data']
            
            # Build items to update/add/remove
            items_to_update = []
            
            # Find existing base subscription item
            base_item = None
            seat_item = None
            
            for item in current_items:
                if item['price']['id'] == settings.STRIPE_PRO_BASE_PRICE_ID:
                    base_item = item
                elif item['price']['id'] == settings.STRIPE_USER_SEAT_PRICE_ID:
                    seat_item = item
            
            # Always keep base subscription (quantity 1)
            if base_item:
                items_to_update.append({
                    'id': base_item['id'],
                    'quantity': 1
                })
            else:
                # This shouldn't happen, but add base if missing
                items_to_update.append({
                    'price': settings.STRIPE_PRO_BASE_PRICE_ID,
                    'quantity': 1
                })
            
            # Handle additional seats
            if new_seat_count > 1:
                additional_seats = new_seat_count - 1
                if seat_item:
                    # Update existing seat item
                    items_to_update.append({
                        'id': seat_item['id'],
                        'quantity': additional_seats
                    })
                else:
                    # Add new seat item
                    items_to_update.append({
                        'price': settings.STRIPE_USER_SEAT_PRICE_ID,
                        'quantity': additional_seats
                    })
            elif seat_item:
                # Remove seat item if going back to 1 user
                items_to_update.append({
                    'id': seat_item['id'],
                    'deleted': True
                })
            
            # Update subscription
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=items_to_update,
                proration_behavior='create_prorations',
                metadata={
                    **subscription.metadata,
                    'seat_count': str(new_seat_count)
                }
            )
            
            logger.info(f"Updated subscription {subscription_id} to {new_seat_count} seats")
            return updated_subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription seats: {str(e)}")
            raise
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True, 
                          reason: Optional[str] = None) -> stripe.Subscription:
        """Cancel a Stripe subscription."""
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                    metadata={
                        'cancellation_reason': reason or 'User requested cancellation'
                    }
                )
            else:
                subscription = stripe.Subscription.cancel(
                    subscription_id,
                    metadata={
                        'cancellation_reason': reason or 'Immediate cancellation'
                    }
                )
            
            logger.info(f"Cancelled subscription {subscription_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            raise
    
    def get_subscription(self, subscription_id: str) -> stripe.Subscription:
        """Retrieve subscription details from Stripe."""
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription: {str(e)}")
            raise
    
    def get_customer(self, customer_id: str) -> stripe.Customer:
        """Retrieve customer details from Stripe."""
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve customer: {str(e)}")
            raise
    
    def get_payment_methods(self, customer_id: str) -> List[stripe.PaymentMethod]:
        """Get all payment methods for a customer."""
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )
            return payment_methods.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve payment methods: {str(e)}")
            raise
    
    def create_setup_intent(self, customer_id: str) -> stripe.SetupIntent:
        """Create a setup intent for saving payment methods."""
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=['card'],
                usage='off_session'
            )
            return setup_intent
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create setup intent: {str(e)}")
            raise
    
    def get_invoices(self, customer_id: str, limit: int = 10) -> List[stripe.Invoice]:
        """Get invoices for a customer."""
        try:
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )
            return invoices.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve invoices: {str(e)}")
            raise
    
    def calculate_subscription_amount(self, seat_count: int) -> Decimal:
        """Calculate total subscription amount based on seat count."""
        if seat_count <= 1:
            return self.BASE_PRICE
        
        additional_seats = seat_count - 1
        return self.BASE_PRICE + (additional_seats * self.PER_SEAT_PRICE)
    
    def process_webhook_event(self, event: stripe.Event, db: Session) -> Dict[str, Any]:
        """Process Stripe webhook events."""
        try:
            event_type = event['type']
            data = event['data']['object']
            
            logger.info(f"Processing webhook event: {event_type}")
            
            if event_type == 'customer.subscription.created':
                return self._handle_subscription_created(data, db)
            elif event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(data, db)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(data, db)
            elif event_type == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(data, db)
            elif event_type == 'invoice.payment_failed':
                return self._handle_payment_failed(data, db)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {'status': 'ignored', 'event_type': event_type}
                
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            raise
    
    def _handle_subscription_created(self, subscription_data: Dict, db: Session) -> Dict[str, Any]:
        """Handle subscription creation webhook."""
        # This would typically be handled by the API endpoint that creates the subscription
        # But we can update local records if needed
        return {'status': 'processed', 'action': 'subscription_created'}
    
    def _handle_subscription_updated(self, subscription_data: Dict, db: Session) -> Dict[str, Any]:
        """Handle subscription update webhook."""
        stripe_subscription_id = subscription_data['id']
        
        # Find local subscription record
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_subscription_id
        ).first()
        
        if subscription:
            # Update local subscription status
            subscription.status = subscription_data['status']
            subscription.current_period_start = datetime.fromtimestamp(subscription_data['current_period_start'])
            subscription.current_period_end = datetime.fromtimestamp(subscription_data['current_period_end'])
            
            if subscription_data.get('canceled_at'):
                subscription.cancelled_at = datetime.fromtimestamp(subscription_data['canceled_at'])
            
            # Calculate seat count from subscription items
            items = subscription_data.get('items', {}).get('data', [])
            new_seat_count = 1  # Base subscription
            
            from app.core.config import get_settings
            settings = get_settings()
            
            for item in items:
                price_id = item.get('price', {}).get('id')
                quantity = item.get('quantity', 0)
                
                if price_id == settings.STRIPE_USER_SEAT_PRICE_ID:
                    # Additional seats
                    new_seat_count += quantity
            
            # Update seat count and total amount
            subscription.seat_count = new_seat_count
            subscription.total_amount = self.calculate_subscription_amount(new_seat_count)
            
            db.commit()
            logger.info(f"Updated local subscription {subscription.id} - seat count: {new_seat_count}")
        
        return {'status': 'processed', 'action': 'subscription_updated'}
    
    def _handle_subscription_deleted(self, subscription_data: Dict, db: Session) -> Dict[str, Any]:
        """Handle subscription deletion webhook."""
        stripe_subscription_id = subscription_data['id']
        
        # Find and update local subscription record
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_subscription_id
        ).first()
        
        if subscription:
            from app.services.subscription_downgrade_service import SubscriptionDowngradeService
            
            # Check if this was a user-initiated cancellation or system cancellation
            cancellation_reason = subscription_data.get('metadata', {}).get('cancellation_reason', 'Subscription deleted')
            
            # Perform immediate downgrade for subscription deletion
            success = SubscriptionDowngradeService.immediate_downgrade(
                subscription, 
                db, 
                cancellation_reason
            )
            
            if success:
                logger.info(f"Successfully downgraded subscription {subscription.id}")
                return {'status': 'processed', 'action': 'subscription_downgraded'}
            else:
                # Fallback to old behavior
                subscription.status = SubscriptionStatus.CANCELLED.value
                subscription.cancelled_at = datetime.now()
                
                # Deactivate facility
                if subscription.facility:
                    subscription.facility.is_active = False
                
                db.commit()
                logger.info(f"Cancelled local subscription {subscription.id}")
                return {'status': 'processed', 'action': 'subscription_cancelled'}
        
        return {'status': 'processed', 'action': 'subscription_not_found'}
    
    def _handle_payment_succeeded(self, invoice_data: Dict, db: Session) -> Dict[str, Any]:
        """Handle successful payment webhook."""
        subscription_id = invoice_data.get('subscription')
        
        if subscription_id:
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()
            
            if subscription:
                subscription.latest_invoice_id = invoice_data['id']
                subscription.status = SubscriptionStatus.ACTIVE.value
                db.commit()
        
        return {'status': 'processed', 'action': 'payment_succeeded'}
    
    def _handle_payment_failed(self, invoice_data: Dict, db: Session) -> Dict[str, Any]:
        """Handle failed payment webhook."""
        subscription_id = invoice_data.get('subscription')
        
        if subscription_id:
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()
            
            if subscription:
                # Import the downgrade service
                from app.services.subscription_downgrade_service import SubscriptionDowngradeService
                
                # Initiate grace period for payment failures (48 hours)
                success = SubscriptionDowngradeService.initiate_grace_period(subscription, db)
                
                if success:
                    # Update payment attempt tracking
                    if invoice_data.get('next_payment_attempt'):
                        subscription.next_payment_attempt = datetime.fromtimestamp(
                            invoice_data['next_payment_attempt']
                        )
                    
                    logger.info(f"Initiated grace period for subscription {subscription.id} due to payment failure")
                    return {'status': 'processed', 'action': 'grace_period_initiated'}
                else:
                    # Fallback to old behavior if grace period initiation fails
                    subscription.status = SubscriptionStatus.PAST_DUE.value
                    if invoice_data.get('next_payment_attempt'):
                        subscription.next_payment_attempt = datetime.fromtimestamp(
                            invoice_data['next_payment_attempt']
                        )
                    db.commit()
                    return {'status': 'processed', 'action': 'marked_past_due'}
        
        return {'status': 'processed', 'action': 'payment_failed'}

    def create_trial_subscription(
        self,
        customer_id: str,
        facility_id: int,
        trial_days: int = 7,
        db: Session = None
    ) -> stripe.Subscription:
        """
        Create a trial subscription for a new facility
        
        Args:
            customer_id: Stripe customer ID
            facility_id: Database facility ID
            trial_days: Number of trial days (default 7)
            db: Database session for subscription record creation
            
        Returns:
            Stripe subscription object
            
        Raises:
            StripeServiceError: If subscription creation fails
        """
        try:
            # Calculate trial end date
            trial_end = datetime.now() + timedelta(days=trial_days)
            
            # Create base subscription with trial
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price': settings.STRIPE_PRO_BASE_PRICE_ID,
                    'quantity': 1
                }],
                trial_end=int(trial_end.timestamp()),
                metadata={
                    'facility_id': str(facility_id),
                    'subscription_type': 'facility_pro',
                    'trial_days': str(trial_days)
                }
            )
            
            # Create database subscription record if db session provided
            if db:
                from app.models.subscription import Subscription
                
                db_subscription = Subscription(
                    stripe_subscription_id=subscription.id,
                    stripe_customer_id=customer_id,
                    facility_id=facility_id,
                    status='trialing',
                    current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                    current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                    trial_end=trial_end,
                    seat_count=1,
                    base_price=Decimal('50.00'),
                    per_seat_price=Decimal('20.00'),
                    total_amount=Decimal('0.00')  # No charge during trial
                )
                
                db.add(db_subscription)
                db.commit()
                db.refresh(db_subscription)
                
                logger.info(f"Created subscription record for facility {facility_id}")
            
            logger.info(f"Created trial subscription {subscription.id} for customer {customer_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating trial subscription: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating trial subscription: {str(e)}")
            raise 