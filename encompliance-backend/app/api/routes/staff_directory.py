"""
Enterprise Staff Directory Routes

Provides organization-wide staff roster visibility, facility assignments, and transfer workflows.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.models.facility import Facility
from app.models.staff_directory import StaffFacilityAssignment, StaffTransferRequest
from app.models.staff_member import StaffMember
from app.models.user import User
from app.schemas.staff_directory import (
    AssignStaffPayload,
    StaffDirectoryEntry,
    StaffDirectoryListResponse,
    StaffTransferResponse,
    TransferRequestPayload,
    TransferResolutionPayload,
)
from app.services.staff_directory_service import StaffDirectoryService
from app.services.activity_audit_service import ActivityAuditService

router = APIRouter(prefix="/enterprise/staff-directory", tags=["staff-directory"])


def _get_admin_context(current_user: User) -> Facility:
    if not current_user.is_facility_admin or not current_user.administered_facility:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Facility administrator access required for staff directory operations.",
        )
    facility = current_user.administered_facility
    if not facility.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Facility must belong to an organization to access the staff directory.",
        )
    return facility


def _serialize_assignment(db: Session, assignment: StaffFacilityAssignment) -> StaffDirectoryEntry:
    staff = db.query(StaffMember).filter(StaffMember.id == assignment.staff_member_id).first()
    facility = db.query(Facility).filter(Facility.id == assignment.facility_id).first()
    if not staff or not facility:
        raise HTTPException(status_code=404, detail="Assignment context not found.")
    return StaffDirectoryEntry(
        staff_member_id=staff.id,
        assignment_id=assignment.id,
        full_name=staff.full_name,
        email=staff.email,
        department=staff.department,
        role=staff.role,
        status=staff.status,
        facility_id=facility.id,
        facility_name=facility.facility_name,
        assigned_at=assignment.assigned_at,
    )


@router.get("", response_model=StaffDirectoryListResponse)
async def list_staff_directory(
    search: str | None = Query(default=None, description="Search by name, email, or department"),
    facility_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility = _get_admin_context(current_user)

    if facility_id:
        target_facility = db.query(Facility).filter(Facility.id == facility_id).first()
        if not target_facility or target_facility.organization_id != facility.organization_id:
            raise HTTPException(status_code=403, detail="Facility outside your organization.")

    result = StaffDirectoryService.list_staff(
        db,
        organization_id=facility.organization_id,
        facility_id=facility_id,
        search=search,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    return StaffDirectoryListResponse(**result)


@router.post("/assign", response_model=StaffDirectoryEntry)
async def assign_staff_to_facility(
    payload: AssignStaffPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility = _get_admin_context(current_user)

    target_facility = db.query(Facility).filter(Facility.id == payload.facility_id).first()
    if not target_facility or target_facility.organization_id != facility.organization_id:
        raise HTTPException(status_code=403, detail="Cannot assign staff outside your organization.")

    assignment = StaffDirectoryService.assign_staff_to_facility(
        db,
        staff_member_id=payload.staff_member_id,
        facility_id=payload.facility_id,
        assigned_by_user_id=current_user.id,
    )
    ActivityAuditService.log_event(
        db,
        actor_user_id=current_user.id,
        facility_id=facility.id,
        event_type="staff_assignment",
        description=f"Assigned staff_member_id={payload.staff_member_id} to facility {payload.facility_id}",
        metadata={"assignment_id": assignment.id},
    )
    return _serialize_assignment(db, assignment)


@router.post("/transfer", response_model=StaffTransferResponse)
async def request_transfer(
    payload: TransferRequestPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility = _get_admin_context(current_user)
    if payload.source_facility_id != facility.id:
        raise HTTPException(status_code=403, detail="Transfers can only be requested from your facility.")

    transfer_request = StaffDirectoryService.request_transfer(
        db,
        staff_member_id=payload.staff_member_id,
        source_facility_id=payload.source_facility_id,
        target_facility_id=payload.target_facility_id,
        requested_by_user_id=current_user.id,
        reason=payload.reason,
    )
    ActivityAuditService.log_event(
        db,
        actor_user_id=current_user.id,
        facility_id=facility.id,
        event_type="staff_transfer_requested",
        description=f"Transfer requested for staff_member_id={payload.staff_member_id}",
        metadata={"target_facility_id": payload.target_facility_id},
    )
    return StaffTransferResponse.from_orm(transfer_request)


def _get_transfer_request_or_404(db: Session, request_id: int) -> StaffTransferRequest:
    transfer_request = db.query(StaffTransferRequest).filter(StaffTransferRequest.id == request_id).first()
    if not transfer_request:
        raise HTTPException(status_code=404, detail="Transfer request not found.")
    return transfer_request


@router.post("/transfer/{request_id}/approve", response_model=StaffTransferResponse)
async def approve_transfer(
    request_id: int,
    payload: TransferResolutionPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility = _get_admin_context(current_user)
    transfer_request = _get_transfer_request_or_404(db, request_id)

    target_facility = db.query(Facility).filter(Facility.id == transfer_request.target_facility_id).first()
    if not target_facility or target_facility.organization_id != facility.organization_id:
        raise HTTPException(status_code=403, detail="Cannot approve transfer outside your organization.")
    if target_facility.id != facility.id:
        raise HTTPException(status_code=403, detail="Only the target facility may approve a transfer.")

    updated_request = StaffDirectoryService.approve_transfer(
        db,
        request_id=request_id,
        approver_id=current_user.id,
        resolution_notes=payload.resolution_notes,
    )
    ActivityAuditService.log_event(
        db,
        actor_user_id=current_user.id,
        facility_id=facility.id,
        event_type="staff_transfer_approved",
        description=f"Approved transfer request_id={request_id}",
        metadata={"resolution_notes": payload.resolution_notes},
    )
    return StaffTransferResponse.from_orm(updated_request)


@router.post("/transfer/{request_id}/reject", response_model=StaffTransferResponse)
async def reject_transfer(
    request_id: int,
    payload: TransferResolutionPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility = _get_admin_context(current_user)
    transfer_request = _get_transfer_request_or_404(db, request_id)

    target_facility = db.query(Facility).filter(Facility.id == transfer_request.target_facility_id).first()
    if not target_facility or target_facility.organization_id != facility.organization_id:
        raise HTTPException(status_code=403, detail="Cannot reject transfer outside your organization.")
    if target_facility.id != facility.id:
        raise HTTPException(status_code=403, detail="Only the target facility may reject a transfer.")

    updated_request = StaffDirectoryService.reject_transfer(
        db,
        request_id=request_id,
        approver_id=current_user.id,
        resolution_notes=payload.resolution_notes,
    )
    ActivityAuditService.log_event(
        db,
        actor_user_id=current_user.id,
        facility_id=facility.id,
        event_type="staff_transfer_rejected",
        description=f"Rejected transfer request_id={request_id}",
        metadata={"resolution_notes": payload.resolution_notes},
    )
    return StaffTransferResponse.from_orm(updated_request)

