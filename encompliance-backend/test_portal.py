import stripe
from app.core.config import get_settings

settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

# Test creating a portal session with the existing config
try:
    session = stripe.billing_portal.Session.create(
        customer='cus_test_customer',  # This will fail but we just want to test the config
        configuration='bpc_1RWnR9RQfRSwy2AavfrsVyAz',
        return_url='http://localhost:5174/facility'
    )
    print('Portal session created successfully')
except stripe.error.InvalidRequestError as e:
    if 'No such customer' in str(e):
        print('Portal configuration is valid (customer error expected)')
    else:
        print(f'Unexpected error: {e}')
except Exception as e:
    print(f'Error: {e}') 