"""
API Key Service
---------------

Centralizes creation, rotation, and verification of external API keys used by
MCP clients or other automation tools. Keys are hashed at rest, scoped to a
facility, and can enforce IP allowlists.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.api_key import APIKey, APIKeyStatus
from app.models.user import User


class APIKeyService:
    KEY_PREFIX = "enc"

    def create_api_key(
        self,
        db: Session,
        *,
        owner: User,
        label: str,
        scopes: List[str],
        expires_in_days: Optional[int],
        ip_allowlist: Optional[List[str]] = None,
    ) -> Tuple[APIKey, str]:
        """Generate and persist a new API key for the provided owner."""
        if not owner.is_facility_admin and not owner.is_superuser:
            raise PermissionError("Only facility admins can issue API keys.")

        if owner.subscription_status not in {"pro", "enterprise"}:
            raise PermissionError("An active paid subscription is required to create API keys.")

        facility_id = owner.facility_id or getattr(owner.administered_facility, "id", None)
        if facility_id is None:
            raise ValueError("API keys require an associated facility.")

        prefix = secrets.token_hex(4)
        secret = f"{self.KEY_PREFIX}_{prefix}_{secrets.token_urlsafe(32)}"
        key_hash = self._hash(secret)

        expires_at = (
            datetime.utcnow() + timedelta(days=expires_in_days)
            if expires_in_days
            else None
        )

        api_key = APIKey(
            label=label,
            prefix=prefix,
            key_hash=key_hash,
            scopes=scopes or ["tasks:read"],
            ip_allowlist=ip_allowlist,
            user_id=owner.id,
            created_by=owner.id,
            facility_id=facility_id,
            expires_at=expires_at,
        )

        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        return api_key, secret

    def list_api_keys(self, db: Session, *, owner: User) -> List[APIKey]:
        return (
            db.query(APIKey)
            .filter(APIKey.user_id == owner.id)
            .order_by(APIKey.created_at.desc())
            .all()
        )

    def revoke_api_key(self, db: Session, *, api_key: APIKey) -> APIKey:
        api_key.status = APIKeyStatus.REVOKED
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key

    def authenticate_raw_key(
        self,
        db: Session,
        *,
        raw_key: str,
        client_ip: Optional[str] = None,
    ) -> APIKey:
        """Validate a presented API key and return the DB entity if valid."""
        prefix = self._extract_prefix(raw_key)
        api_key = (
            db.query(APIKey)
            .filter(APIKey.prefix == prefix)
            .first()
        )

        if not api_key:
            raise ValueError("API key not found.")

        if api_key.key_hash != self._hash(raw_key):
            raise ValueError("Invalid API key.")

        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            api_key.status = APIKeyStatus.EXPIRED
            db.commit()
            raise ValueError("API key expired.")

        if api_key.status != APIKeyStatus.ACTIVE:
            raise PermissionError("API key is not active.")

        if api_key.ip_allowlist and client_ip not in api_key.ip_allowlist:
            raise PermissionError("API key restricted to approved IP addresses.")

        api_key.last_used_at = datetime.utcnow()
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key

    def _hash(self, secret: str) -> str:
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

    def _extract_prefix(self, secret: str) -> str:
        try:
            _, prefix, _ = secret.split("_", 2)
            return prefix
        except ValueError as exc:
            raise ValueError("Malformed API key.") from exc


api_key_service = APIKeyService()

