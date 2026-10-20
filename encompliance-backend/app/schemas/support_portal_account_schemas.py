"""
Support Portal Account Schemas
------------------------------
Pydantic models for support portal accounts and auth payloads.
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional
import datetime


class SupportPortalAccountBase(BaseModel):
    username: str
    email: EmailStr
    roles: Optional[List[str]] = None


class SupportPortalAccountCreate(SupportPortalAccountBase):
    password: str


class SupportPortalAccountUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    roles: Optional[List[str]] = None


class SupportPortalAccountInDB(SupportPortalAccountBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True


class SupportPortalAccountOut(SupportPortalAccountBase):
    id: int
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


class SupportPortalToken(BaseModel):
    access_token: str
    token_type: str


class SupportPortalTokenData(BaseModel):
    username: Optional[str] = None
    roles: Optional[List[str]] = None


class SupportPortalLoginRequest(BaseModel):
    username: str
    password: str


class SupportPortalAuditLogBase(BaseModel):
    action: str
    target: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[dict] = None
    internal_ip_address: Optional[str] = None


class SupportPortalAuditLogOut(SupportPortalAuditLogBase):
    id: int
    support_account_id: int
    timestamp: datetime.datetime
    account_username: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True

