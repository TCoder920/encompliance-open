"""
Activity Audit Service
"""

import csv
import hashlib
import io
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.activity_audit_log import ActivityAuditLog


class ActivityAuditService:
    """Provides append-only audit logging with hash verification."""

    @staticmethod
    def log_event(
        db: Session,
        *,
        actor_user_id: Optional[int],
        facility_id: Optional[int],
        event_type: str,
        description: str,
        metadata: Optional[Dict] = None,
    ) -> ActivityAuditLog:
        prev_entry = db.query(ActivityAuditLog).order_by(ActivityAuditLog.id.desc()).first()
        prev_hash = prev_entry.entry_hash if prev_entry else None

        entry_hash = ActivityAuditService._compute_hash(
            prev_hash,
            actor_user_id,
            facility_id,
            event_type,
            description,
            metadata or {},
        )

        log = ActivityAuditLog(
            actor_user_id=actor_user_id,
            facility_id=facility_id,
            event_type=event_type,
            description=description,
            entry_metadata=metadata,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def list_logs(
        db: Session,
        *,
        facility_id: Optional[int],
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[ActivityAuditLog], int]:
        query = db.query(ActivityAuditLog)
        if facility_id:
            query = query.filter(ActivityAuditLog.facility_id == facility_id)

        total = query.count()
        entries = (
            query.order_by(ActivityAuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return entries, total

    @staticmethod
    def export_logs(db: Session, facility_id: Optional[int]) -> bytes:
        query = db.query(ActivityAuditLog)
        if facility_id:
            query = query.filter(ActivityAuditLog.facility_id == facility_id)

        rows = query.order_by(ActivityAuditLog.created_at.desc()).all()
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["timestamp", "event_type", "description", "actor_user_id", "facility_id", "entry_hash"])
        for row in rows:
            writer.writerow([
                row.created_at.isoformat(),
                row.event_type,
                row.description,
                row.actor_user_id,
                row.facility_id,
                row.entry_hash,
            ])
        return buffer.getvalue().encode("utf-8")

    @staticmethod
    def _compute_hash(
        prev_hash: Optional[str],
        actor_user_id: Optional[int],
        facility_id: Optional[int],
        event_type: str,
        description: str,
        metadata: Dict,
    ) -> str:
        payload = f"{prev_hash or ''}|{actor_user_id or ''}|{facility_id or ''}|{event_type}|{description}|{metadata}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

