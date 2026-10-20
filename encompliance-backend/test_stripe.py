import stripe
from app.core.config import get_settings

settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

try:
    # Test retrieving price objects
    base_price = stripe.Price.retrieve(settings.STRIPE_PRO_BASE_PRICE_ID)
    seat_price = stripe.Price.retrieve(settings.STRIPE_USER_SEAT_PRICE_ID)
    print(f'Base price product: {base_price.product}')
    print(f'Seat price product: {seat_price.product}')
    
    # Test creating a simple portal configuration
    config = stripe.billing_portal.Configuration.create(
        business_profile={'headline': 'Test Portal'},
        features={
            'invoice_history': {'enabled': True},
            'payment_method_update': {'enabled': False},
            'subscription_cancel': {'enabled': False},
            'subscription_update': {
                'enabled': True,
                'default_allowed_updates': ['quantity'],
                'proration_behavior': 'always_invoice',
                'products': [
                    {
                        'product': base_price.product,
                        'prices': []
                    },
                    {
                        'product': seat_price.product,
                        'prices': [settings.STRIPE_USER_SEAT_PRICE_ID]
                    }
                ]
            }
        }
    )
    print(f'Portal config created: {config.id}')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc() 