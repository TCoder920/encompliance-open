"""
Scheduling Routes Module

Exposes REST endpoints for workforce scheduling, enforcing service-layer
business rules and facility-level authorization.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_facility_admin
from app.models.user import User
from app.schemas.scheduling import (
    ShiftCreate,
    ShiftUpdate,
    ShiftResponse,
    StaffAvailabilityCreate,
    StaffAvailabilityUpdate,
    StaffAvailabilityResponse,
    TimeOffRequestCreate,
    TimeOffRequestUpdate,
    TimeOffRequestResponse,
    ShiftSwapRequestCreate,
    ShiftSwapRequestUpdate,
    ShiftSwapRequestResponse,
    ConflictCheckResponse,
)
from app.services.scheduling_service import SchedulingService, SchedulingServiceError


router = APIRouter(prefix="/scheduling", tags=["scheduling"])


def _wrap_service_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except SchedulingServiceError as exc:
        raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc


@router.post("/shifts", response_model=ShiftResponse)
async def create_shift(
    shift_data: ShiftCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    """Create a shift for the facility administrator."""
    return _wrap_service_call(
        SchedulingService.create_shift, db=db, shift_data=shift_data, current_user=current_user
    )


@router.get("/shifts", response_model=List[ShiftResponse])
async def list_shifts(
    status_filter: Optional[str] = Query(None, description="Filter by shift status"),
    start_from: Optional[datetime] = Query(None),
    start_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    facility = current_user.administered_facility
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not configured")
    return _wrap_service_call(
        SchedulingService.list_shifts,
        db=db,
        facility_id=facility.id,
        current_user=current_user,
        status_filter=status_filter,
        start_from=start_from,
        start_to=start_to,
    )


@router.put("/shifts/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: int,
    shift_data: ShiftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return _wrap_service_call(
        SchedulingService.update_shift,
        db=db,
        shift_id=shift_id,
        update_data=shift_data,
        current_user=current_user,
    )


@router.delete("/shifts/{shift_id}")
async def delete_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    _wrap_service_call(
        SchedulingService.soft_delete_shift,
        db=db,
        shift_id=shift_id,
        current_user=current_user,
    )
    return {"message": "Shift deleted"}


@router.post("/availability", response_model=StaffAvailabilityResponse)
async def create_availability(
    availability_data: StaffAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return _wrap_service_call(
        SchedulingService.upsert_availability,
        db=db,
        availability_id=None,
        data=availability_data,
        current_user=current_user,
    )


@router.put("/availability/{availability_id}", response_model=StaffAvailabilityResponse)
async def update_availability(
    availability_id: int,
    availability_data: StaffAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return _wrap_service_call(
        SchedulingService.upsert_availability,
        db=db,
        availability_id=availability_id,
        data=availability_data,
        current_user=current_user,
    )


@router.delete("/availability/{availability_id}")
async def delete_availability(
    availability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    _wrap_service_call(
        SchedulingService.delete_availability,
        db=db,
        availability_id=availability_id,
        current_user=current_user,
    )
    return {"message": "Availability deleted"}


@router.post("/time-off", response_model=TimeOffRequestResponse)
async def create_time_off_request(
    request_data: TimeOffRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return _wrap_service_call(
        SchedulingService.request_time_off,
        db=db,
        data=request_data,
        current_user=current_user,
    )


@router.put("/time-off/{request_id}", response_model=TimeOffRequestResponse)
async def review_time_off_request(
    request_id: int,
    request_data: TimeOffRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return _wrap_service_call(
        SchedulingService.review_time_off,
        db=db,
        request_id=request_id,
        update_data=request_data,
        current_user=current_user,
    )


@router.post("/shift-swaps", response_model=ShiftSwapRequestResponse)
async def create_shift_swap(
    swap_data: ShiftSwapRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return _wrap_service_call(
        SchedulingService.create_shift_swap,
        db=db,
        data=swap_data,
        current_user=current_user,
    )


@router.put("/shift-swaps/{swap_id}", response_model=ShiftSwapRequestResponse)
async def respond_shift_swap(
    swap_id: int,
    swap_data: ShiftSwapRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return _wrap_service_call(
        SchedulingService.respond_to_shift_swap,
        db=db,
        swap_id=swap_id,
        update_data=swap_data,
        current_user=current_user,
    )


@router.get("/shifts/conflicts", response_model=ConflictCheckResponse)
async def check_shift_conflicts(
    staff_member_id: Optional[int] = Query(None),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    facility = current_user.administered_facility
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not configured")
    return _wrap_service_call(
        SchedulingService.detect_staff_conflicts,
        db=db,
        facility_id=facility.id,
        staff_member_id=staff_member_id,
        start_time=start_time,
        end_time=end_time,
        exclude_shift_id=None,
    )

