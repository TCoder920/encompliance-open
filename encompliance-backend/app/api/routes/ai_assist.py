"""
AI Assistance Routes

Exposes endpoints for AI form blueprinting, multimodal chat, and customer
service triage. All routes require authenticated facility administrators.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_facility_admin
from app.database import get_db
from app.models.user import User
from app.schemas.ai_assistance import (
    FormAssistanceRequest,
    FormAssistanceResponse,
    MultimodalChatRequest,
    MultimodalChatResponse,
    CustomerServiceTicket,
    CustomerServiceResponse,
)
from app.services.ai import (
    FormAssistantService,
    MultimodalChatService,
    CustomerServiceAssistant,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/forms/assist", response_model=FormAssistanceResponse)
async def generate_form_blueprint(
    request: FormAssistanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    try:
        return await FormAssistantService.generate_form_blueprint(
            request=request,
            db=db,
            current_user_id=current_user.id,
            facility_id=current_user.facility_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to generate form blueprint") from exc


@router.post("/chat/multimodal", response_model=MultimodalChatResponse)
async def multimodal_chat(
    request: MultimodalChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    try:
        return await MultimodalChatService.generate_response(
            request=request,
            db=db,
            current_user_id=current_user.id,
            facility_id=current_user.facility_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to process chat request") from exc


@router.post("/customer-service/triage", response_model=CustomerServiceResponse)
async def triage_customer_ticket(
    ticket: CustomerServiceTicket,
    prior_attempts: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin),
):
    try:
        return await CustomerServiceAssistant.triage_ticket(
            ticket=ticket,
            db=db,
            current_user_id=current_user.id,
            prior_attempts=prior_attempts,
            facility_id=current_user.facility_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to triage ticket") from exc

