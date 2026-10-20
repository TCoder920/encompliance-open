"""
Manager Control Routes
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.models.facility import Facility
from app.models.manager_override_request import ManagerOverrideStatus
from app.models.user import User
from app.schemas.manager_control import (
    ManagerOverrideRequestCreate,
    ManagerOverrideResolution,
    ManagerOverrideResponse,
)
from app.services.activity_audit_service import ActivityAuditService
from app.services.manager_control_service import ManagerControlService

router = APIRouter(prefix="/enterprise/manager", tags=["manager-controls"])


def _facility_context(current_user: User) -> Facility:
    if not current_user.is_facility_admin or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Facility admin access required.")
    return current_user.administered_facility


def _organization_facilities(db: Session, facility: Facility) -> List[int]:
    if not facility.organization_id:
        return [facility.id]
    facilities = db.query(Facility).filter(Facility.organization_id == facility.organization_id).all()
    return [f.id for f in facilities]


def _require_enterprise_manager(current_user: User, facility: Facility) -> None:
    if current_user.subscription_status != "enterprise":
        raise HTTPException(status_code=403, detail="Enterprise manager privileges required.")


@router.post("/requests", response_model=ManagerOverrideResponse)
async def submit_override_request(
    payload: ManagerOverrideRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility = _facility_context(current_user)
    request = ManagerControlService.submit_request(
        db,
        facility_id=facility.id,
        requested_by_user_id=current_user.id,
        action_type=payload.action_type,
        payload=payload.payload,
    )
    ActivityAuditService.log_event(
        db,
        actor_user_id=current_user.id,
        facility_id=facility.id,
        event_type="manager_override_requested",
        description=f"Requested override {payload.action_type}",
        metadata=payload.payload,
    )
    return ManagerOverrideResponse.from_orm(request)


@router.get("/requests", response_model=List[ManagerOverrideResponse])
async def list_override_requests(
    status_filter: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility = _facility_context(current_user)
    _require_enterprise_manager(current_user, facility)
    facility_ids = _organization_facilities(db, facility)
    requests = ManagerControlService.list_requests(db, organization_facility_ids=facility_ids, status=status_filter)
    return [ManagerOverrideResponse.from_orm(item) for item in requests]


@router.post("/requests/{request_id}/approve", response_model=ManagerOverrideResponse)
async def approve_override_request(
    request_id: int,
    payload: ManagerOverrideResolution,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility = _facility_context(current_user)
    _require_enterprise_manager(current_user, facility)
    request = ManagerControlService.approve_request(
        db,
        request_id=request_id,
        approver_id=current_user.id,
        notes=payload.resolution_notes,
    )
    ActivityAuditService.log_event(
        db,
        actor_user_id=current_user.id,
        facility_id=facility.id,
        event_type="manager_override_approved",
        description=f"Approved override request_id={request_id}",
        metadata={"notes": payload.resolution_notes},
    )
    return ManagerOverrideResponse.from_orm(request)


@router.post("/requests/{request_id}/reject", response_model=ManagerOverrideResponse)
async def reject_override_request(
    request_id: int,
    payload: ManagerOverrideResolution,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility = _facility_context(current_user)
    _require_enterprise_manager(current_user, facility)
    request = ManagerControlService.reject_request(
        db,
        request_id=request_id,
        approver_id=current_user.id,
        notes=payload.resolution_notes,
    )
    ActivityAuditService.log_event(
        db,
        actor_user_id=current_user.id,
        facility_id=facility.id,
        event_type="manager_override_rejected",
        description=f"Rejected override request_id={request_id}",
        metadata={"notes": payload.resolution_notes},
    )
    return ManagerOverrideResponse.from_orm(request)

