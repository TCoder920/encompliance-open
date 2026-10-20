"""
API Key Model
-------------

Stores hashed API keys that external automation clients (e.g., MCP tools)
use to call the EnCompliance backend. Keys are scoped to a facility and
user, include per-key IP allowlists, and can be revoked or expired.
"""

from datetime import datetime
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
    Enum,
)
from sqlalchemy.orm import relationship
from app.database import Base


class APIKeyStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(255), nullable=False)
    prefix = Column(String(16), unique=True, nullable=False)
    key_hash = Column(String(128), unique=True, nullable=False)
    scopes = Column(JSON, nullable=False, default=list)
    ip_allowlist = Column(JSON, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(APIKeyStatus), default=APIKeyStatus.ACTIVE, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    owner = relationship("User", foreign_keys=[user_id], back_populates="api_keys")
    creator = relationship("User", foreign_keys=[created_by])
    facility = relationship("Facility", foreign_keys=[facility_id], back_populates="api_keys")

    def is_active(self) -> bool:
        if self.status != APIKeyStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

