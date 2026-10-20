"""
Enterprise Audit Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.audit import ActivityAuditEntry
from app.services.activity_audit_service import ActivityAuditService

router = APIRouter(prefix="/enterprise/audit", tags=["audit"])


def _facility_context(current_user: User) -> int:
    if not current_user.is_facility_admin or not current_user.administered_facility:
        raise HTTPException(status_code=403, detail="Facility admin access required.")
    return current_user.administered_facility.id


@router.get("/logs", response_model=dict)
async def list_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=10, le=200),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility_id = _facility_context(current_user)
    entries, total = ActivityAuditService.list_logs(db, facility_id=facility_id, page=page, page_size=page_size)
    return {
        "items": [ActivityAuditEntry.from_orm(entry) for entry in entries],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/export")
async def export_logs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    facility_id = _facility_context(current_user)
    payload = ActivityAuditService.export_logs(db, facility_id)
    return StreamingResponse(
        iter([payload]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-log.csv"},
    )

