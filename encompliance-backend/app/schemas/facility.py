"""
Facility Schemas Module

This module defines Pydantic schemas for facility management API operations.
It provides request/response models for facility, subscription, and invitation operations.

Key functionalities:
- Facility creation and management schemas
- Subscription billing and status schemas
- Invitation system schemas
- User permission and role schemas

Dependencies:
- pydantic: Data validation and serialization
- datetime: For timestamp handling
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


class FacilityBase(BaseModel):
    """Base facility schema with common fields."""
    facility_name: str = Field(..., min_length=1, max_length=255)
    facility_address: Optional[str] = None
    facility_city: Optional[str] = None
    facility_state: Optional[str] = None
    facility_zip: Optional[str] = None
    facility_phone: Optional[str] = None
    facility_email: Optional[EmailStr] = None


class FacilityCreate(FacilityBase):
    """Schema for creating a new facility."""
    max_users: Optional[int] = Field(None, ge=1)


class FacilityUpdate(BaseModel):
    """Schema for updating facility information."""
    facility_name: Optional[str] = Field(None, min_length=1, max_length=255)
    facility_address: Optional[str] = None
    facility_city: Optional[str] = None
    facility_state: Optional[str] = None
    facility_zip: Optional[str] = None
    facility_phone: Optional[str] = None
    facility_email: Optional[EmailStr] = None
    max_users: Optional[int] = Field(None, ge=1)


class FacilityResponse(FacilityBase):
    """Schema for facility response data."""
    id: int
    admin_user_id: int
    is_active: bool
    max_users: Optional[int] = None
    current_user_count: int
    available_seats: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Subscription Schemas
class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    seat_count: int = Field(..., ge=1)
    base_price: Decimal
    per_seat_price: Decimal
    total_amount: Decimal


class SubscriptionCreate(BaseModel):
    """Schema for creating a subscription."""
    facility_id: int
    seat_count: int = Field(1, ge=1)
    trial_days: int = Field(7, ge=0, le=30)


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response data."""
    id: int
    stripe_subscription_id: str
    stripe_customer_id: str
    facility_id: int
    status: str
    current_period_start: datetime
    current_period_end: datetime
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]
    cancel_at_period_end: bool
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Invitation Schemas
class InvitationCreate(BaseModel):
    """Schema for creating facility invitations."""
    email: Optional[EmailStr] = None
    expires_in_days: int = Field(7, ge=1, le=30)
    personal_message: Optional[str] = None
    role_description: Optional[str] = None


class InvitationResponse(BaseModel):
    """Schema for invitation response data."""
    id: int
    invitation_code: str
    email: Optional[str]
    facility_id: int
    created_by_user_id: int
    status: str
    used_by_user_id: Optional[int]
    used_at: Optional[datetime]
    expires_at: datetime
    personal_message: Optional[str]
    role_description: Optional[str]
    created_at: datetime
    is_valid: bool
    is_expired: bool
    days_until_expiry: int

    class Config:
        from_attributes = True


# User Management Schemas
class FacilityUserResponse(BaseModel):
    """Schema for facility user information."""
    id: int
    email: str
    username: Optional[str]
    full_name: Optional[str]
    subscription_status: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    role_description: Optional[str]

    class Config:
        from_attributes = True


class FacilityDashboardResponse(BaseModel):
    """Schema for facility overview data.
    
    Pro users manage exactly ONE facility. This response provides
    comprehensive overview data for their single facility.
    """
    facility: FacilityResponse
    subscription: Optional[SubscriptionResponse]
    users: List[FacilityUserResponse]
    active_invitations: List[InvitationResponse]
    training_completion_stats: Dict[str, Any]
    upcoming_events: List[Dict[str, Any]]


# Billing Schemas
class BillingHistoryResponse(BaseModel):
    """Schema for billing history."""
    invoice_id: str
    amount: int
    currency: str
    status: str
    date: datetime
    description: str
    pdf_url: Optional[str]


class PaymentMethodResponse(BaseModel):
    """Schema for payment method information."""
    id: str
    type: str
    card_brand: Optional[str]
    card_last4: Optional[str]
    card_exp_month: Optional[int]
    card_exp_year: Optional[int]
    is_default: bool


# Settings Schemas
class FacilitySettingsResponse(BaseModel):
    """Schema for facility settings."""
    facility: FacilityResponse
    subscription: Optional[SubscriptionResponse]
    payment_methods: List[PaymentMethodResponse]
    billing_history: List[BillingHistoryResponse]


class UserInviteRequest(BaseModel):
    """Schema for inviting users to facility."""
    email: EmailStr
    personal_message: Optional[str] = None
    role_description: Optional[str] = "Team Member"


class SeatCountUpdateRequest(BaseModel):
    """Schema for updating subscription seat count."""
    seat_count: int = Field(..., ge=1, description="New number of seats")


class SubscriptionCancelRequest(BaseModel):
    """Schema for cancelling subscription."""
    at_period_end: bool = Field(True, description="Cancel at end of billing period")
    cancellation_reason: Optional[str] = None 