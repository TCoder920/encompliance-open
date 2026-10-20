import json
import pytest

from app.schemas.ai_assistance import FormAssistanceRequest
from app.services.ai.form_assistant_service import FormAssistantService


@pytest.mark.asyncio
async def test_form_assistant_parses_llm(monkeypatch, db_session):
    async def fake_llm_response(**kwargs):
        return json.dumps(
            {
                "summary": "Custom form summary",
                "sections": [
                    {
                        "title": "Section A",
                        "description": "Desc",
                        "fields": [
                            {
                                "name": "field_one",
                                "label": "Field One",
                                "data_type": "text",
                                "required": True,
                                "helper_text": "Enter a value",
                            }
                        ],
                    }
                ],
            }
        )

    monkeypatch.setattr(
        "app.services.ai.form_assistant_service.get_llm_response", fake_llm_response
    )
    request = FormAssistanceRequest(
        form_name="Incident Report",
        form_goal="Capture incident information",
        facility_type="childcare",
        jurisdiction="MD",
        context_summary="Needs to cover injuries and witnesses.",
    )

    response = await FormAssistantService.generate_form_blueprint(
        request, db_session, current_user_id=1
    )

    assert response.summary == "Custom form summary"
    assert len(response.sections) == 1
    assert response.sections[0].fields[0].name == "field_one"


@pytest.mark.asyncio
async def test_form_assistant_fallback(monkeypatch, db_session):
    async def failing_llm(**kwargs):
        raise RuntimeError("downstream error")

    monkeypatch.setattr(
        "app.services.ai.form_assistant_service.get_llm_response", failing_llm
    )
    request = FormAssistanceRequest(
        form_name="Training Acknowledgment",
        form_goal="Record staff acknowledgment",
    )

    response = await FormAssistantService.generate_form_blueprint(
        request, db_session, current_user_id=1
    )

    assert response.sections, "Fallback should return default sections"
    assert "Starter template" in response.summary

