from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_support_portal_db
from app.schemas.support_portal_account_schemas import (
    SupportPortalToken,
    SupportPortalAccountOut,
)
from app.auth.support_portal_auth_utils import (
    verify_password,
    create_access_token,
    get_support_account,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_support_account,
    ensure_account_roles,
)
from app.models.support_portal_account import SupportPortalAccount
from app.services.audit_service import log_support_audit_event

router = APIRouter()


@router.post("/token", response_model=SupportPortalToken)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_support_portal_db),
):
    """Issue an access token for support portal staff credentials."""
    account = get_support_account(db, username=form_data.username)
    if not account or not verify_password(form_data.password, account.hashed_password):
        await log_support_audit_event(
            db=db,
            support_account_id=account.id if account else None,
            action="login_failed",
            target=form_data.username,
            ip_address=request.client.host if request.client else None,
            details={"reason": "Invalid credentials"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    normalized_roles = ensure_account_roles(account, db=db)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": account.username, "roles": normalized_roles},
        expires_delta=access_token_expires,
    )

    await log_support_audit_event(
        db=db,
        support_account_id=account.id,
        action="login_success",
        target=account.username,
        ip_address=request.client.host if request.client else None,
    )

    return SupportPortalToken(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=SupportPortalAccountOut)
async def read_current_account(
    current_account: SupportPortalAccount = Depends(get_current_support_account),
):
    """Return the current authenticated support portal account."""
    return current_account