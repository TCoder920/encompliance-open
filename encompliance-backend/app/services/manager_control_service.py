"""
Manager Control Service
"""

from datetime import datetime
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.manager_override_request import ManagerOverrideRequest, ManagerOverrideStatus


class ManagerControlService:
    """Handles enterprise manager override workflows."""

    @staticmethod
    def submit_request(
        db: Session,
        *,
        facility_id: int,
        requested_by_user_id: int,
        action_type: str,
        payload,
    ) -> ManagerOverrideRequest:
        request = ManagerOverrideRequest(
            facility_id=facility_id,
            requested_by_user_id=requested_by_user_id,
            action_type=action_type,
            payload=payload,
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def list_requests(
        db: Session,
        *,
        organization_facility_ids: List[int],
        status: str | None = None,
    ) -> List[ManagerOverrideRequest]:
        query = db.query(ManagerOverrideRequest).filter(
            ManagerOverrideRequest.facility_id.in_(organization_facility_ids)
        )
        if status:
            query = query.filter(ManagerOverrideRequest.status == status)
        return query.order_by(ManagerOverrideRequest.created_at.desc()).all()

    @staticmethod
    def approve_request(
        db: Session,
        *,
        request_id: int,
        approver_id: int,
        notes: str | None = None,
    ) -> ManagerOverrideRequest:
        request = db.query(ManagerOverrideRequest).filter(ManagerOverrideRequest.id == request_id).first()
        if not request:
            raise ValueError("Request not found.")
        request.status = ManagerOverrideStatus.APPROVED
        request.approved_by_user_id = approver_id
        request.resolved_at = datetime.utcnow()
        request.resolution_notes = notes
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def reject_request(
        db: Session,
        *,
        request_id: int,
        approver_id: int,
        notes: str | None = None,
    ) -> ManagerOverrideRequest:
        request = db.query(ManagerOverrideRequest).filter(ManagerOverrideRequest.id == request_id).first()
        if not request:
            raise ValueError("Request not found.")
        request.status = ManagerOverrideStatus.REJECTED
        request.approved_by_user_id = approver_id
        request.resolved_at = datetime.utcnow()
        request.resolution_notes = notes
        db.commit()
        db.refresh(request)
        return request

