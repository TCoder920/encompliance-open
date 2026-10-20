import pytest

from app.services.team_comm_service import TeamCommunicationService, EmailCampaignService
from app.schemas.team_comms import TeamChannelCreate, TeamMessageCreate, EmailCampaignCreate
from app.models.task_reference_image import TaskReferenceImage  # noqa: F401


def _bootstrap_facility_admin(db_session):
    from app.models.user import User, UserRole
    from app.models.facility import Facility

    admin = User(
        email="team-admin@example.com",
        username="teamadmin",
        hashed_password="hashed",
        user_role=UserRole.FACILITY_ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    facility = Facility(
        facility_name="Comms Facility",
        admin_user_id=admin.id,
        is_active=True,
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)
    admin.facility_id = facility.id
    db_session.commit()
    db_session.refresh(admin)

    return admin, facility


def test_channel_and_message_flow(db_session):
    admin, facility = _bootstrap_facility_admin(db_session)
    channel = TeamCommunicationService.create_channel(
        db=db_session,
        facility_id=facility.id,
        current_user_id=admin.id,
        payload=TeamChannelCreate(name="Announcements", description="All hands"),
    )
    assert channel.id is not None

    message = TeamCommunicationService.post_message(
        db=db_session,
        facility_id=facility.id,
        channel_id=channel.id,
        sender_id=admin.id,
        payload=TeamMessageCreate(content="<b>Hello</b> team!"),
    )
    assert "&lt;b&gt;" in message.content  # sanitized


def test_email_campaign_creation(db_session):
    admin, facility = _bootstrap_facility_admin(db_session)
    campaign = EmailCampaignService.create_campaign(
        db=db_session,
        facility_id=facility.id,
        creator_id=admin.id,
        payload=EmailCampaignCreate(
            subject="Policy Update",
            body="Please review the new policy.",
            target_roles=["staff"],
        ),
    )
    assert campaign.status in {"scheduled", "sent"}

