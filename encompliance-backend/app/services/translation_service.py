"""
Translation Service
"""

import httpx
import logging

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class TranslationService:
    """Simple wrapper around LibreTranslate."""

    @staticmethod
    async def translate_text(
        text: str,
        source_language: str = "en",
        target_language: str = "es",
    ) -> dict:
        payload = {
            "q": text,
            "source": source_language,
            "target": target_language,
            "format": "text",
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(f"{settings.LIBRETRANSLATE_URL}/translate", json=payload)
                response.raise_for_status()
                data = response.json()
                return {
                    "translated_text": data.get("translatedText", text),
                    "detected_source": data.get("detectedLanguage", source_language),
                }
        except Exception as exc:
            logger.error("Translation failed: %s", exc)
            return {"translated_text": text, "detected_source": source_language}

