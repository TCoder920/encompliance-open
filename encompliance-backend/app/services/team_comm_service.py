"""
Team Communication Service

Handles channel management, messaging, and email campaign creation for facility admins.
"""

from typing import List
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.team_channel import TeamChannel
from app.models.team_message import TeamMessage
from app.models.email_campaign import EmailCampaign, EmailCampaignStatus
from app.schemas.team_comms import (
    TeamChannelCreate,
    TeamMessageCreate,
    EmailCampaignCreate,
)
from app.utils.owasp_protections import InputSanitizer

logger = logging.getLogger(__name__)


class TeamCommunicationService:
    """Utility methods for chat channels and email campaigns."""

    @staticmethod
    def list_channels(db: Session, facility_id: int) -> List[TeamChannel]:
        return (
            db.query(TeamChannel)
            .filter(TeamChannel.facility_id == facility_id)
            .order_by(TeamChannel.name.asc())
            .all()
        )

    @staticmethod
    def create_channel(
        db: Session,
        facility_id: int,
        current_user_id: int,
        payload: TeamChannelCreate,
    ) -> TeamChannel:
        channel = TeamChannel(
            facility_id=facility_id,
            name=payload.name.strip(),
            description=payload.description,
            is_private=payload.is_private,
            created_by=current_user_id,
        )
        db.add(channel)
        db.commit()
        db.refresh(channel)
        return channel

    @staticmethod
    def list_messages(
        db: Session,
        facility_id: int,
        channel_id: int,
        limit: int = 50,
    ) -> List[TeamMessage]:
        return (
            db.query(TeamMessage)
            .filter(
                TeamMessage.facility_id == facility_id,
                TeamMessage.channel_id == channel_id,
            )
            .order_by(desc(TeamMessage.created_at))
            .limit(limit)
            .all()
        )

    @staticmethod
    def post_message(
        db: Session,
        facility_id: int,
        channel_id: int,
        sender_id: int,
        payload: TeamMessageCreate,
    ) -> TeamMessage:
        sanitized_content = InputSanitizer.sanitize_html(payload.content)
        message = TeamMessage(
            channel_id=channel_id,
            facility_id=facility_id,
            sender_id=sender_id,
            content=sanitized_content,
            attachments=payload.attachments,
            mentions=payload.mentions,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message


class EmailCampaignService:
    """Store admin email campaigns and capture metrics placeholder."""

    @staticmethod
    def create_campaign(
        db: Session,
        facility_id: int,
        creator_id: int,
        payload: EmailCampaignCreate,
    ) -> EmailCampaign:
        campaign = EmailCampaign(
            facility_id=facility_id,
            created_by=creator_id,
            subject=payload.subject.strip(),
            body=payload.body,
            template_type=payload.template_type,
            target_roles=payload.target_roles,
            status=EmailCampaignStatus.SCHEDULED if payload.scheduled_for else EmailCampaignStatus.SENT,
            scheduled_for=payload.scheduled_for,
            delivery_metrics={"status": "queued"},
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

