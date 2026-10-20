"""
Cleanup Tasks Module

This module provides background tasks for maintaining database cleanliness
by removing stale or temporary data that is no longer needed.

Key functionalities:
- Removal of expired blacklisted tokens
- Removal of unverified user accounts older than a certain threshold
- Removal of expired signup sessions

Educational Note: Implements automated cleanup patterns to maintain database
hygiene and prevent accumulation of stale temporary data.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.token import BlacklistedToken
from app.models.signup_session import SignupSession
from app.database import get_db
from app.api.routes.auth import delete_user_account
from app.services.signup_session_service import SignupSessionService
from app.services.storage_meter_service import StorageMeterService

logger = logging.getLogger(__name__)

async def cleanup_expired_tokens(db: Session):
    """
    Remove expired tokens from the blacklist to prevent it from growing indefinitely.
    """
    try:
        # Current time
        now = datetime.utcnow()
        
        # Delete tokens that have expired
        result = db.query(BlacklistedToken).filter(
            BlacklistedToken.expires_at < now
        ).delete()
        
        # Commit the changes
        db.commit()
        
        if result > 0:
            logger.info(f"Cleaned up {result} expired blacklisted tokens")
        
        return result
    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}")
        db.rollback()
        return 0

async def cleanup_expired_signup_sessions(db: Session):
    """
    Remove expired signup sessions to prevent accumulation of temporary data.
    
    Args:
        db: Database session
    
    Returns:
        int: Number of sessions removed
    """
    try:
        sessions_removed = SignupSessionService.cleanup_expired_sessions(db)
        
        if sessions_removed > 0:
            logger.info(f"Cleaned up {sessions_removed} expired signup sessions")
        
        return sessions_removed
    except Exception as e:
        logger.error(f"Error cleaning up expired signup sessions: {e}")
        return 0

async def cleanup_unverified_accounts(db: Session, days_threshold: int = 7):
    """
    Remove unverified user accounts that are older than the specified threshold.
    
    Args:
        db: Database session
        days_threshold: Number of days after which unverified accounts are removed
                       (default: 7 days)
    
    Returns:
        int: Number of accounts removed
    """
    try:
        # Calculate the cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        # Find unverified accounts older than the threshold
        accounts = db.query(User).filter(
            User.email_verified == False,
            User.created_at < cutoff_date
        ).all()
        
        count = len(accounts)
        success_count = 0
        
        if count > 0:
            logger.info(f"Found {count} unverified accounts older than {days_threshold} days")
            
            for account in accounts:
                logger.info(f"Removing unverified account: {account.email} (created: {account.created_at})")
                # Use the helper function for thorough cleanup
                if await delete_user_account(db, account):
                    success_count += 1
                else:
                    logger.warning(f"Failed to properly remove account {account.id} ({account.email})")
            
            logger.info(f"Successfully removed {success_count} of {count} unverified accounts")
        
        return success_count
    except Exception as e:
        logger.error(f"Error cleaning up unverified accounts: {e}")
        db.rollback()
        return 0

async def run_daily_cleanup():
    """
    Run all cleanup tasks. Should be scheduled to run once per day.
    """
    db = next(get_db())
    try:
        logger.info("Starting daily cleanup tasks")
        
        # Clean up expired tokens
        tokens_removed = await cleanup_expired_tokens(db)
        logger.info(f"Removed {tokens_removed} expired tokens")
        
        # Clean up expired signup sessions
        sessions_removed = await cleanup_expired_signup_sessions(db)
        logger.info(f"Removed {sessions_removed} expired signup sessions")
        
        # Clean up unverified accounts
        accounts_removed = await cleanup_unverified_accounts(db)
        logger.info(f"Removed {accounts_removed} unverified accounts")

        # Recalculate storage meters for accurate billing
        meters_updated = StorageMeterService.recalculate_all_facilities(db)
        logger.info(f"Rebuilt storage meters for {meters_updated} facilities")
        
        logger.info("Daily cleanup tasks completed successfully")
    except Exception as e:
        logger.error(f"Error during daily cleanup: {e}")
    finally:
        db.close() 