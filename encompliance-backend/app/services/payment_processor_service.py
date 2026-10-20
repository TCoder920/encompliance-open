"""Payment Processor Service

Centralised logic for processing completed Stripe Checkout Sessions in EnCompliance.
This module is the single source of truth for all side-effects triggered once a
checkout session has been paid, including seat adjustments and plan upgrades.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
import logging
import json
from datetime import datetime
from decimal import Decimal

import stripe

from app.models import Facility, Subscription, User
from app.models.user import UserRole
from app.models.subscription import SubscriptionStatus
from app.services.stripe_service import StripeService

logger = logging.getLogger(__name__)

class PaymentProcessorService:
    """Payment Processor Service Module

    This module centralises all logic related to processing completed Stripe Checkout
    Sessions for the EnCompliance application. It was extracted from the original
    `handle_checkout_session_completed` implementation inside
    `app/api/routes/payments.py` to promote single-responsibility, facilitate reuse
    across multiple API endpoints, and keep route handlers lightweight.

    Main responsibilities:
    1. Seat change processing (upgrades and reductions).
    2. Free-to-Pro subscription upgrades including facility creation/activation.
    3. Legacy seat upgrade fallback handling.
    4. Standard subscription sign-up activation.

    The service guarantees:
    • Database transaction safety with proper commits/rollbacks.
    • Robust fallback strategies when metadata is incomplete.
    • Comprehensive error logging with clear action indicators.
    • No direct dependency on FastAPI request objects (pure business logic).

    Public Interface:
    • PaymentProcessorService.handle_checkout_session_completed(session_data, db)

    This returns a standardised dictionary:
        {"status": "processed"|"error"|"ignored", "action": <str>, "message": <str>}
    which consumers (API routes, webhooks, background tasks) can use to determine
    next steps.
    """

    @staticmethod
    def handle_checkout_session_completed(session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Process a completed Stripe Checkout Session.

        Parameters
        ----------
        session_data : Dict[str, Any]
            Raw session dictionary as returned by Stripe.
        db : Session
            SQLAlchemy session for persistence operations.

        Returns
        -------
        Dict[str, Any]
            Standardised status dictionary consumed by API routes.
        """
        try:
            session_id = session_data['id']
            customer_id = session_data['customer']
            metadata = session_data.get('metadata', {}) or {}

            # 1. Seat Reduction -------------------------------------------------
            if metadata.get('seat_reduction') == 'true':
                return PaymentProcessorService._process_seat_change(
                    db=db,
                    metadata=metadata,
                    increase=False
                )

            # 2. Seat Upgrade ---------------------------------------------------
            if metadata.get('seat_upgrade') == 'true':
                return PaymentProcessorService._process_seat_change(
                    db=db,
                    metadata=metadata,
                    increase=True
                )

            # 3. Legacy seat upgrade (metadata has seat_count) ------------------
            if metadata.get('seat_count'):
                return PaymentProcessorService._process_legacy_seat_upgrade(
                    db=db,
                    session_data=session_data,
                    metadata=metadata
                )

            # 4. Free → Pro upgrade --------------------------------------------
            if metadata.get('upgrade_type') == 'free_to_pro':
                return PaymentProcessorService._process_free_to_pro_upgrade(
                    db=db,
                    metadata=metadata,
                    session_data=session_data,
                    customer_id=customer_id,
                    session_id=session_id
                )

            # 5. Regular subscription signup fallback --------------------------
            return PaymentProcessorService._process_subscription_signup(db, session_data)
        except Exception as exc:
            logger.error(f"PaymentProcessorService error: {exc}")
            db.rollback()
            return {'status': 'error', 'message': str(exc)}

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _process_seat_change(*, db: Session, metadata: Dict[str, Any], increase: bool) -> Dict[str, Any]:
        facility_id = metadata.get('facility_id')
        new_seat_count = int(metadata.get('new_seat_count')) if metadata.get('new_seat_count') else None
        subscription_id = metadata.get('subscription_id')

        if not (facility_id and subscription_id and new_seat_count):
            return {'status': 'error', 'message': 'Missing seat change metadata'}

        facility = db.query(Facility).filter(Facility.id == int(facility_id)).first()
        if not facility:
            return {'status': 'error', 'message': 'Facility not found'}

        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()

        if not subscription:
            # Fallback: try locate subscription by facility
            subscription = db.query(Subscription).filter(
                Subscription.facility_id == facility.id
            ).order_by(Subscription.created_at.desc()).first()

        if not subscription:
            return {'status': 'error', 'message': 'Subscription not found'}

        try:
            stripe_service = StripeService()
            
            # Check if the subscription is canceled
            stripe_subscription = stripe_service.get_subscription(subscription.stripe_subscription_id)
            
            if stripe_subscription.status == 'canceled':
                logger.warning(f"Attempted seat change on canceled subscription {subscription_id} for facility {facility_id}")
                
                # Check if the customer has a new active subscription
                if facility.stripe_customer_id:
                    try:
                        active_subs = stripe.Subscription.list(
                            customer=facility.stripe_customer_id, 
                            status='active',
                            limit=1
                        )
                        
                        if active_subs.data:
                            # Customer has resubscribed - this old session is no longer valid
                            logger.info(f"Customer {facility.stripe_customer_id} has resubscribed with new subscription {active_subs.data[0].id}")
                            return {
                                'status': 'error', 
                                'message': 'This payment session is for a canceled subscription. You have since resubscribed with a new subscription. Please initiate a new seat upgrade from your current dashboard.',
                                'error_code': 'session_for_canceled_subscription',
                                'action_required': 'restart_seat_upgrade'
                            }
                    except Exception as e:
                        logger.error(f"Error checking for active subscriptions: {e}")
                
                # No active subscription found - user needs to resubscribe
                return {
                    'status': 'error', 
                    'message': 'Your subscription has been canceled. Please resubscribe to your Pro plan before adding additional seats.',
                    'error_code': 'subscription_canceled',
                    'action_required': 'resubscribe'
                }
            
            # Normal subscription update for active subscriptions
            stripe_service.update_subscription_seats(subscription.stripe_subscription_id, new_seat_count)

            subscription.seat_count = new_seat_count
            subscription.total_amount = stripe_service.calculate_subscription_amount(new_seat_count)
            db.commit()

            action = 'seat_upgrade_completed' if increase else 'seat_reduction_completed'
            logger.info(f"Facility {facility_id}: seat change processed to {new_seat_count} seats (increase={increase})")
            return {'status': 'processed', 'action': action}
                
        except Exception as exc:
            logger.error(f"Error updating subscription seats: {exc}")
            return {'status': 'error', 'message': f'Failed to update subscription: {exc}'}

    @staticmethod
    def _process_legacy_seat_upgrade(*, db: Session, session_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        facility_id = metadata.get('facility_id')
        new_seat_count = int(metadata.get('seat_count'))

        facility = db.query(Facility).filter(Facility.id == int(facility_id)).first() if facility_id else None
        if not facility:
            return {'status': 'error', 'message': 'Facility not found'}

        subscription = db.query(Subscription).filter(
            Subscription.facility_id == facility.id
        ).order_by(Subscription.created_at.desc()).first()

        if not subscription:
            return {'status': 'error', 'message': 'Subscription not found'}

        subscription_id = session_data.get('subscription')
        if hasattr(subscription_id, 'id'):
            subscription_id = subscription_id.id

        stripe_subscription = stripe.Subscription.retrieve(subscription_id)

        stripe_service = StripeService()
        stripe_service.update_subscription_seats(subscription.stripe_subscription_id, new_seat_count)

        subscription.seat_count = new_seat_count
        subscription.total_amount = Decimal(str(stripe_subscription.items.data[0].price.unit_amount / 100))
        db.commit()

        logger.info(f"Facility {facility_id}: legacy seat upgrade to {new_seat_count} seats")
        return {'status': 'processed', 'action': 'seat_upgrade_completed'}

    @staticmethod
    def _process_free_to_pro_upgrade(*, db: Session, metadata: Dict[str, Any], session_data: Dict[str, Any], customer_id: str, session_id: str) -> Dict[str, Any]:
        user_id = metadata.get('user_id')
        facility_data_json = metadata.get('facility_data')

        if not user_id or not facility_data_json:
            logger.error(f"Missing user_id or facility_data in checkout session {session_id}")
            return {'status': 'error', 'message': 'Missing required metadata'}

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return {'status': 'error', 'message': 'User not found'}

        if user.subscription_status == 'pro' and user.facility_id:
            return {'status': 'processed', 'action': 'user_already_upgraded_to_pro', 'message': 'User already has Pro subscription'}

        facility_data = json.loads(facility_data_json)
        subscription_id = session_data.get('subscription')
        if hasattr(subscription_id, 'id'):
            subscription_id = subscription_id.id

        stripe_subscription = stripe.Subscription.retrieve(subscription_id)

        # Check for existing facility linked to customer
        existing_facility = db.query(Facility).filter(Facility.stripe_customer_id == customer_id).first()
        if existing_facility:
            return PaymentProcessorService._upgrade_user_with_existing_facility(
                db=db,
                user=user,
                facility=existing_facility,
                subscription_id=subscription_id,
                customer_id=customer_id,
                stripe_subscription=stripe_subscription
            )

        # Otherwise, create a new facility
        facility = Facility(
            facility_name=facility_data['name'],
            facility_address=facility_data.get('address'),
            facility_city=facility_data.get('city'),
            facility_state=facility_data.get('state'),
            facility_zip=facility_data.get('zip'),
            facility_phone=facility_data.get('phone'),
            facility_email=facility_data.get('email'),
            admin_user_id=user.id,
            stripe_customer_id=customer_id,
            is_active=True
        )
        db.add(facility)
        db.flush()

        PaymentProcessorService._create_subscription_record(
            db=db,
            facility=facility,
            subscription_id=subscription_id,
            customer_id=customer_id,
            stripe_subscription=stripe_subscription
        )

        # Promote user
        user.subscription_status = 'pro'
        user.user_role = UserRole.FACILITY_ADMIN
        user.facility_id = facility.id
        db.commit()

        logger.info(f"User {user.id} upgraded to Pro with new facility {facility.id}")
        return {'status': 'processed', 'action': 'user_upgraded_to_pro'}

    @staticmethod
    def _upgrade_user_with_existing_facility(*, db: Session, user: User, facility: Facility, subscription_id: str, customer_id: str, stripe_subscription):
        user.subscription_status = 'pro'
        user.user_role = UserRole.FACILITY_ADMIN
        user.facility_id = facility.id
        facility.is_active = True

        existing_sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == subscription_id).first()
        if not existing_sub:
            PaymentProcessorService._create_subscription_record(
                db=db,
                facility=facility,
                subscription_id=subscription_id,
                customer_id=customer_id,
                stripe_subscription=stripe_subscription
            )
        db.commit()
        logger.info(f"User {user.id} upgraded using existing facility {facility.id}")
        return {'status': 'processed', 'action': 'user_upgraded_to_pro'}

    @staticmethod
    def _create_subscription_record(*, db: Session, facility: Facility, subscription_id: str, customer_id: str, stripe_subscription):
        subscription = Subscription(
            stripe_subscription_id=str(subscription_id),
            stripe_customer_id=customer_id,
            facility_id=facility.id,
            status=stripe_subscription.status,
            current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
            seat_count=1,
            total_amount=Decimal('50.00')
        )
        if stripe_subscription.trial_end:
            subscription.trial_end = datetime.fromtimestamp(stripe_subscription.trial_end)
        db.add(subscription)

    @staticmethod
    def _process_subscription_signup(db: Session, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback processing for sign-ups initiated via `create-subscription`."""
        subscription_id = session_data.get('subscription')
        if hasattr(subscription_id, 'id'):
            subscription_id = subscription_id.id

        subscription = db.query(Subscription).filter(Subscription.stripe_subscription_id == str(subscription_id)).first()
        if not subscription or not subscription.facility:
            return {'status': 'ignored', 'message': 'Not an upgrade checkout session'}

        user = db.query(User).filter(User.id == subscription.facility.admin_user_id).first()
        if user and user.subscription_status != 'pro':
            user.subscription_status = 'pro'
            user.user_role = UserRole.FACILITY_ADMIN
            user.facility_id = subscription.facility.id
            db.commit()
            logger.info(f"User {user.id} promoted to Pro after subscription {subscription_id}")
            return {'status': 'processed', 'action': 'user_subscription_activated'}

        return {'status': 'ignored', 'message': 'Not an upgrade checkout session'} 