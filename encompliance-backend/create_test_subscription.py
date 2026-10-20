#!/usr/bin/env python3

from app.database import get_db
from app.models.facility import Facility
from app.models.subscription import Subscription
from app.services.stripe_service import StripeService
from datetime import datetime
import stripe

def create_test_subscription():
    db_gen = get_db()
    db = next(db_gen)

    try:
        # Get facility
        facility = db.query(Facility).filter(Facility.id == 1).first()
        print(f'Facility: {facility.facility_name}')
        
        # Create Stripe customer if not exists
        stripe_service = StripeService()
        if not facility.stripe_customer_id:
            customer = stripe_service.create_customer(
                email='test@example.com',
                name='Test User',
                facility_name=facility.facility_name
            )
            facility.stripe_customer_id = customer.id
            print(f'Created customer: {customer.id}')
        else:
            print(f'Using existing customer: {facility.stripe_customer_id}')
        
        # Create subscription
        stripe_subscription = stripe_service.create_subscription(
            customer_id=facility.stripe_customer_id,
            facility_id=facility.id,
            seat_count=1,
            trial_days=7
        )
        
        # Create local subscription record
        subscription = Subscription(
            stripe_subscription_id=stripe_subscription.id,
            stripe_customer_id=facility.stripe_customer_id,
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
        facility.subscription_id = stripe_subscription.id
        db.commit()
        
        print(f'Created subscription: {stripe_subscription.id}')
        print(f'Status: {stripe_subscription.status}')
        print(f'Trial end: {subscription.trial_end}')
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_subscription() 