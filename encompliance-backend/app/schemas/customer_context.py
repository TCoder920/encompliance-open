"""
Customer Context Schemas
------------------------
Schemas for customer context data displayed in support ticket views.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserContext(BaseModel):
    """User information for customer context."""
    id: int
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    facility_type: Optional[str] = None
    state: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool
    subscription_status: Optional[str] = None
    user_role: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class FacilityContext(BaseModel):
    """Facility information for customer context."""
    id: int
    facility_name: Optional[str] = None
    facility_address: Optional[str] = None
    facility_city: Optional[str] = None
    facility_state: Optional[str] = None
    facility_zip: Optional[str] = None
    facility_phone: Optional[str] = None
    facility_email: Optional[str] = None
    is_active: bool
    max_users: Optional[int] = None
    created_at: Optional[datetime] = None


class SubscriptionContext(BaseModel):
    """Subscription information for customer context."""
    id: Optional[int] = None
    status: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    seat_count: Optional[int] = None
    total_amount: Optional[str] = None
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool = False


class PaymentContext(BaseModel):
    """Recent payment information for customer context."""
    id: Optional[int] = None
    amount: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    description: Optional[str] = None


class CustomerContextOut(BaseModel):
    """Complete customer context for a support ticket."""
    user: Optional[UserContext] = None
    facility: Optional[FacilityContext] = None
    subscription: Optional[SubscriptionContext] = None
    recent_payments: List[PaymentContext] = []
    ticket_count: int = 0
    open_ticket_count: int = 0

    class Config:
        from_attributes = True

