"""
OTP Schema Module

This module defines Pydantic schemas for OTP (One-Time Password) operations.
It includes request and response models for OTP generation and verification.

Key functionalities:
- OTP request validation
- OTP verification validation
- OTP response formatting
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, Literal
import re

class OTPRequest(BaseModel):
    recipient: str = Field(..., description="Email address or phone number to send OTP to")
    method: Literal["email", "sms"] = Field(..., description="Method to send OTP")
    
    @validator('recipient')
    def validate_recipient(cls, v, values):
        method = values.get('method')
        if method == 'email':
            # Basic email validation - will be further validated as EmailStr
            if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
                raise ValueError("Invalid email format")
        elif method == 'sms':
            # Basic phone number validation
            if not re.match(r"^\+?[1-9]\d{1,14}$", v):
                raise ValueError("Invalid phone number format")
        return v

class EmailOTPRequest(OTPRequest):
    method: Literal["email"] = "email"
    recipient: EmailStr

class SMSOTPRequest(OTPRequest):
    method: Literal["sms"] = "sms"
    
class OTPVerify(BaseModel):
    recipient: str = Field(..., description="Email address or phone number the OTP was sent to")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    method: Literal["email", "sms"] = Field(..., description="Method used to send OTP")

class OTPResponse(BaseModel):
    success: bool
    message: str
    expires_in: Optional[int] = None  # Seconds until expiry

class OTPVerifyResponse(BaseModel):
    success: bool
    message: str
    verified: bool
    token: Optional[str] = None  # JWT token returned on successful verification 