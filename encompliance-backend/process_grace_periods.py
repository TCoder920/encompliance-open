#!/usr/bin/env python3
"""
Grace Period Processing Script

This script processes expired grace periods and downgrades users whose payment
was not received within the 48-hour grace period. It should be run periodically
as a background task (e.g., via cron job every hour).

Usage:
    python process_grace_periods.py

Dependencies:
    - app.database: Database connection
    - app.services.subscription_downgrade_service: Downgrade processing logic
"""

import sys
import os
import logging
from datetime import datetime

# Add the parent directory to the path so we can import our app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.services.subscription_downgrade_service import SubscriptionDowngradeService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('grace_period_processing.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main function to process expired grace periods."""
    logger.info("Starting grace period processing...")
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Process all expired grace periods
        result = SubscriptionDowngradeService.process_expired_grace_periods(db)
        
        logger.info(f"Grace period processing completed:")
        logger.info(f"  - Processed: {result.get('processed', 0)} subscriptions")
        logger.info(f"  - Downgraded: {result.get('downgraded', 0)} subscriptions")
        logger.info(f"  - Failed: {result.get('failed', 0)} subscriptions")
        
        if result.get('error'):
            logger.error(f"Error during processing: {result['error']}")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error during grace period processing: {str(e)}")
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 