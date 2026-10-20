import pytest

from app.services.rbac_service import RBACService
from app.schemas.rbac import RoleCreate, RoleAssignmentCreate
from app.models.user import User, UserRole
from app.models.facility import Facility
from app.models.role import Role
from app.models.task_reference_image import TaskReferenceImage  # noqa: F401


def _bootstrap_admin(db_session):
    admin = User(
        email="rbac@example.com",
        username="rbac",
        hashed_password="hashed",
        user_role=UserRole.FACILITY_ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    facility = Facility(
        facility_name="RBAC Facility",
        admin_user_id=admin.id,
        is_active=True,
    )
    db_session.add(facility)
    db_session.commit()
    return admin, facility


def test_create_role_and_assign(db_session):
    admin, facility = _bootstrap_admin(db_session)
    role = RBACService.create_role(
        db_session,
        RoleCreate(name="auditor", description="Audits records", permissions=["view_reports"]),
    )
    assert isinstance(role, Role)

    assignment = RBACService.assign_role(
        db_session,
        RoleAssignmentCreate(user_id=admin.id, role_id=role.id, facility_id=facility.id),
    )
    assert assignment.role_id == role.id

