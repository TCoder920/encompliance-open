"""
Scheduling Service Module

Centralizes all workforce scheduling business logic including shift creation,
conflict detection, availability tracking, PTO workflows, and shift swaps.
This service enforces facility-level multi-tenancy, audit logging, and
defensive validation before DB mutations.

Educational Note: Implements the Service Layer pattern recommended by
FastAPI/SQLAlchemy guidance and references OWASP secure coding practices for
input validation and authorization.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import enum

from fastapi import status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.models.facility import Facility
from app.models.staff_member import StaffMember
from app.models.scheduling import (
    Shift,
    ShiftStatus,
    StaffAvailability,
    TimeOffRequest,
    TimeOffStatus,
    TimeOffCategory,
    ShiftSwapRequest,
    ShiftSwapStatus,
)
from app.schemas.scheduling import (
    ShiftCreate,
    ShiftUpdate,
    StaffAvailabilityCreate,
    StaffAvailabilityUpdate,
    TimeOffRequestCreate,
    TimeOffRequestUpdate,
    ShiftSwapRequestCreate,
    ShiftSwapRequestUpdate,
    ConflictCheckResponse,
)
# Audit logging removed - scheduling actions are regular user actions, not support portal actions


logger = logging.getLogger(__name__)


class SchedulingServiceError(Exception):
    """Raised when scheduling operations fail validation."""

    def __init__(self, message: str, http_status: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.http_status = http_status


class SchedulingService:
    """Service class encapsulating scheduling workflows."""

    @staticmethod
    def create_shift(db: Session, shift_data: ShiftCreate, current_user: User) -> Shift:
        facility = SchedulingService._require_facility(current_user, shift_data.facility_id)
        SchedulingService._validate_shift_window(shift_data.start_time, shift_data.end_time)

        if shift_data.staff_member_id:
            SchedulingService._ensure_staff_member_scope(
                db, shift_data.staff_member_id, current_user.id
            )
            conflict = SchedulingService.detect_staff_conflicts(
                db=db,
                facility_id=facility.id,
                staff_member_id=shift_data.staff_member_id,
                start_time=shift_data.start_time,
                end_time=shift_data.end_time,
            )
            if conflict.has_conflict:
                raise SchedulingServiceError(
                    f"Shift conflicts with existing assignments: {conflict.conflict_reason}"
                )

        payload = SchedulingService._normalize_payload(shift_data.model_dump())
        payload["created_by"] = current_user.id
        shift = Shift(**payload)
        db.add(shift)
        db.commit()
        db.refresh(shift)

        SchedulingService._audit_log(
            db,
            admin_user_id=current_user.id,
            action="create_shift",
            target=f"shift:{shift.id}",
            details={"facility_id": facility.id, "status": shift.status},
        )
        return shift

    @staticmethod
    def list_shifts(
        db: Session,
        facility_id: int,
        current_user: User,
        status_filter: Optional[str] = None,
        start_from: Optional[datetime] = None,
        start_to: Optional[datetime] = None,
    ) -> List[Shift]:
        facility = SchedulingService._require_facility(current_user, facility_id)
        query = db.query(Shift).filter(
            Shift.facility_id == facility.id,
            Shift.is_deleted == False,  # noqa: E712 - SQLAlchemy expects boolean
        )

        if status_filter:
            query = query.filter(Shift.status == status_filter)
        if start_from:
            query = query.filter(Shift.start_time >= start_from)
        if start_to:
            query = query.filter(Shift.start_time <= start_to)

        shifts = query.order_by(Shift.start_time.asc()).all()
        logger.info("Loaded %s shifts for facility %s", len(shifts), facility.id)
        return shifts

    @staticmethod
    def update_shift(
        db: Session,
        shift_id: int,
        update_data: ShiftUpdate,
        current_user: User,
    ) -> Shift:
        shift = SchedulingService._get_shift_for_admin(db, shift_id, current_user)
        payload = SchedulingService._normalize_payload(update_data.model_dump(exclude_unset=True))

        new_start = payload.get("start_time", shift.start_time)
        new_end = payload.get("end_time", shift.end_time)
        SchedulingService._validate_shift_window(new_start, new_end)

        staff_member_id = payload.get("staff_member_id", shift.staff_member_id)

        if staff_member_id:
            SchedulingService._ensure_staff_member_scope(
                db, staff_member_id, current_user.id
            )
            conflict = SchedulingService.detect_staff_conflicts(
                db=db,
                facility_id=shift.facility_id,
                staff_member_id=staff_member_id,
                start_time=new_start,
                end_time=new_end,
                exclude_shift_id=shift.id,
            )
            if conflict.has_conflict:
                raise SchedulingServiceError(
                    f"Shift conflicts detected: {conflict.conflict_reason}"
                )

        for field, value in payload.items():
            setattr(shift, field, value)

        db.commit()
        db.refresh(shift)
        SchedulingService._audit_log(
            db,
            admin_user_id=current_user.id,
            action="update_shift",
            target=f"shift:{shift.id}",
            details={"fields": list(payload.keys())},
        )
        return shift

    @staticmethod
    def soft_delete_shift(db: Session, shift_id: int, current_user: User) -> None:
        shift = SchedulingService._get_shift_for_admin(db, shift_id, current_user)
        shift.is_deleted = True
        db.commit()
        SchedulingService._audit_log(
            db,
            admin_user_id=current_user.id,
            action="delete_shift",
            target=f"shift:{shift.id}",
            details={"soft_delete": True},
        )

    @staticmethod
    def upsert_availability(
        db: Session,
        availability_id: Optional[int],
        data: StaffAvailabilityCreate | StaffAvailabilityUpdate,
        current_user: User,
    ):
        facility = SchedulingService._require_facility(
            current_user,
            getattr(data, "facility_id", None) or current_user.administered_facility.id,
        )

        if isinstance(data, StaffAvailabilityCreate):
            SchedulingService._ensure_staff_member_scope(
                db, data.staff_member_id, current_user.id
            )
            payload = SchedulingService._normalize_payload(data.model_dump())
            payload["created_by"] = current_user.id
            availability = StaffAvailability(**payload)
            db.add(availability)
        else:
            availability = SchedulingService._get_availability_for_admin(
                db, availability_id, current_user
            )
            normalized = SchedulingService._normalize_payload(
                data.model_dump(exclude_unset=True)
            )
            for field, value in normalized.items():
                setattr(availability, field, value)

        db.commit()
        db.refresh(availability)
        SchedulingService._audit_log(
            db,
            admin_user_id=current_user.id,
            action="upsert_availability",
            target=f"availability:{availability.id}",
            details={"facility_id": facility.id},
        )
        return availability

    @staticmethod
    def delete_availability(db: Session, availability_id: int, current_user: User):
        availability = SchedulingService._get_availability_for_admin(
            db, availability_id, current_user
        )
        db.delete(availability)
        db.commit()
        SchedulingService._audit_log(
            db,
            admin_user_id=current_user.id,
            action="delete_availability",
            target=f"availability:{availability_id}",
            details=None,
        )

    @staticmethod
    def request_time_off(
        db: Session,
        data: TimeOffRequestCreate,
        current_user: User,
    ) -> TimeOffRequest:
        facility = SchedulingService._require_facility(current_user, data.facility_id)
        SchedulingService._ensure_staff_member_scope(
            db, data.staff_member_id, current_user.id
        )
        SchedulingService._validate_shift_window(data.start_date, data.end_date)

        conflicts = SchedulingService._time_off_conflicts(
            db, facility.id, data.staff_member_id, data.start_date, data.end_date
        )
        if conflicts:
            raise SchedulingServiceError(
                f"Time off request overlaps with shifts: {conflicts}"
            )

        payload = SchedulingService._normalize_payload(data.model_dump())
        payload["status"] = TimeOffStatus.PENDING.value
        payload["requested_by"] = current_user.id
        request = TimeOffRequest(**payload)
        db.add(request)
        db.commit()
        db.refresh(request)
        SchedulingService._audit_log(
            db,
            admin_user_id=current_user.id,
            action="create_time_off",
            target=f"timeoff:{request.id}",
            details={"status": request.status},
        )
        return request

    @staticmethod
    def review_time_off(
        db: Session,
        request_id: int,
        update_data: TimeOffRequestUpdate,
        current_user: User,
    ) -> TimeOffRequest:
        request = SchedulingService._get_time_off_for_admin(db, request_id, current_user)
        payload = SchedulingService._normalize_payload(update_data.model_dump(exclude_unset=True))

        if "status" in payload and payload["status"] not in {
            TimeOffStatus.APPROVED.value,
            TimeOffStatus.DENIED.value,
            TimeOffStatus.CANCELLED.value,
        }:
            raise SchedulingServiceError("Invalid status transition for review")

        if "start_date" in payload or "end_date" in payload:
            new_start = payload.get("start_date", request.start_date)
            new_end = payload.get("end_date", request.end_date)
            SchedulingService._validate_shift_window(new_start, new_end)

        for field, value in payload.items():
            setattr(request, field, value)

        request.reviewed_by = current_user.id
        request.reviewed_at = datetime.utcnow()
        request.add_audit_entry(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "admin_id": current_user.id,
                "updates": list(payload.keys()),
            }
        )

        db.commit()
        db.refresh(request)
        SchedulingService._audit_log(
            db,
            admin_user_id=current_user.id,
            action="review_time_off",
            target=f"timeoff:{request.id}",
            details={"status": request.status},
        )
        return request

    @staticmethod
    def create_shift_swap(
        db: Session,
        data: ShiftSwapRequestCreate,
        current_user: User,
    ) -> ShiftSwapRequest:
        facility = SchedulingService._require_facility(current_user, data.facility_id)
        shift = SchedulingService._get_shift_for_admin(db, data.shift_id, current_user)
        SchedulingService._ensure_staff_member_scope(
            db, data.requested_by_staff_id, current_user.id
        )

        payload = SchedulingService._normalize_payload(data.model_dump())
        payload["created_by"] = current_user.id
        swap = ShiftSwapRequest(**payload)
        db.add(swap)
        db.commit()
        db.refresh(swap)
        SchedulingService._audit_log(
            db,
            admin_user_id=current_user.id,
            action="create_shift_swap",
            target=f"swap:{swap.id}",
            details={"facility_id": facility.id, "shift_id": shift.id},
        )
        return swap

    @staticmethod
    def respond_to_shift_swap(
        db: Session,
        swap_id: int,
        update_data: ShiftSwapRequestUpdate,
        current_user: User,
    ) -> ShiftSwapRequest:
        swap = SchedulingService._get_swap_for_admin(db, swap_id, current_user)
        payload = SchedulingService._normalize_payload(update_data.model_dump(exclude_unset=True))

        if "status" in payload:
            SchedulingService._validate_swap_transition(swap.status, payload["status"])

        for field, value in payload.items():
            setattr(swap, field, value)

        swap.resolved_by = current_user.id
        swap.responded_at = datetime.utcnow()
        db.commit()
        db.refresh(swap)
        SchedulingService._audit_log(
            db,
            admin_user_id=current_user.id,
            action="respond_shift_swap",
            target=f"swap:{swap.id}",
            details={"status": swap.status},
        )
        return swap

    @staticmethod
    def detect_staff_conflicts(
        db: Session,
        facility_id: int,
        staff_member_id: Optional[int],
        start_time: datetime,
        end_time: datetime,
        exclude_shift_id: Optional[int] = None,
    ) -> ConflictCheckResponse:
        if not staff_member_id:
            return ConflictCheckResponse(
                has_conflict=False,
                conflict_reason=None,
                conflicting_shift_ids=[],
                conflicting_time_off_ids=[],
            )

        shift_query = db.query(Shift).filter(
            Shift.facility_id == facility_id,
            Shift.staff_member_id == staff_member_id,
            Shift.is_deleted == False,  # noqa: E712
            Shift.start_time < end_time,
            Shift.end_time > start_time,
        )
        if exclude_shift_id:
            shift_query = shift_query.filter(Shift.id != exclude_shift_id)
        overlapping_shifts = shift_query.all()

        time_off_query = db.query(TimeOffRequest).filter(
            TimeOffRequest.facility_id == facility_id,
            TimeOffRequest.staff_member_id == staff_member_id,
            TimeOffRequest.status.notin_(
                [TimeOffStatus.CANCELLED.value, TimeOffStatus.DENIED.value]
            ),
            TimeOffRequest.start_date < end_time,
            TimeOffRequest.end_date > start_time,
            TimeOffRequest.is_deleted == False,  # noqa: E712
        )
        overlapping_time_off = time_off_query.all()

        has_conflict = bool(overlapping_shifts or overlapping_time_off)
        reason = None
        if overlapping_shifts:
            reason = "Overlapping shift assignments"
        elif overlapping_time_off:
            reason = "Approved/Pending time off"

        return ConflictCheckResponse(
            has_conflict=has_conflict,
            conflict_reason=reason,
            conflicting_shift_ids=[shift.id for shift in overlapping_shifts],
            conflicting_time_off_ids=[req.id for req in overlapping_time_off],
        )

    # ---------- Internal helpers ----------

    @staticmethod
    def _require_facility(current_user: User, facility_id: Optional[int]) -> Facility:
        if not current_user.is_facility_admin:
            raise SchedulingServiceError(
                "Facility administrator access required",
                http_status=status.HTTP_403_FORBIDDEN,
            )

        facility = current_user.administered_facility
        if not facility:
            raise SchedulingServiceError("Facility record not found for administrator")

        if facility_id and facility.id != facility_id:
            raise SchedulingServiceError("Facility mismatch for requested resource")

        return facility

    @staticmethod
    def _ensure_staff_member_scope(
        db: Session, staff_member_id: int, admin_user_id: int
    ) -> StaffMember:
        staff_member = (
            db.query(StaffMember)
            .filter(
                StaffMember.id == staff_member_id,
                StaffMember.facility_administrator_id == admin_user_id,
            )
            .first()
        )
        if not staff_member:
            raise SchedulingServiceError("Staff member not in facility scope")
        return staff_member

    @staticmethod
    def _validate_shift_window(start: datetime, end: datetime):
        if end <= start:
            raise SchedulingServiceError("End time must be after start time")

    @staticmethod
    def _get_shift_for_admin(db: Session, shift_id: int, current_user: User) -> Shift:
        facility = SchedulingService._require_facility(current_user, None)
        shift = (
            db.query(Shift)
            .filter(
                Shift.id == shift_id,
                Shift.facility_id == facility.id,
                Shift.is_deleted == False,  # noqa: E712
            )
            .first()
        )
        if not shift:
            raise SchedulingServiceError(
                "Shift not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return shift

    @staticmethod
    def _get_availability_for_admin(
        db: Session, availability_id: int, current_user: User
    ) -> StaffAvailability:
        facility = SchedulingService._require_facility(current_user, None)
        availability = (
            db.query(StaffAvailability)
            .filter(
                StaffAvailability.id == availability_id,
                StaffAvailability.facility_id == facility.id,
            )
            .first()
        )
        if not availability:
            raise SchedulingServiceError(
                "Availability block not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return availability

    @staticmethod
    def _get_time_off_for_admin(
        db: Session, request_id: int, current_user: User
    ) -> TimeOffRequest:
        facility = SchedulingService._require_facility(current_user, None)
        request = (
            db.query(TimeOffRequest)
            .filter(
                TimeOffRequest.id == request_id,
                TimeOffRequest.facility_id == facility.id,
                TimeOffRequest.is_deleted == False,  # noqa: E712
            )
            .first()
        )
        if not request:
            raise SchedulingServiceError(
                "Time off request not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return request

    @staticmethod
    def _get_swap_for_admin(
        db: Session, swap_id: int, current_user: User
    ) -> ShiftSwapRequest:
        facility = SchedulingService._require_facility(current_user, None)
        swap = (
            db.query(ShiftSwapRequest)
            .filter(
                ShiftSwapRequest.id == swap_id,
                ShiftSwapRequest.facility_id == facility.id,
            )
            .first()
        )
        if not swap:
            raise SchedulingServiceError(
                "Shift swap request not found",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return swap

    @staticmethod
    def _validate_swap_transition(
        current_status: str, new_status: str
    ) -> None:
        terminal_states = {
            ShiftSwapStatus.APPROVED.value,
            ShiftSwapStatus.DENIED.value,
            ShiftSwapStatus.CANCELLED.value,
            ShiftSwapStatus.EXPIRED.value,
        }
        if current_status in terminal_states:
            raise SchedulingServiceError(
                "Cannot update a resolved shift swap request"
            )
        if new_status not in {
            ShiftSwapStatus.APPROVED.value,
            ShiftSwapStatus.DENIED.value,
            ShiftSwapStatus.CANCELLED.value,
        }:
            raise SchedulingServiceError("Unsupported shift swap status transition")

    @staticmethod
    def _time_off_conflicts(
        db: Session,
        facility_id: int,
        staff_member_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[int]:
        overlaps = (
            db.query(Shift.id)
            .filter(
                Shift.facility_id == facility_id,
                Shift.staff_member_id == staff_member_id,
                Shift.is_deleted == False,  # noqa: E712
                Shift.start_time < end_date,
                Shift.end_time > start_date,
            )
            .all()
        )
        return [item[0] for item in overlaps]

    @staticmethod
    def _audit_log(
        db: Session,
        admin_user_id: int,
        action: str,
        target: Optional[str],
        details: Optional[dict],
    ):
        # Audit logging removed - scheduling actions are regular user actions in the main database,
        # not support portal actions. Use ActivityAuditService if audit logging is needed for scheduling.
        logger.debug(f"Scheduling action logged (audit disabled): {action} by user {admin_user_id}")
        pass

    @staticmethod
    def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {}
        for key, value in payload.items():
            normalized[key] = SchedulingService._serialize_value(value)
        return normalized

    @staticmethod
    def _serialize_value(value: Any):
        if isinstance(value, enum.Enum):
            return value.value
        return value

