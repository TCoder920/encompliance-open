"""
Staff Directory Service

Handles staff roster queries, facility assignments, and transfer workflows for enterprise customers.
"""

from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.facility import Facility
from app.models.staff_directory import (
    StaffAssignmentStatus,
    StaffFacilityAssignment,
    StaffTransferRequest,
    StaffTransferStatus,
)
from app.models.staff_member import StaffMember
from app.models.user import User


class StaffDirectoryService:
    """Business logic for managing cross-facility staff assignments."""

    @staticmethod
    def list_staff(
        db: Session,
        *,
        organization_id: Optional[int],
        facility_id: Optional[int],
        search: Optional[str],
        status: Optional[str],
        page: int = 1,
        page_size: int = 25,
    ) -> Dict:
        query = (
            db.query(StaffFacilityAssignment, StaffMember, Facility)
            .join(StaffMember, StaffFacilityAssignment.staff_member_id == StaffMember.id)
            .join(Facility, StaffFacilityAssignment.facility_id == Facility.id)
            .filter(StaffFacilityAssignment.status == StaffAssignmentStatus.ACTIVE.value)
        )

        if organization_id:
            query = query.filter(Facility.organization_id == organization_id)

        if facility_id:
            query = query.filter(Facility.id == facility_id)

        if status:
            query = query.filter(StaffMember.status == status)

        if search:
            like_term = f"%{search.lower()}%"
            full_name_expr = func.concat(func.lower(StaffMember.first_name), " ", func.lower(StaffMember.last_name))
            query = query.filter(
                or_(
                    full_name_expr.like(like_term),
                    func.lower(StaffMember.email).like(like_term),
                    func.lower(StaffMember.department).like(like_term),
                )
            )

        total = query.count()
        records = (
            query.order_by(StaffMember.last_name.asc(), StaffMember.first_name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = [
            {
                "assignment_id": assignment.id,
                "staff_member_id": staff.id,
                "full_name": staff.full_name,
                "email": staff.email,
                "department": staff.department,
                "role": staff.role,
                "status": staff.status,
                "facility_id": facility.id,
                "facility_name": facility.facility_name,
                "assigned_at": assignment.assigned_at,
            }
            for assignment, staff, facility in records
        ]

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    @staticmethod
    def assign_staff_to_facility(
        db: Session,
        *,
        staff_member_id: int,
        facility_id: int,
        assigned_by_user_id: int,
    ) -> StaffFacilityAssignment:
        StaffDirectoryService._validate_staff_and_facility(db, staff_member_id, facility_id)

        existing = (
            db.query(StaffFacilityAssignment)
            .filter(
                StaffFacilityAssignment.staff_member_id == staff_member_id,
                StaffFacilityAssignment.facility_id == facility_id,
                StaffFacilityAssignment.status == StaffAssignmentStatus.ACTIVE.value,
            )
            .first()
        )
        if existing:
            return existing

        assignment = StaffFacilityAssignment(
            staff_member_id=staff_member_id,
            facility_id=facility_id,
            assigned_by_user_id=assigned_by_user_id,
            status=StaffAssignmentStatus.ACTIVE.value,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def request_transfer(
        db: Session,
        *,
        staff_member_id: int,
        source_facility_id: int,
        target_facility_id: int,
        requested_by_user_id: int,
        reason: Optional[str] = None,
    ) -> StaffTransferRequest:
        StaffDirectoryService._validate_staff_and_facility(db, staff_member_id, source_facility_id)
        StaffDirectoryService._validate_facility_in_same_org(db, source_facility_id, target_facility_id)

        active_assignment = (
            db.query(StaffFacilityAssignment)
            .filter(
                StaffFacilityAssignment.staff_member_id == staff_member_id,
                StaffFacilityAssignment.facility_id == source_facility_id,
                StaffFacilityAssignment.status == StaffAssignmentStatus.ACTIVE.value,
            )
            .first()
        )
        if not active_assignment:
            raise ValueError("Staff member has no active assignment at the source facility.")

        existing_request = (
            db.query(StaffTransferRequest)
            .filter(
                StaffTransferRequest.staff_member_id == staff_member_id,
                StaffTransferRequest.status == StaffTransferStatus.PENDING.value,
            )
            .first()
        )
        if existing_request:
            return existing_request

        transfer_request = StaffTransferRequest(
            staff_member_id=staff_member_id,
            source_facility_id=source_facility_id,
            target_facility_id=target_facility_id,
            status=StaffTransferStatus.PENDING.value,
            requested_by_user_id=requested_by_user_id,
            reason=reason,
        )
        db.add(transfer_request)
        db.commit()
        db.refresh(transfer_request)
        return transfer_request

    @staticmethod
    def approve_transfer(
        db: Session,
        *,
        request_id: int,
        approver_id: int,
        resolution_notes: Optional[str] = None,
    ) -> StaffTransferRequest:
        transfer_request = db.query(StaffTransferRequest).filter(StaffTransferRequest.id == request_id).first()
        if not transfer_request:
            raise ValueError("Transfer request not found.")
        if transfer_request.status != StaffTransferStatus.PENDING.value:
            raise ValueError("Transfer request already resolved.")

        StaffDirectoryService._validate_staff_and_facility(
            db, transfer_request.staff_member_id, transfer_request.source_facility_id
        )
        StaffDirectoryService._validate_facility_in_same_org(
            db, transfer_request.source_facility_id, transfer_request.target_facility_id
        )

        # Close existing assignment
        assignment = (
            db.query(StaffFacilityAssignment)
            .filter(
                StaffFacilityAssignment.staff_member_id == transfer_request.staff_member_id,
                StaffFacilityAssignment.facility_id == transfer_request.source_facility_id,
                StaffFacilityAssignment.status == StaffAssignmentStatus.ACTIVE.value,
            )
            .first()
        )
        if assignment:
            assignment.status = StaffAssignmentStatus.REMOVED.value
            assignment.unassigned_at = datetime.utcnow()

        # Create new assignment
        StaffDirectoryService.assign_staff_to_facility(
            db,
            staff_member_id=transfer_request.staff_member_id,
            facility_id=transfer_request.target_facility_id,
            assigned_by_user_id=approver_id,
        )

        transfer_request.status = StaffTransferStatus.APPROVED.value
        transfer_request.approved_by_user_id = approver_id
        transfer_request.resolved_at = datetime.utcnow()
        transfer_request.resolution_notes = resolution_notes
        db.commit()
        db.refresh(transfer_request)
        return transfer_request

    @staticmethod
    def reject_transfer(
        db: Session,
        *,
        request_id: int,
        approver_id: int,
        resolution_notes: Optional[str] = None,
    ) -> StaffTransferRequest:
        transfer_request = db.query(StaffTransferRequest).filter(StaffTransferRequest.id == request_id).first()
        if not transfer_request:
            raise ValueError("Transfer request not found.")
        if transfer_request.status != StaffTransferStatus.PENDING.value:
            raise ValueError("Transfer request already resolved.")

        transfer_request.status = StaffTransferStatus.REJECTED.value
        transfer_request.approved_by_user_id = approver_id
        transfer_request.resolved_at = datetime.utcnow()
        transfer_request.resolution_notes = resolution_notes
        db.commit()
        db.refresh(transfer_request)
        return transfer_request

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_staff_and_facility(db: Session, staff_member_id: int, facility_id: int) -> None:
        staff = db.query(StaffMember).filter(StaffMember.id == staff_member_id).first()
        facility = db.query(Facility).filter(Facility.id == facility_id).first()
        if not staff or not facility:
            raise ValueError("Invalid staff member or facility.")

    @staticmethod
    def _validate_facility_in_same_org(db: Session, facility_a_id: int, facility_b_id: int) -> None:
        facilities = (
            db.query(Facility.id, Facility.organization_id)
            .filter(Facility.id.in_([facility_a_id, facility_b_id]))
            .all()
        )
        if len(facilities) != 2:
            raise ValueError("One of the facilities could not be found.")
        org_ids = {facility.organization_id for facility in facilities}
        if len(org_ids) > 1:
            raise ValueError("Facilities must belong to the same organization for transfers.")

