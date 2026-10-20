"""
Google Integration Routes
"""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/auth/google", tags=["google"])
settings = get_settings()


@router.get("/config")
async def get_google_oauth_config():
    return {
        "clientId": settings.GOOGLE_OAUTH_CLIENT_ID,
        "scopes": [
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
    }

