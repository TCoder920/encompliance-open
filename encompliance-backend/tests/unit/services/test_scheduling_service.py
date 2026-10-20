"""
Unit tests for the SchedulingService covering shift creation and conflict detection.
"""

from datetime import datetime, timedelta

import pytest

from app.schemas.scheduling import ShiftCreate
from app.services.scheduling_service import SchedulingService, SchedulingServiceError
from app.models.user import User, UserRole
from app.models.facility import Facility
from app.models.staff_member import StaffMember, StaffStatus
from app.models.scheduling import Shift, TimeOffRequest, TimeOffStatus, TimeOffCategory
from app.models.task_reference_image import TaskReferenceImage  # noqa: F401 - ensures mapper registration


def _bootstrap_admin(db_session):
    admin = User(
        email="admin@example.com",
        username="admin",
        hashed_password="hashed",
        full_name="Admin User",
        user_role=UserRole.FACILITY_ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    facility = Facility(
        facility_name="Test Facility",
        admin_user_id=admin.id,
        is_active=True,
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)

    admin.facility_id = facility.id
    db_session.commit()
    db_session.refresh(admin)

    staff = StaffMember(
        first_name="Sam",
        last_name="Nurse",
        email="sam@example.com",
        facility_administrator_id=admin.id,
        status=StaffStatus.ACTIVE.value,
    )
    db_session.add(staff)
    db_session.commit()
    db_session.refresh(staff)

    return admin, facility, staff


class TestSchedulingService:
    """Core scheduling service behaviour."""

    def test_create_shift_success(self, db_session):
        admin, facility, staff = _bootstrap_admin(db_session)
        start = datetime.utcnow()
        end = start + timedelta(hours=8)

        payload = ShiftCreate(
            facility_id=facility.id,
            title="Day Shift",
            description="Primary coverage",
            role="Lead",
            department="Operations",
            location="Main Floor",
            start_time=start,
            end_time=end,
            staff_member_id=staff.id,
        )

        shift = SchedulingService.create_shift(
            db=db_session,
            shift_data=payload,
            current_user=admin,
        )

        assert isinstance(shift, Shift)
        assert shift.id is not None
        assert shift.staff_member_id == staff.id
        assert shift.facility_id == facility.id

    def test_create_shift_conflict_detection(self, db_session):
        admin, facility, staff = _bootstrap_admin(db_session)
        start = datetime.utcnow()
        end = start + timedelta(hours=8)

        first_shift = ShiftCreate(
            facility_id=facility.id,
            title="Day Shift",
            description="Coverage",
            role="Lead",
            department="Ops",
            location="Main",
            start_time=start,
            end_time=end,
            staff_member_id=staff.id,
        )
        SchedulingService.create_shift(db=db_session, shift_data=first_shift, current_user=admin)

        overlapping_shift = ShiftCreate(
            facility_id=facility.id,
            title="Overlap Shift",
            description="Conflict",
            role="Lead",
            department="Ops",
            location="Main",
            start_time=start + timedelta(hours=2),
            end_time=end + timedelta(hours=2),
            staff_member_id=staff.id,
        )

        with pytest.raises(SchedulingServiceError):
            SchedulingService.create_shift(
                db=db_session,
                shift_data=overlapping_shift,
                current_user=admin,
            )

    def test_detect_time_off_conflict(self, db_session):
        admin, facility, staff = _bootstrap_admin(db_session)
        start = datetime.utcnow()
        end = start + timedelta(hours=4)

        request = TimeOffRequest(
            staff_member_id=staff.id,
            facility_id=facility.id,
            start_date=start,
            end_date=end,
            status=TimeOffStatus.APPROVED.value,
            category=TimeOffCategory.PTO.value,
            requested_by=admin.id,
        )
        db_session.add(request)
        db_session.commit()

        result = SchedulingService.detect_staff_conflicts(
            db=db_session,
            facility_id=facility.id,
            staff_member_id=staff.id,
            start_time=start + timedelta(hours=1),
            end_time=end + timedelta(hours=1),
        )

        assert result.has_conflict is True
        assert request.id in result.conflicting_time_off_ids

