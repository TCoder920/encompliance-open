"""
Analytics Routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_facility_admin
from app.schemas.analytics import CrossFacilityAnalytics
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/cross-facility", response_model=CrossFacilityAnalytics)
async def cross_facility_metrics(
    db: Session = Depends(get_db),
    current_user=Depends(require_facility_admin),
):
    return AnalyticsService.get_cross_facility_metrics(db)

