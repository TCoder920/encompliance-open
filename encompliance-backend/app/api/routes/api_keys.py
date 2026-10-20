from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_facility_admin
from app.database import get_db
from app.models.api_key import APIKey
from app.models.user import User
from app.schemas.api_key import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyResponse,
)
from app.services.api_key_service import api_key_service
from app.utils.rate_limiter import RateLimitExceeded, rate_limiter

router = APIRouter(tags=["api-keys"])


def _serialize(api_key: APIKey) -> APIKeyResponse:
    return APIKeyResponse(
        id=api_key.id,
        label=api_key.label,
        prefix=api_key.prefix,
        scopes=api_key.scopes or [],
        status=api_key.status,
        ip_allowlist=api_key.ip_allowlist,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        facility_id=api_key.facility_id,
    )


@router.post(
    "/api-keys",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_api_key(
    payload: APIKeyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    try:
        rate_limiter.hit(f"api-keys:create:{current_user.id}", limit=5, window_seconds=60)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    try:
        api_key, secret = api_key_service.create_api_key(
            db,
            owner=current_user,
            label=payload.label,
            scopes=payload.scopes,
            expires_in_days=payload.expires_in_days,
            ip_allowlist=payload.ip_allowlist,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return APIKeyCreateResponse(**_serialize(api_key).dict(), secret=secret)


@router.get("/api-keys", response_model=List[APIKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    try:
        rate_limiter.hit(f"api-keys:list:{current_user.id}", limit=20, window_seconds=60)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    keys = api_key_service.list_api_keys(db, owner=current_user)
    return [_serialize(key) for key in keys]


@router.delete(
    "/api-keys/{api_key_id}",
    response_model=APIKeyResponse,
    status_code=status.HTTP_200_OK,
)
def revoke_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    try:
        rate_limiter.hit(f"api-keys:revoke:{current_user.id}", limit=10, window_seconds=60)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == api_key_id, APIKey.user_id == current_user.id)
        .first()
    )
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found.")

    api_key = api_key_service.revoke_api_key(db, api_key=api_key)
    return _serialize(api_key)

