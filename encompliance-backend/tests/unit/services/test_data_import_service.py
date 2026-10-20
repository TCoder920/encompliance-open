import pytest

from app.services.data_import_service import DataImportService
from app.schemas.data_import import DataImportRequest
from app.models.user import User, UserRole
from app.models.facility import Facility
from app.models.task_reference_image import TaskReferenceImage  # noqa: F401


def _bootstrap_admin(db_session):
    admin = User(
        email="import-admin@example.com",
        username="importadmin",
        hashed_password="hashed",
        user_role=UserRole.FACILITY_ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    facility = Facility(
        facility_name="Import Facility",
        admin_user_id=admin.id,
        is_active=True,
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)
    admin.facility_id = facility.id
    db_session.commit()
    db_session.refresh(admin)
    return admin


def test_data_import_dry_run(db_session):
    admin = _bootstrap_admin(db_session)
    payload = {
        "notes": [
            {"title": "Restored Note", "content": "Hello"},
        ]
    }
    result = DataImportService.run_import(
        db=db_session,
        facility_admin=admin,
        payload=payload,
        dry_run=True,
    )
    assert result.dry_run is True
    assert result.records_created == 1


def test_data_import_unsupported_section(db_session):
    admin = _bootstrap_admin(db_session)
    payload = {"unknown": []}
    with pytest.raises(ValueError):
        DataImportService.run_import(db_session, admin, payload, dry_run=True)

