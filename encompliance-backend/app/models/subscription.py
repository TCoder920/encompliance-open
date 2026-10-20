"""
Subscription Model Module

This module defines the Subscription database model for the EnCompliance Pro Mode billing system.
It tracks Stripe subscription details, billing cycles, and seat-based pricing.

Key functionalities:
- Stripe subscription integration and tracking
- Seat-based billing calculation ($50 base + $20 per additional user)
- Subscription status management (active/inactive/cancelled)
- Billing period tracking
- Payment history and invoice management
- Grace period management for payment failures

Dependencies:
- sqlalchemy: For database model definition
- datetime: For timestamp handling
- decimal: For precise monetary calculations
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
from decimal import Decimal
import enum


class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Stripe integration
    stripe_subscription_id = Column(String(255), nullable=False, unique=True, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    stripe_price_id = Column(String(255), nullable=True)  # Stripe price object ID
    
    # Facility relationship
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    
    # Subscription status
    status = Column(String(20), nullable=False, default=SubscriptionStatus.ACTIVE.value)
    
    # Billing periods
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Seat management
    seat_count = Column(Integer, nullable=False, default=1)  # Number of users
    base_price = Column(Numeric(10, 2), nullable=False, default=Decimal('50.00'))  # Base facility price
    per_seat_price = Column(Numeric(10, 2), nullable=False, default=Decimal('20.00'))  # Price per additional user
    total_amount = Column(Numeric(10, 2), nullable=False)  # Total subscription amount
    
    # Trial information
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    
    # Grace period management
    grace_period_end = Column(DateTime(timezone=True), nullable=True)  # End of grace period for failed payments
    
    # Cancellation information
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Payment information
    latest_invoice_id = Column(String(255), nullable=True)
    next_payment_attempt = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    facility = relationship("Facility", back_populates="subscriptions")
    
    @property
    def is_active(self):
        """Check if subscription is currently active."""
        return self.status == SubscriptionStatus.ACTIVE.value
    
    @property
    def is_trial(self):
        """Check if subscription is in trial period."""
        if not self.trial_end:
            return False
        return datetime.now() < self.trial_end
    
    @property
    def is_in_grace_period(self):
        """Check if subscription is in grace period."""
        if not self.grace_period_end:
            return False
        return (
            self.status == SubscriptionStatus.PAST_DUE.value and
            datetime.now() < self.grace_period_end
        )
    
    @property
    def effective_access_level(self):
        """Get the effective access level considering grace periods."""
        if self.status in [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIALING.value]:
            return "pro"
        elif self.is_in_grace_period:
            return "pro"  # Keep Pro access during grace period
        else:
            return "free"
    
    @property
    def days_until_renewal(self):
        """Get days until next billing cycle."""
        if self.current_period_end:
            delta = self.current_period_end - datetime.now()
            return max(0, delta.days)
        return 0
    
    @property
    def grace_period_hours_remaining(self):
        """Get hours remaining in grace period."""
        if not self.grace_period_end:
            return 0
        delta = self.grace_period_end - datetime.now()
        return max(0, int(delta.total_seconds() / 3600))
    
    def calculate_total_amount(self):
        """Calculate total subscription amount based on seat count."""
        if self.seat_count <= 1:
            return self.base_price
        additional_seats = self.seat_count - 1
        return self.base_price + (additional_seats * self.per_seat_price)
    
    def update_seat_count(self, new_seat_count):
        """Update seat count and recalculate total amount."""
        self.seat_count = max(1, new_seat_count)
        self.total_amount = self.calculate_total_amount()
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, facility_id={self.facility_id}, status={self.status}, seats={self.seat_count})>" 