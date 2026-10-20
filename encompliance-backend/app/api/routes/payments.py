"""
Payment API Routes Module

This module defines API endpoints for Stripe payment integration and subscription management.
It handles subscription creation, billing updates, payment methods, and webhook processing.

Key functionalities:
- Subscription signup and management
- Payment method management
- Billing history and invoice retrieval
- Stripe webhook event processing
- Seat count updates and billing calculations

Dependencies:
- fastapi: Web framework for API endpoints
- stripe: Payment processing integration
- sqlalchemy: Database operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal
import stripe
import logging
import json
from datetime import datetime
import asyncio

from app.core.config import get_settings
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Facility, Subscription, FacilityInvitation
from app.models.subscription import SubscriptionStatus
from app.models.user import UserRole
from app.services.stripe_service import StripeService
from app.schemas.facility import FacilityCreate, SubscriptionResponse
from app.services.subscription_downgrade_service import SubscriptionDowngradeService
from app.services.payment_processor_service import PaymentProcessorService

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


# Pydantic models for request/response
class SubscriptionCreateRequest(BaseModel):
    facilityName: str = Field(..., description="Name of the facility")
    facilityAddress: Optional[str] = None
    facilityCity: Optional[str] = None
    facilityState: Optional[str] = None
    facilityZip: Optional[str] = None
    facilityPhone: Optional[str] = None
    facilityEmail: Optional[str] = None
    trialDays: int = Field(7, description="Number of trial days")


class SeatUpdateRequest(BaseModel):
    seat_count: int = Field(..., ge=1, description="New seat count")


class CheckoutSessionRequest(BaseModel):
    """Request for creating a Stripe Checkout Session."""
    type: Optional[str] = Field(None, description="Type of checkout: seat_upgrade, etc.")
    mode: str = Field("subscription", description="Checkout mode: subscription, setup, or payment")
    seat_count: Optional[int] = Field(None, ge=1, description="Number of seats for subscription")
    additional_seats: Optional[int] = Field(None, ge=1, description="Number of additional seats to add")
    success_url: str = Field(..., description="URL to redirect after successful payment")
    cancel_url: str = Field(..., description="URL to redirect after cancelled payment")


class UpgradeToProRequest(BaseModel):
    """Request for upgrading a free user to Pro subscription."""
    facility_name: str = Field(..., description="Name of the facility to create")
    facility_address: Optional[str] = None
    facility_city: Optional[str] = None
    facility_state: Optional[str] = None
    facility_zip: Optional[str] = None
    facility_phone: Optional[str] = None
    facility_email: Optional[str] = None
    success_url: str = Field(..., description="URL to redirect after successful payment")
    cancel_url: str = Field(..., description="URL to redirect after cancelled payment")
    trial_days: int = Field(7, description="Number of trial days")


# In-memory cache for the portal configuration ID
_portal_config_id = "bpc_1RaSt3RQfRSwy2AaOkiAb3xO"  # Use new restricted configuration
_add_member_portal_config_id = "bpc_1RaQw4RQfRSwy2AaJaUEIfI7"  # Specialized config for adding team members
_remove_member_portal_config_id = "bpc_1RaQwMRQfRSwy2AaQB3zb0dC"  # Specialized config for removing team members
_portal_config_lock = asyncio.Lock()

async def get_or_create_portal_configuration():
    """
    Get the existing default portal configuration.
    """
    global _portal_config_id
    return _portal_config_id

async def get_or_create_add_member_portal_configuration():
    """
    Get the existing portal configuration for adding members.
    """
    global _add_member_portal_config_id
    return _add_member_portal_config_id

async def get_or_create_remove_member_portal_configuration():
    """
    Get the existing portal configuration for removing members.
    """
    global _remove_member_portal_config_id
    return _remove_member_portal_config_id


class PaymentMethodResponse(BaseModel):
    id: str
    brand: str
    last4: str
    expMonth: int
    expYear: int
    isDefault: bool


class InvoiceResponse(BaseModel):
    id: str
    amountPaid: int
    currency: str
    status: str
    created: int
    pdfUrl: Optional[str]


class SubscriptionStatusResponse(BaseModel):
    id: str
    status: str
    currentPeriodStart: int
    currentPeriodEnd: int
    seatCount: int
    totalAmount: str
    trialEnd: Optional[int] = None
    cancelAtPeriodEnd: bool = False


@router.post("/upgrade-to-pro")
async def upgrade_to_pro(
    request: UpgradeToProRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe Checkout Session for free user to upgrade to Pro."""
    try:
        # Check if user is currently free OR pro without a facility (incomplete signup)
        if current_user.subscription_status not in ['free', 'pro']:
            raise HTTPException(
                status_code=400,
                detail="User is not eligible for Pro upgrade"
            )
        
        # Check if user already has a facility
        if current_user.administered_facility:
            raise HTTPException(
                status_code=400,
                detail="User already administers a facility"
            )
        
        stripe_service = StripeService()
        
        # Create Stripe customer
        customer = stripe_service.create_customer(
            email=current_user.email,
            name=current_user.full_name or current_user.email,
            facility_name=request.facility_name,
            metadata={
                'user_id': str(current_user.id),
                'upgrade_date': str(datetime.now()),
                'facility_data': json.dumps({
                    'name': request.facility_name,
                    'address': request.facility_address,
                    'city': request.facility_city,
                    'state': request.facility_state,
                    'zip': request.facility_zip,
                    'phone': request.facility_phone,
                    'email': request.facility_email
                })
            }
        )
        
        # Create Stripe Checkout Session for subscription
        session = stripe.checkout.Session.create(
            customer=customer.id,
            mode='subscription',
            line_items=[{
                'price': settings.STRIPE_PRO_BASE_PRICE_ID,
                'quantity': 1
            }],
            success_url=request.success_url + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.cancel_url,
            subscription_data={
                'trial_period_days': request.trial_days,
                'metadata': {
                    'user_id': str(current_user.id),
                    'facility_name': request.facility_name,
                    'upgrade_type': 'free_to_pro'
                }
            },
            metadata={
                'user_id': str(current_user.id),
                'facility_name': request.facility_name,
                'upgrade_type': 'free_to_pro',
                'facility_data': json.dumps({
                    'name': request.facility_name,
                    'address': request.facility_address,
                    'city': request.facility_city,
                    'state': request.facility_state,
                    'zip': request.facility_zip,
                    'phone': request.facility_phone,
                    'email': request.facility_email
                })
            },
            billing_address_collection='required'
        )
        
        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "customer_id": customer.id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating upgrade checkout: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating upgrade checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create upgrade checkout")


