"""
Usage Billing Routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_active_user, require_facility_admin
from app.schemas.usage_billing import UsageSummary
from app.services.usage_billing_service import UsageBillingService

router = APIRouter(prefix="/usage-billing", tags=["usage-billing"])


@router.get("/summary", response_model=UsageSummary)
async def usage_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return UsageBillingService.get_usage_summary(db, current_user.id)


@router.get("/facility-summary")
async def facility_usage_summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_facility_admin),
):
    return UsageBillingService.get_facility_summary(db, current_user.facility_id)

