import os
import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

# Create logger
logger = logging.getLogger(__name__)

def init_sentry(environment: str = "development") -> None:
    """
    Initialize Sentry for error monitoring
    
    Args:
        environment: The environment name (e.g., 'development', 'production')
    """
    # Get Sentry DSN from environment variable
    sentry_dsn = os.getenv("SENTRY_DSN")
    
    # Only initialize Sentry if DSN is provided and environment is production/staging
    if sentry_dsn and environment in ("production", "staging"):
        # Set up logging integration
        logging_integration = LoggingIntegration(
            level=logging.INFO,        # Capture INFO and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )
        
        # Initialize Sentry SDK
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            release=os.getenv("APP_VERSION", "0.1.0"),
            traces_sample_rate=0.5,  # Capture 50% of transactions for performance
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                logging_integration,
            ],
            # Set performance sampling
            _experiments={
                "profiles_sample_rate": 0.2,  # Capture 20% of transactions for profiling
            }
        )
        
        logger.info(f"Sentry initialized in {environment} environment")
    else:
        logger.info("Sentry disabled: DSN not provided or not in production/staging environment")

def capture_exception(exception: Exception, context: dict = None) -> None:
    """
    Capture an exception and send to Sentry
    
    Args:
        exception: The exception to capture
        context: Optional additional context data
    """
    if os.getenv("ENVIRONMENT") in ("production", "staging"):
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exception)
    
    # Always log locally
    logger.exception(f"Exception: {str(exception)}", extra=context or {}) 