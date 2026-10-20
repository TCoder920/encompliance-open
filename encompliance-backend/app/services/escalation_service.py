"""
Escalation Service

Manages enterprise notification escalation policies and incident processing.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio

from sqlalchemy.orm import Session

from app.models.escalation import (
    EscalationChannel,
    EscalationIncident,
    EscalationIncidentStatus,
    EscalationPolicy,
    EscalationStep,
)
from app.models.facility import Facility
from app.models.user import User, UserRole
from app.schemas.notification import NotificationCreate, NotificationType, NotificationPriority
from app.services.notification_service import NotificationService


class EscalationService:
    """Business logic for escalation policies and incidents."""

    @staticmethod
    def list_policies(db: Session, facility_id: int) -> List[EscalationPolicy]:
        return (
            db.query(EscalationPolicy)
            .filter(EscalationPolicy.facility_id == facility_id)
            .order_by(EscalationPolicy.created_at.desc())
            .all()
        )

    @staticmethod
    def create_policy(
        db: Session,
        facility_id: int,
        created_by_user_id: int,
        payload: Dict,
    ) -> EscalationPolicy:
        policy = EscalationPolicy(
            facility_id=facility_id,
            name=payload["name"],
            incident_type=payload["incident_type"],
            description=payload.get("description"),
            created_by_user_id=created_by_user_id,
        )
        db.add(policy)
        db.flush()

        steps_payload = payload.get("steps", [])
        for index, step_payload in enumerate(steps_payload, start=1):
            step = EscalationStep(
                policy_id=policy.id,
                step_number=index,
                delay_minutes=step_payload.get("delay_minutes", 0),
                channel=EscalationChannel(step_payload.get("channel", EscalationChannel.EMAIL.value)),
                target_role=step_payload.get("target_role"),
                target_user_id=step_payload.get("target_user_id"),
                custom_recipient=step_payload.get("custom_recipient"),
                message_template=step_payload.get("message_template"),
            )
            db.add(step)

        db.commit()
        db.refresh(policy)
        return policy

    @staticmethod
    def trigger_incident(
        db: Session,
        policy_id: int,
        metadata: Optional[Dict] = None,
    ) -> EscalationIncident:
        incident = EscalationIncident(
            policy_id=policy_id,
            incident_metadata=metadata or {},
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def acknowledge_incident(db: Session, incident_id: int) -> Optional[EscalationIncident]:
        incident = db.query(EscalationIncident).filter(EscalationIncident.id == incident_id).first()
        if not incident:
            return None
        incident.status = EscalationIncidentStatus.ACKNOWLEDGED
        incident.acknowledged_at = datetime.utcnow()
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def process_pending_incidents(db: Session) -> int:
        pending_incidents = (
            db.query(EscalationIncident)
            .join(EscalationPolicy)
            .filter(
                EscalationIncident.status == EscalationIncidentStatus.PENDING,
                EscalationPolicy.is_active == True,  # noqa: E712
            )
            .all()
        )

        processed = 0
        for incident in pending_incidents:
            steps = sorted(incident.policy.steps, key=lambda s: s.step_number)
            next_step = EscalationService._determine_next_step(incident, steps)
            if not next_step:
                continue

            if EscalationService._should_send_step(incident, next_step):
                EscalationService._dispatch_step(db, incident, next_step)
                incident.last_step_sent = next_step.step_number
                processed += 1

        if processed:
            db.commit()
        return processed

    # Internal helpers -----------------------------------------------------

    @staticmethod
    def _determine_next_step(incident: EscalationIncident, steps: List[EscalationStep]) -> Optional[EscalationStep]:
        if not steps:
            return None
        last_step = incident.last_step_sent or 0
        for step in steps:
            if step.step_number > last_step:
                return step
        return None

    @staticmethod
    def _should_send_step(incident: EscalationIncident, step: EscalationStep) -> bool:
        scheduled_time = incident.triggered_at + timedelta(minutes=step.delay_minutes or 0)
        return datetime.utcnow() >= scheduled_time

    @staticmethod
    def _dispatch_step(db: Session, incident: EscalationIncident, step: EscalationStep) -> None:
        recipients = EscalationService._resolve_recipients(db, incident.policy, step)
        if not recipients:
            return

        message_template = step.message_template or f"{incident.policy.name} requires attention."
        metadata = incident.incident_metadata or {}
        for recipient in recipients:
            notification = NotificationCreate(
                title=f"Escalation: {incident.policy.incident_type}",
                message=message_template,
                type=NotificationType.ESCALATION,
                priority=NotificationPriority.HIGH,
                related_id=str(incident.id),
                related_type="escalation_incident",
                action_url=metadata.get("action_url"),
            )
            EscalationService._create_notification_async(db, notification, recipient.id)

    @staticmethod
    def _resolve_recipients(
        db: Session,
        policy: EscalationPolicy,
        step: EscalationStep,
    ) -> List[User]:
        recipients: List[User] = []

        if step.target_user_id:
            user = db.query(User).filter(User.id == step.target_user_id).first()
            if user:
                recipients.append(user)
            return recipients

        if step.target_role == "facility_admin":
            facility = db.query(Facility).filter(Facility.id == policy.facility_id).first()
            if facility and facility.admin_user:
                recipients.append(facility.admin_user)
        elif step.target_role == "organization_manager":
            users = (
                db.query(User)
                .filter(
                    User.facility_id == policy.facility_id,
                    User.user_role == UserRole.FACILITY_ADMIN,
                )
                .all()
            )
            recipients.extend(users)

        return recipients

    @staticmethod
    def _create_notification_async(db: Session, payload: NotificationCreate, user_id: int):
        coro = NotificationService.create_notification(db, payload, user_id, send_email=True, send_push=True)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            asyncio.run(coro)

