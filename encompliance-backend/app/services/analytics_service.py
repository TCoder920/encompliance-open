"""
Analytics Service
"""

from typing import List
from sqlalchemy.orm import Session

from app.models.facility import Facility
from app.models.staff_member import StaffMember
from app.schemas.analytics import CrossFacilityAnalytics, FacilityMetric


class AnalyticsService:
    """Generates cross-facility rollups."""

    @staticmethod
    def get_cross_facility_metrics(db: Session) -> CrossFacilityAnalytics:
        facilities = db.query(Facility).all()
        metrics: List[FacilityMetric] = []
        staff_total = 0

        for facility in facilities:
            staff_count = (
                db.query(StaffMember)
                .filter(StaffMember.facility_administrator_id == facility.admin_user_id)
                .count()
            )
            staff_total += staff_count
            metrics.append(
                FacilityMetric(
                    facility_id=facility.id,
                    facility_name=facility.facility_name,
                    active_staff=staff_count,
                    open_policies=0,
                )
            )

        return CrossFacilityAnalytics(
            total_facilities=len(facilities),
            staff_count=staff_total,
            policy_distribution_pending=0,
            facilities=metrics,
        )

