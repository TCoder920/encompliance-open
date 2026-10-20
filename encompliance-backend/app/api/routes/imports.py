"""
Data Import Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_facility_admin
from app.models.user import User
from app.schemas.data_import import DataImportRequest, DataImportResult
from app.services.data_import_service import DataImportService

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/data", response_model=DataImportResult)
async def import_data(
    request: DataImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    facility = current_user.administered_facility
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found for admin.")

    try:
        return DataImportService.run_import(
            db=db,
            facility_admin=current_user,
            payload=request.payload,
            dry_run=request.dry_run,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Import failed")

