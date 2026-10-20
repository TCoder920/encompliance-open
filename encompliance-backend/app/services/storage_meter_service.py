"""
Storage Meter Service

Provides tiered storage quota enforcement, event-based metering, and usage
summaries for facility administrators. This service centralizes all storage
billing logic so API routes and upload services can log usage deltas without
duplicating business rules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.assignment_image import AssignmentImage
from app.models.document import Document
from app.models.facility import Facility
from app.models.operational_task import OperationalTask
from app.models.storage_meter import StorageMeter, StorageUsageEvent
from app.models.task_assignment import TaskAssignment
from app.models.task_reference_image import TaskReferenceImage


class StorageMeterService:
    """
    Enforces tiered storage billing with immutable usage events and monthly rollups.
    """

    # Default quotas per tier (bytes) and overage rates (USD per GB).
    TIER_CONFIG: Dict[str, Dict[str, float]] = {
        "free": {"included_bytes": 5 * 1024 ** 3, "overage_rate": 0.35},
        "pro": {"included_bytes": 25 * 1024 ** 3, "overage_rate": 0.15},
        "enterprise": {"included_bytes": 250 * 1024 ** 3, "overage_rate": 0.05},
    }

    ALERT_THRESHOLDS = {
        "warning": 0.75,
        "critical": 0.9,
    }

    @classmethod
    def log_consumption(
        cls,
        db: Session,
        *,
        facility_id: Optional[int],
        delta_bytes: int,
        resource_type: str,
        resource_id: int,
        user_id: Optional[int] = None,
        metadata: Optional[Dict] = None,
        auto_commit: bool = True,
    ) -> Optional[StorageMeter]:
        """
        Record a storage delta (positive for uploads, negative for deletions).
        """
        if not facility_id or delta_bytes == 0:
            return None

        meter = cls._get_or_create_current_meter(db, facility_id)
        meter.used_bytes = max(0, meter.used_bytes + delta_bytes)
        meter.overage_bytes = max(0, meter.used_bytes - meter.included_bytes)
        meter.alert_level = cls._determine_alert_level(meter)

        usage_event = StorageUsageEvent(
            meter_id=meter.id,
            facility_id=facility_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            delta_bytes=delta_bytes,
            event_metadata=metadata or {},
        )
        db.add(usage_event)

        if auto_commit:
            db.commit()
            db.refresh(meter)
        return meter

    @classmethod
    def get_usage_summary(cls, db: Session, facility_id: int, include_events: bool = True) -> Dict:
        """
        Return the active billing period summary for a facility.
        """
        meter = cls._get_or_create_current_meter(db, facility_id)
        config = cls.TIER_CONFIG.get(meter.tier_name, cls.TIER_CONFIG["pro"])
        percent_used = 0.0
        if meter.included_bytes > 0:
            percent_used = min(1.0, meter.used_bytes / meter.included_bytes)

        summary = {
            "facility_id": facility_id,
            "billing_period_start": meter.billing_period_start,
            "billing_period_end": meter.billing_period_end,
            "tier_name": meter.tier_name,
            "included_bytes": meter.included_bytes,
            "used_bytes": meter.used_bytes,
            "overage_bytes": meter.overage_bytes,
            "percent_used": percent_used,
            "alert_level": meter.alert_level,
            "overage_rate": config["overage_rate"],
            "available_bytes": max(0, meter.included_bytes - meter.used_bytes),
            "recommended_tier": cls._recommend_tier(meter.used_bytes),
        }

        if include_events:
            events = (
                db.query(StorageUsageEvent)
                .filter(StorageUsageEvent.facility_id == facility_id)
                .order_by(StorageUsageEvent.created_at.desc())
                .limit(15)
                .all()
            )
            summary["events"] = events

        return summary

    @classmethod
    def recalculate_facility_usage(cls, db: Session, facility_id: int, auto_commit: bool = True) -> Optional[StorageMeter]:
        """
        Recompute total usage from authoritative sources (documents + images).
        """
        if not facility_id:
            return None

        total_bytes = cls._calculate_raw_usage(db, facility_id)
        meter = cls._get_or_create_current_meter(db, facility_id)
        meter.used_bytes = total_bytes
        meter.overage_bytes = max(0, total_bytes - meter.included_bytes)
        meter.alert_level = cls._determine_alert_level(meter)

        if auto_commit:
            db.commit()
            db.refresh(meter)
        return meter

    @classmethod
    def recalculate_all_facilities(cls, db: Session) -> int:
        """
        Rebuild usage for every active facility. Invoked nightly from cleanup.
        """
        facility_ids = [fid for (fid,) in db.query(Facility.id).filter(Facility.is_active == True).all()]
        updated = 0
        for facility_id in facility_ids:
            meter = cls.recalculate_facility_usage(db, facility_id, auto_commit=False)
            if meter:
                updated += 1
        db.commit()
        return updated

    # Internal helpers -----------------------------------------------------

    @classmethod
    def _get_or_create_current_meter(cls, db: Session, facility_id: int) -> StorageMeter:
        start, end = cls._current_billing_window()
        meter = (
            db.query(StorageMeter)
            .filter(
                StorageMeter.facility_id == facility_id,
                StorageMeter.billing_period_start == start,
            )
            .with_for_update(of=StorageMeter)
            .first()
        )
        if meter:
            return meter

        tier_name = cls._determine_tier(db, facility_id)
        config = cls.TIER_CONFIG.get(tier_name, cls.TIER_CONFIG["pro"])
        meter = StorageMeter(
            facility_id=facility_id,
            billing_period_start=start,
            billing_period_end=end,
            tier_name=tier_name,
            included_bytes=int(config["included_bytes"]),
        )
        db.add(meter)
        db.commit()
        db.refresh(meter)
        return meter

    @staticmethod
    def _current_billing_window(now: Optional[datetime] = None):
        now = now or datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        return start, end

    @classmethod
    def _determine_tier(cls, db: Session, facility_id: int) -> str:
        facility = db.query(Facility).filter(Facility.id == facility_id).first()
        if not facility:
            return "pro"

        if facility.organization_id:
            return "enterprise"

        if facility.admin_user and facility.admin_user.subscription_status == "enterprise":
            return "enterprise"

        if facility.admin_user and facility.admin_user.subscription_status == "pro":
            return "pro"

        return "free"

    @classmethod
    def _determine_alert_level(cls, meter: StorageMeter) -> Optional[str]:
        if meter.included_bytes <= 0:
            return None
        utilization = meter.used_bytes / meter.included_bytes
        if utilization >= cls.ALERT_THRESHOLDS["critical"]:
            return "critical"
        if utilization >= cls.ALERT_THRESHOLDS["warning"]:
            return "warning"
        return None

    @classmethod
    def _calculate_raw_usage(cls, db: Session, facility_id: int) -> int:
        document_bytes = (
            db.query(func.coalesce(func.sum(Document.file_size), 0))
            .filter(Document.facility_id == facility_id, Document.is_deleted == False)
            .scalar()
            or 0
        )

        assignment_bytes = (
            db.query(
                func.coalesce(
                    func.sum(
                        AssignmentImage.file_size + func.coalesce(AssignmentImage.original_file_size, 0)
                    ),
                    0,
                )
            )
            .join(TaskAssignment, AssignmentImage.assignment_id == TaskAssignment.id)
            .join(OperationalTask, TaskAssignment.operational_task_id == OperationalTask.id)
            .filter(OperationalTask.facility_id == facility_id)
            .scalar()
            or 0
        )

        reference_bytes = (
            db.query(
                func.coalesce(
                    func.sum(
                        TaskReferenceImage.file_size + func.coalesce(TaskReferenceImage.original_file_size, 0)
                    ),
                    0,
                )
            )
            .join(OperationalTask, TaskReferenceImage.operational_task_id == OperationalTask.id)
            .filter(OperationalTask.facility_id == facility_id)
            .scalar()
            or 0
        )

        return int(document_bytes + assignment_bytes + reference_bytes)

    @classmethod
    def _recommend_tier(cls, used_bytes: int) -> Optional[str]:
        if used_bytes >= cls.TIER_CONFIG["enterprise"]["included_bytes"] * 0.8:
            return None  # already at top tier
        if used_bytes > cls.TIER_CONFIG["pro"]["included_bytes"]:
            return "enterprise"
        if used_bytes > cls.TIER_CONFIG["free"]["included_bytes"]:
            return "pro"
        return None


