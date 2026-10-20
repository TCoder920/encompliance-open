"""
Enterprise Escalation Policy Routes
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.models.escalation import EscalationPolicy
from app.models.user import User
from app.schemas.escalation import (
    EscalationIncidentResponse,
    EscalationPolicyCreate,
    EscalationPolicyResponse,
)
from app.services.escalation_service import EscalationService
from app.services.activity_audit_service import ActivityAuditService

router = APIRouter(prefix="/enterprise/escalations", tags=["escalations"])


def _require_facility_context(current_user: User) -> int:
    if not current_user.is_facility_admin or not current_user.administered_facility:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Facility admin access required.")
    if not current_user.administered_facility.organization_id:
        raise HTTPException(status_code=400, detail="Enterprise organization context required.")
    return current_user.administered_facility.id


@router.get("/policies", response_model=List[EscalationPolicyResponse])
async def list_policies(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility_id = _require_facility_context(current_user)
    policies = EscalationService.list_policies(db, facility_id)
    return [EscalationPolicyResponse.from_orm(policy) for policy in policies]


@router.post("/policies", response_model=EscalationPolicyResponse)
async def create_policy(
    payload: EscalationPolicyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility_id = _require_facility_context(current_user)
    policy = EscalationService.create_policy(
        db,
        facility_id=facility_id,
        created_by_user_id=current_user.id,
        payload=payload.dict(),
    )
    ActivityAuditService.log_event(
        db,
        actor_user_id=current_user.id,
        facility_id=facility_id,
        event_type="escalation_policy_created",
        description=f"Created escalation policy {policy.name}",
        metadata={"policy_id": policy.id},
    )
    return EscalationPolicyResponse.from_orm(policy)


@router.post("/policies/{policy_id}/trigger", response_model=EscalationIncidentResponse)
async def trigger_incident(
    policy_id: int,
    metadata: Optional[dict] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility_id = _require_facility_context(current_user)
    policy = db.query(EscalationPolicy).filter(EscalationPolicy.id == policy_id, EscalationPolicy.facility_id == facility_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found.")

    incident = EscalationService.trigger_incident(db, policy_id=policy_id, metadata=metadata)
    ActivityAuditService.log_event(
        db,
        actor_user_id=current_user.id,
        facility_id=facility_id,
        event_type="escalation_triggered",
        description=f"Triggered escalation policy_id={policy_id}",
        metadata=metadata,
    )
    return EscalationIncidentResponse.from_orm(incident)


@router.post("/incidents/{incident_id}/acknowledge", response_model=EscalationIncidentResponse)
async def acknowledge_incident(
    incident_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _require_facility_context(current_user)
    incident = EscalationService.acknowledge_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")
    ActivityAuditService.log_event(
        db,
        actor_user_id=current_user.id,
        facility_id=current_user.administered_facility.id if current_user.administered_facility else None,
        event_type="escalation_acknowledged",
        description=f"Acknowledged incident_id={incident_id}",
        metadata=None,
    )
    return EscalationIncidentResponse.from_orm(incident)

