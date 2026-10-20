"""
Storage Meter API Routes

Provides facility administrators visibility into storage consumption and allows
manual recalculation/alert acknowledgement workflows required for tiered billing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.schemas.storage_meter import StorageUsageSummary
from app.services.storage_meter_service import StorageMeterService

router = APIRouter(prefix="/storage", tags=["storage"])


def _require_facility_admin(current_user):
    if not current_user.is_facility_admin or not current_user.facility_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Storage metrics are only available to facility administrators.",
        )


@router.get("/usage", response_model=StorageUsageSummary)
async def get_storage_usage(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Return the current billing-period usage for the facility administered by the caller.
    """
    _require_facility_admin(current_user)
    summary = StorageMeterService.get_usage_summary(db, current_user.facility_id)
    return summary


@router.post("/recalculate", response_model=StorageUsageSummary)
async def recalculate_storage_usage(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Force a rescan across all documents and images to realign meters.
    """
    _require_facility_admin(current_user)
    StorageMeterService.recalculate_facility_usage(db, current_user.facility_id)
    summary = StorageMeterService.get_usage_summary(db, current_user.facility_id)
    return summary

