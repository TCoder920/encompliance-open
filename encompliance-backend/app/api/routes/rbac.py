"""
RBAC Routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_facility_admin
from app.schemas.rbac import RoleCreate, RoleResponse, RoleAssignmentCreate
from app.services.rbac_service import RBACService

router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_facility_admin),
):
    return RBACService.create_role(db, payload)


@router.post("/assignments")
async def assign_role(
    payload: RoleAssignmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_facility_admin),
):
    RBACService.assign_role(db, payload)
    return {"status": "assigned"}

