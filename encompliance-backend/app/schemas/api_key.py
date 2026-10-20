from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, conlist

from app.models.api_key import APIKeyStatus


class APIKeyBase(BaseModel):
    id: int
    label: str
    prefix: str
    scopes: List[str]
    status: APIKeyStatus
    ip_allowlist: Optional[List[str]] = None
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        use_enum_values = True


class APIKeyCreateRequest(BaseModel):
    label: str = Field(..., min_length=3, max_length=255)
    scopes: conlist(str, min_length=1) = Field(default_factory=lambda: ["tasks:read"])
    expires_in_days: Optional[int] = Field(default=90, ge=1, le=365)
    ip_allowlist: Optional[List[str]] = None


class APIKeyResponse(APIKeyBase):
    facility_id: Optional[int]


class APIKeyCreateResponse(APIKeyResponse):
    secret: str