@router.post("/create-subscription", response_model=Dict[str, Any])
async def create_subscription(
    request: SubscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new facility subscription for the current user."""
    try:
        # Check if user already has a facility
        if current_user.administered_facility:
            raise HTTPException(
                status_code=400,
                detail="User already administers a facility"
            )
        
        stripe_service = StripeService()
        
        # Create Stripe customer
        customer = stripe_service.create_customer(
            email=current_user.email,
            name=current_user.full_name or current_user.email,
            facility_name=request.facilityName,
            metadata={
                'user_id': str(current_user.id),
                'signup_date': str(datetime.now())
            }
        )
        
        # Create facility record
        facility = Facility(
            facility_name=request.facilityName,
            facility_address=request.facilityAddress,
            facility_city=request.facilityCity,
            facility_state=request.facilityState,
            facility_zip=request.facilityZip,
            facility_phone=request.facilityPhone,
            facility_email=request.facilityEmail,
            admin_user_id=current_user.id,
            stripe_customer_id=customer.id,
            is_active=True
        )
        db.add(facility)
        db.flush()  # Get facility ID
        
        # Create Stripe subscription
        stripe_subscription = stripe_service.create_subscription(
            customer_id=customer.id,
            facility_id=facility.id,
            seat_count=1,
            trial_days=request.trialDays
        )
        
        # Create local subscription record
        subscription = Subscription(
            stripe_subscription_id=stripe_subscription.id,
            stripe_customer_id=customer.id,
            facility_id=facility.id,
            status=stripe_subscription.status,
            current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
            seat_count=1,
            total_amount=stripe_service.BASE_PRICE
        )
        
        if stripe_subscription.trial_end:
            subscription.trial_end = datetime.fromtimestamp(stripe_subscription.trial_end)
        
        db.add(subscription)
        
        # Update user as facility admin with Pro status
        current_user.facility_id = facility.id
        current_user.subscription_status = 'pro'
        current_user.user_role = UserRole.FACILITY_ADMIN
        
        # Update facility with subscription ID
        facility.subscription_id = stripe_subscription.id
        
        db.commit()
        
        # Get client secret for payment
        client_secret = None
        if stripe_subscription.latest_invoice and stripe_subscription.latest_invoice.payment_intent:
            client_secret = stripe_subscription.latest_invoice.payment_intent.client_secret
        
        return {
            "success": True,
            "subscriptionId": stripe_subscription.id,
            "clientSecret": client_secret,
            "facilityId": facility.id,
            "trialEnd": subscription.trial_end.isoformat() if subscription.trial_end else None
        }
        
    except stripe.error.StripeError as e:
        db.rollback()
        logger.error(f"Stripe error creating subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")


@router.get("/subscription-status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current subscription status for the user's facility."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    
    # Get current subscription
    subscription = db.query(Subscription).filter(
        Subscription.facility_id == facility.id
    ).order_by(desc(Subscription.created_at)).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    return SubscriptionStatusResponse(
        id=subscription.id,
        status=subscription.status,
        currentPeriodStart=int(subscription.current_period_start.timestamp()),
        currentPeriodEnd=int(subscription.current_period_end.timestamp()),
        seatCount=subscription.seat_count,
        totalAmount=str(subscription.total_amount),
        trialEnd=int(subscription.trial_end.timestamp()) if subscription.trial_end else None,
        cancelAtPeriodEnd=subscription.cancel_at_period_end
    )


@router.post("/update-subscription-seats")
async def update_subscription_seats(
    request: SeatUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update subscription seat count."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    
    # Get current subscription
    subscription = db.query(Subscription).filter(
        Subscription.facility_id == facility.id
    ).order_by(desc(Subscription.created_at)).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    try:
        # Update subscription through Stripe
        stripe_service = StripeService()
        updated_subscription = stripe_service.update_subscription_seats(
            subscription.stripe_subscription_id,
            request.seat_count
        )
        
        # Update local subscription record
        subscription.seat_count = request.seat_count
        subscription.total_amount = stripe_service.calculate_subscription_amount(request.seat_count)
        db.commit()
        
        return {
            "message": "Subscription updated successfully",
            "seat_count": request.seat_count,
            "total_amount": str(subscription.total_amount)
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error updating subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update subscription")


@router.post("/cancel-subscription")
async def cancel_subscription(
    at_period_end: bool = True,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel facility subscription."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    if not facility.subscriptions:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    subscription = facility.subscriptions[0]
    
    try:
        stripe_service = StripeService()
        
        # Cancel Stripe subscription
        cancelled_subscription = stripe_service.cancel_subscription(
            subscription.stripe_subscription_id,
            at_period_end=at_period_end,
            reason=reason
        )
        
        # Handle immediate vs period-end cancellation differently
        if at_period_end:
            # Just mark for cancellation at period end
            subscription.cancel_at_period_end = True
            if reason:
                subscription.cancellation_reason = reason
            db.commit()
            
            return {
                "success": True,
                "cancelledAt": cancelled_subscription.canceled_at,
                "atPeriodEnd": at_period_end,
                "message": "Subscription will be cancelled at the end of the current billing period"
            }
        else:
            # Immediate cancellation - perform downgrade
            success = SubscriptionDowngradeService.immediate_downgrade(
                subscription,
                db,
                reason or "User requested immediate cancellation"
            )
            
            if success:
                return {
                    "success": True,
                    "cancelledAt": cancelled_subscription.canceled_at,
                    "atPeriodEnd": at_period_end,
                    "message": "Subscription cancelled immediately. Account downgraded to free tier."
                }
            else:
                # Fallback to old behavior
                subscription.status = SubscriptionStatus.CANCELLED.value
                subscription.cancelled_at = datetime.now()
                facility.is_active = False
                if reason:
                    subscription.cancellation_reason = reason
                db.commit()
                
                return {
                    "success": True,
                    "cancelledAt": cancelled_subscription.canceled_at,
                    "atPeriodEnd": at_period_end,
                    "message": "Subscription cancelled immediately"
                }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment methods for facility."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    
    try:
        stripe_service = StripeService()
        payment_methods = stripe_service.get_payment_methods(facility.stripe_customer_id)
        
        return [
            PaymentMethodResponse(
                id=pm.id,
                brand=pm.card.brand,
                last4=pm.card.last4,
                expMonth=pm.card.exp_month,
                expYear=pm.card.exp_year,
                isDefault=False  # You'd need to check customer.default_payment_method
            )
            for pm in payment_methods
        ]
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error getting payment methods: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")


@router.post("/setup-intent")
async def create_setup_intent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create setup intent for adding payment methods."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    
    try:
        stripe_service = StripeService()
        setup_intent = stripe_service.create_setup_intent(facility.stripe_customer_id)
        
        return {
            "clientSecret": setup_intent.client_secret
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating setup intent: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")


@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing history for facility."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    
    try:
        stripe_service = StripeService()
        invoices = stripe_service.get_invoices(facility.stripe_customer_id, limit)
        
        return [
            InvoiceResponse(
                id=invoice.id,
                amountPaid=invoice.amount_paid,
                currency=invoice.currency,
                status=invoice.status,
                created=invoice.created,
                pdfUrl=invoice.invoice_pdf
            )
            for invoice in invoices
        ]
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error getting invoices: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")


@router.get("/subscription-status-detailed")
async def get_detailed_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed subscription status including grace period information."""
    try:
        from app.services.subscription_downgrade_service import SubscriptionDowngradeService
        
        # Get comprehensive subscription status
        status_info = SubscriptionDowngradeService.check_subscription_status(current_user, db)
        
        # Add user tier information
        status_info.update({
            "user_id": current_user.id,
            "user_tier": current_user.subscription_status or "free",
            "pending_downgrade": getattr(current_user, 'pending_downgrade', False),
            "downgrade_after": current_user.downgrade_after.isoformat() if getattr(current_user, 'downgrade_after', None) else None
        })
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting detailed subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get subscription status")


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe Checkout Session for subscription management."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    
    # Get current subscription
    subscription = db.query(Subscription).filter(
        Subscription.facility_id == facility.id
    ).order_by(desc(Subscription.created_at)).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    try:
        # Handle seat upgrade specifically
        if request.type == "seat_upgrade" and request.additional_seats:
            # Calculate new seat count
            new_seat_count = subscription.seat_count + request.additional_seats
            
            # Create checkout session for seat upgrade
            session = stripe.checkout.Session.create(
                customer=facility.stripe_customer_id,
                mode='payment',  # One-time payment for seat upgrade
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Additional Seat{"s" if request.additional_seats > 1 else ""} ({request.additional_seats})',
                            'description': f'Add {request.additional_seats} additional seat{"s" if request.additional_seats > 1 else ""} to your subscription'
                        },
                        'unit_amount': 2000,  # $20.00 in cents
                    },
                    'quantity': request.additional_seats
                }],
                success_url=request.success_url,
                cancel_url=request.cancel_url,
                metadata={
                    'facility_id': str(facility.id),
                    'seat_upgrade': 'true',
                    'additional_seats': str(request.additional_seats),
                    'new_seat_count': str(new_seat_count),
                    'user_id': str(current_user.id),
                    'subscription_id': subscription.stripe_subscription_id
                },
                billing_address_collection='required'
            )
            
            return {
                "checkout_url": session.url,
                "session_id": session.id
            }
        
        # Check if this is a seat upgrade (increasing seat count) - legacy support
        if request.seat_count and request.seat_count > subscription.seat_count:
            additional_seats = request.seat_count - subscription.seat_count
            
            # Create checkout session for seat upgrade
            session = stripe.checkout.Session.create(
                customer=facility.stripe_customer_id,
                mode='payment',  # One-time payment for seat upgrade
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Additional Seat{"s" if additional_seats > 1 else ""} ({additional_seats})',
                            'description': f'Add {additional_seats} additional seat{"s" if additional_seats > 1 else ""} to your subscription'
                        },
                        'unit_amount': 2000,  # $20.00 in cents
                    },
                    'quantity': additional_seats
                }],
                success_url=request.success_url,
                cancel_url=request.cancel_url,
                metadata={
                    'facility_id': str(facility.id),
                    'seat_upgrade': 'true',
                    'additional_seats': str(additional_seats),
                    'new_seat_count': str(request.seat_count),
                    'user_id': str(current_user.id),
                    'subscription_id': subscription.stripe_subscription_id
                },
                billing_address_collection='required'
            )
            
            return {
                "checkout_url": session.url,
                "session_id": session.id
            }
        
        # For other cases (downgrades or new subscriptions), create checkout session
        # Build line items based on seat count
        line_items = []
        
        # Base subscription (always 1)
        line_items.append({
            'price': settings.STRIPE_PRO_BASE_PRICE_ID,
            'quantity': 1
        })
        
        # Additional seats if needed
        seat_count = request.seat_count or subscription.seat_count
        if seat_count > 1:
            additional_seats = seat_count - 1
            line_items.append({
                'price': settings.STRIPE_USER_SEAT_PRICE_ID,
                'quantity': additional_seats
            })
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=facility.stripe_customer_id,
            mode=request.mode,
            line_items=line_items,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                'facility_id': str(facility.id),
                'seat_count': str(seat_count),
                'user_id': str(current_user.id)
            },
            billing_address_collection='required'
        )
        
        return {
            "checkout_url": session.url,
            "session_id": session.id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/create-customer-portal")
async def create_customer_portal_session(
    return_url: str = Query(..., description="URL to return to after customer portal session"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe Customer Portal session for subscription management."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    if not facility.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found for this facility")
    
    try:
        # Retrieve the user's most recent subscription from the database
        subscription = db.query(Subscription).filter(
            Subscription.facility_id == facility.id
        ).order_by(desc(Subscription.created_at)).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="No subscription found")
        
        # Create Stripe billing portal session
        portal_config_id = await get_or_create_portal_configuration()
        
        session = stripe.billing_portal.Session.create(
            customer=facility.stripe_customer_id,
            return_url=return_url,
            configuration=portal_config_id
        )
        return {"portal_url": session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating customer portal session: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating customer portal session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.post("/create-add-member-portal")
async def create_add_member_portal_session(
    return_url: str = Query(..., description="URL to return to after portal session"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe Customer Portal session specifically for adding team members (seat upgrades)."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    if not facility.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found for this facility")
    
    try:
        # Use specialized portal configuration for adding team members
        portal_config_id = await get_or_create_add_member_portal_configuration()
        
        session = stripe.billing_portal.Session.create(
            customer=facility.stripe_customer_id,
            return_url=return_url,
            configuration=portal_config_id
        )
        return {"portal_url": session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in add member portal session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"{str(e)}")
    except Exception as e:
        logger.error(f"Error in add member portal session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.post("/reduce-seats")
async def reduce_subscription_seats(
    seats_to_remove: int = Query(..., ge=1, description="Number of seats to remove"),
    return_url: str = Query(..., description="URL to return to after checkout"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a checkout session to reduce subscription seats."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    if not facility.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found for this facility")
    
    # Get current subscription
    subscription = db.query(Subscription).filter(
        Subscription.facility_id == facility.id
    ).order_by(desc(Subscription.created_at)).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    # Validate seat reduction
    new_seat_count = subscription.seat_count - seats_to_remove
    if new_seat_count < 1:
        raise HTTPException(
            status_code=400, 
            detail="Cannot reduce seats below 1. Facility must have at least 1 seat."
        )
    
    # Check if facility has enough removable users
    current_users = facility.current_user_count
    if current_users > new_seat_count:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reduce to {new_seat_count} seats. You currently have {current_users} users. Please remove users first."
        )
    
    try:
        # Calculate the new subscription amount
        stripe_service = StripeService()
        new_total_amount = stripe_service.calculate_subscription_amount(new_seat_count)
        
        # Create a checkout session for the reduced subscription
        # This will be a subscription modification, not a one-time payment
        line_items = []
        
        # Base subscription (always 1)
        line_items.append({
            'price': settings.STRIPE_PRO_BASE_PRICE_ID,
            'quantity': 1
        })
        
        # Additional seats if needed
        if new_seat_count > 1:
            additional_seats = new_seat_count - 1
            line_items.append({
                'price': settings.STRIPE_USER_SEAT_PRICE_ID,
                'quantity': additional_seats
            })
        
        # Create checkout session for subscription modification
        session = stripe.checkout.Session.create(
            customer=facility.stripe_customer_id,
            mode='subscription',
            line_items=line_items,
            success_url=f"{return_url}?seat_reduction_success=true",
            cancel_url=f"{return_url}?seat_reduction_cancelled=true",
            metadata={
                'facility_id': str(facility.id),
                'seat_reduction': 'true',
                'old_seat_count': str(subscription.seat_count),
                'new_seat_count': str(new_seat_count),
                'seats_removed': str(seats_to_remove),
                'user_id': str(current_user.id),
                'subscription_id': subscription.stripe_subscription_id
            },
            subscription_data={
                'metadata': {
                    'facility_id': str(facility.id),
                    'seat_count': str(new_seat_count)
                }
            }
        )
        
        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "old_seat_count": subscription.seat_count,
            "new_seat_count": new_seat_count,
            "monthly_savings": float((subscription.total_amount - new_total_amount))
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating seat reduction checkout: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating seat reduction checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create seat reduction checkout")


# Keep the old endpoint for backward compatibility but mark it as deprecated
@router.post("/create-remove-member-portal")
async def create_remove_member_portal_session(
    return_url: str = Query(..., description="URL to return to after portal session"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe Customer Portal session specifically for removing team members (seat downgrades).
    
    DEPRECATED: Use /reduce-seats endpoint instead for proper seat management.
    """
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    if not facility.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found for this facility")
    
    # Get current subscription to check minimum seat requirements
    subscription = db.query(Subscription).filter(
        Subscription.facility_id == facility.id
    ).order_by(desc(Subscription.created_at)).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    # Check if facility has more than 1 seat (can't go below 1)
    if subscription.seat_count <= 1:
        raise HTTPException(
            status_code=400, 
            detail="Cannot remove team members. Facility must have at least 1 seat."
        )
    
    try:
        # Use specialized portal configuration for removing team members
        portal_config_id = await get_or_create_remove_member_portal_configuration()
        
        session = stripe.billing_portal.Session.create(
            customer=facility.stripe_customer_id,
            return_url=return_url,
            configuration=portal_config_id
        )
        return {"portal_url": session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in remove member portal session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"{str(e)}")
    except Exception as e:
        logger.error(f"Error in remove member portal session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.post("/verify-payment")
async def verify_payment(
    session_id: str = Query(..., description="Stripe checkout session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify a Stripe Checkout Session and process the payment.

    This replaces the previous `verify-checkout-session` endpoint and merges
    the functionality previously handled in the webhook backup. It directly
    retrieves the session from Stripe and delegates processing to the central
    `PaymentProcessorService`.
    """
    try:
        # Retrieve the checkout session directly from Stripe for maximum reliability
        session = stripe.checkout.Session.retrieve(session_id)
        if not session or session.get('payment_status') != 'paid':
            raise HTTPException(status_code=400, detail="Checkout session not paid or not found")

        result = PaymentProcessorService.handle_checkout_session_completed(session, db)
        
        if result.get('status') == 'error':
            # Check for specific error codes to return structured responses
            error_code = result.get('error_code')
            if error_code == 'subscription_canceled':
                return {
                    "success": False,
                    "error_code": error_code,
                    "message": result.get('message', 'Subscription canceled'),
                    "action_required": result.get('action_required', 'resubscribe')
                }
            elif error_code == 'session_for_canceled_subscription':
                return {
                    "success": False,
                    "error_code": error_code,
                    "message": result.get('message', 'Session for canceled subscription'),
                    "action_required": result.get('action_required', 'restart_seat_upgrade')
                }
            else:
                raise HTTPException(status_code=500, detail=result.get('message', 'Payment processing failed'))

        return {"success": True, **result}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error verifying checkout session: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except HTTPException:
        # Pass through
        raise
    except Exception as e:
        logger.error(f"Error verifying checkout session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify checkout session")


@router.post("/reduce-seats-direct")
async def reduce_subscription_seats_direct(
    seats_to_remove: int = Query(..., ge=1, description="Number of seats to remove"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Directly reduce subscription seats without requiring checkout."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    if not facility.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found for this facility")
    
    # Get current subscription
    subscription = db.query(Subscription).filter(
        Subscription.facility_id == facility.id
    ).order_by(desc(Subscription.created_at)).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    # Validate seat reduction
    new_seat_count = subscription.seat_count - seats_to_remove
    if new_seat_count < 1:
        raise HTTPException(
            status_code=400, 
            detail="Cannot reduce seats below 1. Facility must have at least 1 seat."
        )
    
    # Check if facility has enough removable users (including admin in count)
    current_users = facility.current_user_count  # This includes admin
    if current_users > new_seat_count:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reduce to {new_seat_count} seats. You currently have {current_users} users (including admin). Please remove team members first."
        )
    
    try:
        # Update Stripe subscription directly
        from app.services.stripe_service import StripeService
        stripe_service = StripeService()
        
        # Update the subscription in Stripe
        stripe_service.update_subscription_seats(
            subscription.stripe_subscription_id,
            new_seat_count
        )
        
        # Calculate the new subscription amount
        new_total_amount = stripe_service.calculate_subscription_amount(new_seat_count)
        
        # Update local subscription record
        subscription.seat_count = new_seat_count
        subscription.total_amount = new_total_amount
        db.commit()
        
        logger.info(f"Successfully reduced facility {facility.id} from {subscription.seat_count + seats_to_remove} to {new_seat_count} seats")
        
        return {
            "success": True,
            "message": f"Successfully reduced subscription by {seats_to_remove} seat{'s' if seats_to_remove > 1 else ''}",
            "old_seat_count": subscription.seat_count + seats_to_remove,
            "new_seat_count": new_seat_count,
            "monthly_savings": float((subscription.seat_count + seats_to_remove - new_seat_count) * 20),
            "new_monthly_cost": float(new_total_amount)
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error reducing subscription seats: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error(f"Error reducing subscription seats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reduce subscription seats") 


@router.post("/add-seats-direct")
async def add_subscription_seats_direct(
    seats_to_add: int = Query(..., ge=1, description="Number of seats to add"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Directly add subscription seats without requiring checkout."""
    if not current_user.is_pro_user or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Pro subscription required")
    
    facility = current_user.administered_facility
    if not facility.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found for this facility")
    
    # Get current subscription
    subscription = db.query(Subscription).filter(
        Subscription.facility_id == facility.id
    ).order_by(desc(Subscription.created_at)).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    # Basic validation
    if seats_to_add <= 0:
        raise HTTPException(
            status_code=400, 
            detail="Number of seats to add must be greater than 0."
        )
    
    new_seat_count = subscription.seat_count + seats_to_add
    
    try:
        # Update Stripe subscription directly
        from app.services.stripe_service import StripeService
        stripe_service = StripeService()
        
        # Update the subscription in Stripe
        stripe_service.update_subscription_seats(
            subscription.stripe_subscription_id,
            new_seat_count
        )
        
        # Calculate the new subscription amount
        new_total_amount = stripe_service.calculate_subscription_amount(new_seat_count)
        
        # Update local subscription record
        old_seat_count = subscription.seat_count
        subscription.seat_count = new_seat_count
        subscription.total_amount = new_total_amount
        db.commit()
        
        logger.info(f"Successfully added {seats_to_add} seats to facility {facility.id} (from {old_seat_count} to {new_seat_count})")
        
        return {
            "success": True,
            "message": f"Successfully added {seats_to_add} seat{'s' if seats_to_add > 1 else ''}",
            "old_seat_count": old_seat_count,
            "new_seat_count": new_seat_count,
            "additional_monthly_cost": float(seats_to_add * 20),
            "new_monthly_cost": float(new_total_amount)
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error adding subscription seats: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error(f"Error adding subscription seats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add subscription seats") 