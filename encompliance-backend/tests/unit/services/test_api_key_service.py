import pytest
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.facility import Facility
from app.services.api_key_service import api_key_service


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password="hashed",
        full_name="Admin User",
        is_active=True,
        subscription_status="pro",
        user_role=UserRole.FACILITY_ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    facility = Facility(
        facility_name="Test Facility",
        admin_user_id=user.id,
        facility_state="CA",
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)

    user.facility_id = facility.id
    db_session.commit()
    db_session.refresh(user)

    return user


def test_create_and_authenticate_api_key(db_session: Session, admin_user: User):
    api_key, secret = api_key_service.create_api_key(
        db_session,
        owner=admin_user,
        label="ChatGPT",
        scopes=["tasks:read"],
        expires_in_days=30,
        ip_allowlist=None,
    )

    assert secret.startswith("enc_")
    assert api_key.label == "ChatGPT"

    resolved = api_key_service.authenticate_raw_key(
        db_session, raw_key=secret, client_ip="127.0.0.1"
    )
    assert resolved.id == api_key.id


def test_ip_allowlist_enforced(db_session: Session, admin_user: User):
    api_key, secret = api_key_service.create_api_key(
        db_session,
        owner=admin_user,
        label="Restricted",
        scopes=["tasks:read"],
        expires_in_days=30,
        ip_allowlist=["10.0.0.1"],
    )

    with pytest.raises(PermissionError):
        api_key_service.authenticate_raw_key(
            db_session, raw_key=secret, client_ip="127.0.0.1"
        )

    # Allowed IP succeeds
    resolved = api_key_service.authenticate_raw_key(
        db_session, raw_key=secret, client_ip="10.0.0.1"
    )
    assert resolved.id == api_key.id

