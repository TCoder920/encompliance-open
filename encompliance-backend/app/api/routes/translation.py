"""
Translation Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.translation import TranslationRequest, TranslationResponse
from app.services.translation_service import TranslationService
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/translation", tags=["translation"])


@router.post("/", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    current_user=Depends(get_current_active_user),
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    result = await TranslationService.translate_text(
        text=request.text,
        source_language=request.source_language,
        target_language=request.target_language,
    )
    return TranslationResponse(**result)

