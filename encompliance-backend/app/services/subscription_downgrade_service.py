"""
Subscription Downgrade Service Module

This module handles subscription downgrades, grace periods, and automatic downgrade logic
for the EnCompliance Pro Mode system. It manages the transition from paid to free tiers
while preserving user data.

Key functionalities:
- Grace period management (48 hours for payment failures)
- Immediate downgrade for user-initiated cancellations
- Data preservation during downgrades
- Feature access revocation
- Automatic downgrade processing

Dependencies:
- sqlalchemy: Database operations
- datetime: For timestamp handling and grace period calculations
- logging: For audit trail
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models import User, Facility, Subscription
from app.models.subscription import SubscriptionStatus
import logging

logger = logging.getLogger(__name__)


class SubscriptionDowngradeService:
    """Service class for handling subscription downgrades and grace periods."""
    
    GRACE_PERIOD_HOURS = 48  # 48 hour grace period for payment failures
    
    @classmethod
    def initiate_grace_period(cls, subscription: Subscription, db: Session) -> bool:
        """
        Start grace period for payment failed subscriptions.
        
        Args:
            subscription: The subscription that failed payment
            db: Database session
            
        Returns:
            bool: True if grace period was initiated successfully
        """
        try:
            # Set grace period end time
            grace_period_end = datetime.now() + timedelta(hours=cls.GRACE_PERIOD_HOURS)
            
            # Update subscription with grace period info
            subscription.status = SubscriptionStatus.PAST_DUE.value
            subscription.grace_period_end = grace_period_end
            
            # Keep facility active during grace period
            if subscription.facility:
                subscription.facility.is_active = True
                
            # Keep user as pro during grace period but flag for downgrade
            admin_user = subscription.facility.admin_user if subscription.facility else None
            if admin_user:
                admin_user.pending_downgrade = True
                admin_user.downgrade_after = grace_period_end
            
            db.commit()
            
            logger.info(f"Initiated grace period for subscription {subscription.id} until {grace_period_end}")
            return True
            
        except Exception as e:
            logger.error(f"Error initiating grace period for subscription {subscription.id}: {str(e)}")
            db.rollback()
            return False
    
    @classmethod
    def immediate_downgrade(cls, subscription: Subscription, db: Session, reason: str = "User cancelled") -> bool:
        """
        Immediately downgrade a subscription (for user-initiated cancellations).
        
        Args:
            subscription: The subscription to downgrade
            db: Database session
            reason: Reason for the downgrade
            
        Returns:
            bool: True if downgrade was successful
        """
        try:
            # Update subscription status
            subscription.status = SubscriptionStatus.CANCELLED.value
            subscription.cancelled_at = datetime.now()
            subscription.cancellation_reason = reason
            
            # Downgrade facility and users
            success = cls._perform_downgrade(subscription, db, reason)
            
            if success:
                db.commit()
                logger.info(f"Immediate downgrade completed for subscription {subscription.id}: {reason}")
            else:
                db.rollback()
                logger.error(f"Failed to complete immediate downgrade for subscription {subscription.id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error during immediate downgrade for subscription {subscription.id}: {str(e)}")
            db.rollback()
            return False
    
    @classmethod
    def process_expired_grace_periods(cls, db: Session) -> Dict[str, Any]:
        """
        Process all subscriptions with expired grace periods.
        
        Args:
            db: Database session
            
        Returns:
            Dict with processing results
        """
        try:
            current_time = datetime.now()
            
            # Find subscriptions with expired grace periods
            expired_subscriptions = db.query(Subscription).filter(
                Subscription.status == SubscriptionStatus.PAST_DUE.value,
                Subscription.grace_period_end <= current_time
            ).all()
            
            downgraded_count = 0
            failed_count = 0
            
            for subscription in expired_subscriptions:
                try:
                    success = cls._perform_downgrade(
                        subscription, 
                        db, 
                        "Grace period expired - payment not received"
                    )
                    
                    if success:
                        subscription.status = SubscriptionStatus.CANCELLED.value
                        subscription.cancelled_at = current_time
                        downgraded_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error downgrading subscription {subscription.id}: {str(e)}")
                    failed_count += 1
            
            if downgraded_count > 0 or failed_count > 0:
                db.commit()
            
            logger.info(f"Grace period processing complete: {downgraded_count} downgraded, {failed_count} failed")
            
            return {
                "processed": len(expired_subscriptions),
                "downgraded": downgraded_count,
                "failed": failed_count,
                "timestamp": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing expired grace periods: {str(e)}")
            db.rollback()
            return {
                "processed": 0,
                "downgraded": 0,
                "failed": 0,
                "error": str(e)
            }
    
    @classmethod
    def _perform_downgrade(cls, subscription: Subscription, db: Session, reason: str) -> bool:
        """
        Perform the actual downgrade process while preserving data.
        
        Args:
            subscription: The subscription to downgrade
            db: Database session
            reason: Reason for downgrade
            
        Returns:
            bool: True if downgrade was successful
        """
        try:
            facility = subscription.facility
            if not facility:
                logger.warning(f"No facility found for subscription {subscription.id}")
                return False
            
            # Preserve facility data but mark as inactive for Pro features
            facility.is_active = False
            
            # Downgrade admin user to free tier
            admin_user = facility.admin_user
            if admin_user:
                admin_user.subscription_status = "free"
                admin_user.pending_downgrade = False
                admin_user.downgrade_after = None
                
                # Preserve user data but remove Pro access
                logger.info(f"Downgraded user {admin_user.id} to free tier")
            
            # Handle facility users - downgrade all to free but keep in facility
            for user in facility.users:
                if user.id != admin_user.id:  # Don't double-process admin
                    user.subscription_status = "free"
                    logger.info(f"Downgraded facility user {user.id} to free tier")
            
            # Log the downgrade for audit trail
            logger.info(f"Downgraded facility {facility.id} and {len(facility.users)} users. Reason: {reason}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error performing downgrade for subscription {subscription.id}: {str(e)}")
            return False
    
    @classmethod
    def check_subscription_status(cls, user: User, db: Session) -> Dict[str, Any]:
        """
        Check user's subscription status and access level.
        
        Args:
            user: User to check
            db: Database session
            
        Returns:
            Dict with subscription status information
        """
        try:
            # Check if user has facility and subscription
            if not user.administered_facility:
                return {
                    "has_subscription": False,
                    "tier": "free",
                    "access_level": "free",
                    "grace_period": False
                }
            
            subscription = db.query(Subscription).filter(
                Subscription.facility_id == user.administered_facility.id
            ).order_by(Subscription.created_at.desc()).first()
            
            if not subscription:
                return {
                    "has_subscription": False,
                    "tier": "free", 
                    "access_level": "free",
                    "grace_period": False
                }
            
            # Check grace period status
            in_grace_period = (
                subscription.status == SubscriptionStatus.PAST_DUE.value and
                subscription.grace_period_end and
                subscription.grace_period_end > datetime.now()
            )
            
            # Determine access level
            if subscription.status in [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIALING.value]:
                access_level = "pro"
            elif in_grace_period:
                access_level = "pro"  # Keep Pro access during grace period
            else:
                access_level = "free"
            
            return {
                "has_subscription": True,
                "tier": user.subscription_status or "free",
                "access_level": access_level,
                "subscription_status": subscription.status,
                "grace_period": in_grace_period,
                "grace_period_end": subscription.grace_period_end.isoformat() if subscription.grace_period_end else None,
                "current_period_end": subscription.current_period_end.isoformat(),
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except Exception as e:
            logger.error(f"Error checking subscription status for user {user.id}: {str(e)}")
            return {
                "has_subscription": False,
                "tier": "free",
                "access_level": "free",
                "grace_period": False,
                "error": str(e)
            } 