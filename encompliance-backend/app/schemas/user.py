"""
User Schemas Module

This module defines Pydantic schemas for user-related data validation and serialization
in the EnCompliance application.

Key functionalities:
- User registration and signup schemas
- User authentication schemas
- User profile data validation
- Token management schemas
- User update and modification schemas
- Multi-step signup process schemas
- Session-based signup schemas for temporary data storage
- Quick access links schemas for dashboard customization

Dependencies:
- pydantic: For data validation and serialization
- datetime: For timestamp handling

Educational Note: Implements session-based signup schemas to defer permanent
user creation until email verification, following data minimization principles.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, computed_field, model_validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum

# Import UserRole enum from the model to avoid conflicts
from app.models.user import UserRole

class QuickAccessLink(BaseModel):
    label: str = Field(..., min_length=1, max_length=50)
    path: str = Field(..., min_length=1, max_length=200)
    icon: Optional[str] = Field(None, max_length=50)  # Lucide icon name

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    operation_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    operation_name: str
    state: Optional[str] = None
    phone_number: Optional[str] = None
    facility_type: Optional[str] = None
    username: Optional[str] = None

    def get_username(self) -> str:
        # Use email as username if not provided
        return self.username or self.email.split('@')[0]

# Legacy schemas for backward compatibility
class UserSignupStep1(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    operation_name: str
    phone_number: Optional[str] = None
    username: Optional[str] = None

class UserSignupStep2(BaseModel):
    user_id: int
    state: str

class UserSignupStep3(BaseModel):
    user_id: int
    selected_facility_types: List[str]

# New session-based signup schemas
class SessionSignupStep1(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    operation_name: str
    phone_number: Optional[str] = None

class SessionSignupStep1Point5(BaseModel):
    """Role selection step for choosing user type"""
    session_token: str
    user_role: str = Field(..., description="Either 'facility_admin' or 'regular_user'")

class SessionSignupStep1Point75(BaseModel):
    """Tier selection step for choosing subscription level"""
    session_token: str
    selected_tier: str = Field(..., description="Either 'free' or 'pro'")

class SessionSignupStep2(BaseModel):
    session_token: str
    state: str

class SessionSignupStep3(BaseModel):
    session_token: str
    selected_facility_types: List[str]

class SessionSignupStep3FacilityAdmin(BaseModel):
    """Step 3 for facility administrators - facility creation"""
    session_token: str
    facility_name: str = Field(..., min_length=1, max_length=255)
    facility_address: Optional[str] = None
    facility_city: Optional[str] = None
    facility_state: Optional[str] = None
    facility_zip: Optional[str] = None
    facility_phone: Optional[str] = None
    facility_email: Optional[EmailStr] = None
    trial_days: int = Field(7, ge=0, le=30, description="Number of trial days")

class SessionSignupResponse(BaseModel):
    session_token: str
    step_completed: int
    expires_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Session-based OTP verification
class SessionOTPVerification(BaseModel):
    session_token: str
    otp_code: str

# Legacy OTP verification for backward compatibility
class OTPVerification(BaseModel):
    user_id: int
    otp_code: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    operation_name: Optional[str] = None
    facility_type: Optional[str] = None
    state: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    quick_access_links: Optional[List[QuickAccessLink]] = None

class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    operation_name: Optional[str] = None
    facility_type: Optional[str] = None
    state: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    subscription_status: str = "active"  # Default value
    subscription_end_date: Optional[str] = None
    user_role: Optional[Union[UserRole, str]] = UserRole.FREE_USER  # Add user_role field with flexible typing
    role_description: Optional[str] = None  # Add role_description field
    quick_access_links: Optional[List[QuickAccessLink]] = None
    
    @field_validator('user_role', mode='before')
    @classmethod
    def validate_user_role(cls, v):
        """Convert UserRole enum to string value for JSON serialization."""
        if isinstance(v, UserRole):
            return v.value
        return v
    
    @model_validator(mode='after')
    def validate_subscription_status_for_team_members(self):
        """Override subscription_status for team members to show 'team_member'."""
        if self.user_role == 'team_member':
            self.subscription_status = 'team_member'
        return self
    
    class Config:
        from_attributes = True
        json_encoders = {
            UserRole: lambda v: v.value if isinstance(v, UserRole) else v
        }

class UserInDBBase(UserBase):
    id: int
    is_active: bool
    email_verified: bool
    last_login: Optional[datetime] = None
    state: Optional[str] = None
    facility_type: Optional[str] = None
    openai_assistant_id: Optional[str] = None
    openai_vector_store_id: Optional[str] = None
    quick_access_links: Optional[List[QuickAccessLink]] = None

    class Config:
        orm_mode = True

class TeamMemberProfileUpdate(BaseModel):
    """Profile update request for team members (requires approval for name changes)"""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class TeamMemberNameChangeRequest(BaseModel):
    """Request for team member name change (requires admin approval)"""
    new_full_name: str = Field(..., min_length=1, max_length=255)
    reason: Optional[str] = None

class TeamMemberNameChangeResponse(BaseModel):
    """Response for name change request"""
    id: int
    user_id: int
    current_name: str
    requested_name: str
    reason: Optional[str]
    status: str  # pending, approved, rejected
    requested_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by_admin_id: Optional[int]
    
    class Config:
        from_attributes = True 