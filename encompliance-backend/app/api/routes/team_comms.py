"""
Team Communication Routes

Endpoints for channel management, messaging, and email campaigns.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_facility_admin
from app.models.user import User
from app.schemas.team_comms import (
    TeamChannelCreate,
    TeamChannelResponse,
    TeamMessageCreate,
    TeamMessageResponse,
    EmailCampaignCreate,
    EmailCampaignResponse,
)
from app.services.team_comm_service import TeamCommunicationService, EmailCampaignService

router = APIRouter(prefix="/team-comms", tags=["team-comms"])


@router.get("/channels", response_model=List[TeamChannelResponse])
async def get_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return TeamCommunicationService.list_channels(
        db=db,
        facility_id=current_user.administered_facility.id,
    )


@router.post("/channels", response_model=TeamChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    payload: TeamChannelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return TeamCommunicationService.create_channel(
        db=db,
        facility_id=current_user.administered_facility.id,
        current_user_id=current_user.id,
        payload=payload,
    )


@router.get("/channels/{channel_id}/messages", response_model=List[TeamMessageResponse])
async def get_channel_messages(
    channel_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return TeamCommunicationService.list_messages(
        db=db,
        facility_id=current_user.administered_facility.id,
        channel_id=channel_id,
        limit=limit,
    )


@router.post(
    "/channels/{channel_id}/messages",
    response_model=TeamMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_message(
    channel_id: int,
    payload: TeamMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return TeamCommunicationService.post_message(
        db=db,
        facility_id=current_user.administered_facility.id,
        channel_id=channel_id,
        sender_id=current_user.id,
        payload=payload,
    )


@router.post("/email-campaigns", response_model=EmailCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_email_campaign(
    payload: EmailCampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    return EmailCampaignService.create_campaign(
        db=db,
        facility_id=current_user.administered_facility.id,
        creator_id=current_user.id,
        payload=payload,
    )

