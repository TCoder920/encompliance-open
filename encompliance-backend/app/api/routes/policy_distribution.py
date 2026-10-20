"""
Policy Distribution Routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_facility_admin
from app.schemas.policy_distribution import PolicyDistributionRequest, PolicyDistributionResponse
from app.services.policy_distribution_service import PolicyDistributionService

router = APIRouter(prefix="/policy-distribution", tags=["policy-distribution"])


@router.post("/", response_model=PolicyDistributionResponse)
async def distribute_policy(
    payload: PolicyDistributionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_facility_admin),
):
    return PolicyDistributionService.distribute_policy(db, payload)

