"""
Admin Schemas Module

This module defines Pydantic schemas for admin-related data validation and serialization
in the EnCompliance application.

Key functionalities:
- Admin user data validation
- Authentication token schemas
- Audit log data structures
- Role-based access control schemas
- Admin user creation and update schemas

Dependencies:
- pydantic: For data validation and serialization
- datetime: For timestamp handling
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional
import datetime

# --- Admin User Schemas ---
class AdminUserBase(BaseModel):
    username: str
    email: EmailStr
    roles: Optional[List[str]] = None

class AdminUserCreate(AdminUserBase):
    password: str

class AdminUserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    roles: Optional[List[str]] = None

class AdminUserInDB(AdminUserBase):
    id: int

    class Config:
        orm_mode = True # Compatibility with SQLAlchemy v1
        from_attributes = True # Compatibility with SQLAlchemy v2+

class AdminUserOut(AdminUserBase): # Exclude sensitive info like password hash
    id: int
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# --- Auth Schemas ---
class AdminToken(BaseModel):
    access_token: str
    token_type: str

class AdminTokenData(BaseModel):
    username: Optional[str] = None
    roles: Optional[List[str]] = None

class AdminLoginRequest(BaseModel):
    username: str
    password: str

# --- Audit Log Schemas ---
class AuditLogBase(BaseModel):
    action: str
    target: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[dict] = None
    internal_ip_address: Optional[str] = None

class AuditLogOut(AuditLogBase):
    id: int
    admin_user_id: int
    timestamp: datetime.datetime
    internal_ip_address: Optional[str] = None
    admin_username: Optional[str] = None # Add username for easier display

    class Config:
        orm_mode = True
        from_attributes = True

# Import datetime if not already imported at top level
import datetime 