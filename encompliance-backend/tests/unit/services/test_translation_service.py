import pytest
import httpx

from app.services.translation_service import TranslationService


@pytest.mark.asyncio
async def test_translation_service_handles_failure(monkeypatch):
    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            raise httpx.HTTPError("network error")

    monkeypatch.setattr("app.services.translation_service.httpx.AsyncClient", MockClient)
    result = await TranslationService.translate_text("hello world", "en", "es")
    assert result["translated_text"] == "hello world"

