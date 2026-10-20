"""
Support Portal Authentication Utilities
---------------------------------------
Encapsulates the hashing, JWT, and RBAC helpers used exclusively by the
customer support portal.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Set

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.database import get_support_portal_db
from app.models.support_portal_account import SupportPortalAccount
from app.schemas.support_portal_account_schemas import SupportPortalTokenData
from app.core.config import get_settings

settings = get_settings()

SECRET_KEY = settings.SUPPORT_PORTAL_SECRET_KEY
ALGORITHM = settings.SUPPORT_PORTAL_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.SUPPORT_PORTAL_ACCESS_TOKEN_EXPIRE_MINUTES

SUPPORT_ADMIN_ROLE = "support_admin"
SUPPORT_AGENT_ROLE = "support_agent"
LEGACY_ADMIN_ROLES = {"senior", "super_admin"}
LEGACY_AGENT_ROLES = {"mid", "beginner", "viewer"}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def normalize_role_names(role_list: Optional[List[str]]) -> List[str]:
    """
    Normalize a list of role strings into the canonical support_admin/support_agent set.
    Admins automatically inherit agent privileges.
    """
    normalized: Set[str] = set()

    if not role_list:
        normalized.add(SUPPORT_AGENT_ROLE)
        return list(normalized)

    for role in role_list:
        if not role:
            continue
        role_value = role.lower()

        if role_value in (SUPPORT_ADMIN_ROLE,):
            normalized.update({SUPPORT_ADMIN_ROLE, SUPPORT_AGENT_ROLE})
        elif role_value in (SUPPORT_AGENT_ROLE,):
            normalized.add(SUPPORT_AGENT_ROLE)
        elif role_value in LEGACY_ADMIN_ROLES:
            normalized.update({SUPPORT_ADMIN_ROLE, SUPPORT_AGENT_ROLE})
        elif role_value in LEGACY_AGENT_ROLES:
            normalized.add(SUPPORT_AGENT_ROLE)

    if not normalized:
        normalized.add(SUPPORT_AGENT_ROLE)
    return list(normalized)


def ensure_account_roles(account: SupportPortalAccount, db: Optional[Session] = None) -> List[str]:
    """
    Normalize and optionally persist role changes for a support account.
    """
    normalized = normalize_role_names(account.roles)
    if account.roles != normalized:
        account.roles = normalized
        if db:
            db.add(account)
            db.commit()
            db.refresh(account)
    else:
        # Ensure attribute set even if not persisted
        account.roles = normalized
    return normalized


def is_support_admin(account: SupportPortalAccount) -> bool:
    return SUPPORT_ADMIN_ROLE in normalize_role_names(account.roles)


def decode_access_token(token: str) -> SupportPortalTokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        roles: Optional[List[str]] = payload.get("roles")
        if username is None:
            raise credentials_exception
        return SupportPortalTokenData(username=username, roles=roles)
    except (JWTError, ValidationError):
        raise credentials_exception


def verify_token(token: str) -> Optional[int]:
    """
    Verify a JWT token and return the account ID.
    Used for WebSocket authentication.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            return None
        
        # Get account ID from database
        db = next(get_support_portal_db())
        try:
            account = get_support_account(db, username=username)
            return account.id if account else None
        finally:
            db.close()
    except (JWTError, ValidationError, Exception):
        return None


def get_support_account(db: Session, username: str) -> Optional[SupportPortalAccount]:
    return (
        db.query(SupportPortalAccount)
        .filter(SupportPortalAccount.username == username)
        .first()
    )


async def get_current_support_account(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_support_portal_db),
) -> SupportPortalAccount:
    token_data = decode_access_token(token)
    user = get_support_account(db, username=token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Support account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.roles = normalize_role_names(user.roles)
    return user


def require_role(required_roles: List[str]):
    # Allow legacy role names to be passed for backwards compatibility
    normalized_required: Set[str] = set()
    for role in required_roles:
        if role in LEGACY_ADMIN_ROLES or role == SUPPORT_ADMIN_ROLE:
            normalized_required.add(SUPPORT_ADMIN_ROLE)
        elif role in LEGACY_AGENT_ROLES or role == SUPPORT_AGENT_ROLE:
            normalized_required.add(SUPPORT_AGENT_ROLE)

    if not normalized_required:
        normalized_required.add(SUPPORT_AGENT_ROLE)

    async def role_checker(
        current_user: SupportPortalAccount = Depends(get_current_support_account),
    ) -> SupportPortalAccount:
        roles = set(normalize_role_names(current_user.roles))
        if not roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="Account has no assigned roles"
            )

        has_required_role = bool(roles & normalized_required)
        # support_admin inherits all agent-level privileges
        if not has_required_role and SUPPORT_ADMIN_ROLE in roles and SUPPORT_AGENT_ROLE in normalized_required:
            has_required_role = True

        if not has_required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {list(normalized_required)}",
            )
        return current_user

    return role_checker 