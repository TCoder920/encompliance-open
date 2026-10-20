"""
WebAuthn Schemas Module
-------------------
This module defines Pydantic models for WebAuthn (passkey) operations in the EnCompliance system.
It includes schema definitions for:
- Registration options and responses
- Authentication options and responses
- Credential management
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional
from datetime import datetime


class RegistrationOptions(BaseModel):
    """Options for starting WebAuthn registration."""
    credential_name: Optional[str] = "My passkey"
    authenticator_attachment: Optional[str] = None  # "platform" or "cross-platform"


class RegistrationOptionsResponse(BaseModel):
    """Response containing WebAuthn registration options."""
    options: Dict[str, Any]
    user_id: int


class RegistrationVerification(BaseModel):
    """Verification data for WebAuthn registration."""
    credential: Dict[str, Any]
    credential_name: Optional[str] = "My passkey"
    device_type: Optional[str] = None


class CredentialResponse(BaseModel):
    """Response containing WebAuthn credential information."""
    id: int
    name: str
    created_at: datetime
    device_type: Optional[str] = None
    message: str


class AuthenticationOptions(BaseModel):
    """Options for starting WebAuthn authentication."""
    username: Optional[str] = None
    email: Optional[str] = None
    user_id: Optional[int] = None
    user_verification: Optional[str] = "preferred"
    
    class Config:
        # At least one identifier method must be provided
        @validator("user_id", pre=True, always=True)
        def check_identifiers(cls, v, values):
            username = values.get("username")
            email = values.get("email")
            if not any([username, email, v]):
                raise ValueError("At least one of username, email, or user_id must be provided")
            return v


class AuthenticationOptionsResponse(BaseModel):
    """Response containing WebAuthn authentication options."""
    options: Dict[str, Any]
    user_id: int


class AuthenticationVerification(BaseModel):
    """Verification data for WebAuthn authentication."""
    credential: Dict[str, Any]
    user_id: int


class CredentialSummary(BaseModel):
    """Summary of a WebAuthn credential."""
    id: int
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    device_type: Optional[str] = None 