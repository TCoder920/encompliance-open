"""
Form Assistant Service

Provides AI-powered blueprints for compliance forms requested by facility
administrators. The service sanitizes inputs, calls the LLM gateway, and
returns structured section/field metadata with sensible fallbacks.
"""

from __future__ import annotations

import json
import logging
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.schemas.ai_assistance import (
    FormAssistanceRequest,
    FormAssistanceResponse,
    FormSection,
    FormFieldDescriptor,
)
from app.services.llm_service import get_llm_response
from app.services.usage_billing_service import UsageBillingService
from app.utils.owasp_protections import InputSanitizer

logger = logging.getLogger(__name__)


class FormAssistantService:
    """Generate AI-assisted form layouts with compliance hints."""

    @staticmethod
    async def generate_form_blueprint(
        request: FormAssistanceRequest,
        db: Session,
        current_user_id: int,
        facility_id: int | None = None,
    ) -> FormAssistanceResponse:
        sanitized_goal = InputSanitizer.sanitize_html(request.form_goal)
        sanitized_context = (
            InputSanitizer.sanitize_html(request.context_summary)
            if request.context_summary
            else ""
        )
        jurisdiction = request.jurisdiction or "national"

        prompt = (
            "You are a compliance program form architect. "
            "Return JSON describing form sections for the following request.\n"
            f"Form Name: {request.form_name}\n"
            f"Goal: {sanitized_goal}\n"
            f"Facility Type: {request.facility_type or 'general childcare'}\n"
            f"Jurisdiction: {jurisdiction}\n"
            f"Context: {sanitized_context or 'Not provided'}\n"
            "Respond strictly as JSON with keys: summary, sections[].title, "
            "sections[].description, sections[].fields[]."
            "fields require: name, label, data_type, required (bool), helper_text.\n"
        )

        try:
            llm_raw = await get_llm_response(
                prompt=prompt,
                operation_type=request.facility_type or "childcare",
                message_history=[],
                db=db,
                current_user_id=current_user_id,
                stream=False,
            )
            FormAssistantService._record_usage(
                db=db,
                user_id=current_user_id,
                facility_id=facility_id,
                prompt=prompt,
                completion=llm_raw,
                model_name="gpt-4o-mini",
            )
            return FormAssistantService._parse_ai_blueprint(llm_raw, request)
        except Exception as exc:
            logger.warning("AI form assistant fallback triggered: %s", exc)
            return FormAssistantService._fallback_blueprint(request)

    @staticmethod
    def _parse_ai_blueprint(llm_raw: str, request: FormAssistanceRequest) -> FormAssistanceResponse:
        try:
            payload = json.loads(llm_raw)
        except json.JSONDecodeError:
            logger.debug("Failed to parse AI JSON, using fallback.")
            return FormAssistantService._fallback_blueprint(request)

        sections_payload = payload.get("sections", [])
        sections: List[FormSection] = []
        for section in sections_payload:
            fields_payload = section.get("fields", [])
            fields = [
                FormFieldDescriptor(
                    name=field.get("name", f"field_{idx}"),
                    label=field.get("label", "Untitled Field"),
                    data_type=field.get("data_type", "text"),
                    required=bool(field.get("required", True)),
                    helper_text=field.get("helper_text"),
                    validations=field.get("validations", []),
                )
                for idx, field in enumerate(fields_payload, start=1)
            ]
            sections.append(
                FormSection(
                    title=section.get("title", "General Information"),
                    description=section.get("description"),
                    fields=fields,
                )
            )

        summary = payload.get(
            "summary",
            f"Auto-generated sections for {request.form_name}. Review before publishing.",
        )

        return FormAssistanceResponse(
            summary=summary,
            sections=sections or FormAssistantService._fallback_sections(request),
            compliance_notes=payload.get("compliance_notes", []),
        )

    @staticmethod
    def _fallback_blueprint(request: FormAssistanceRequest) -> FormAssistanceResponse:
        return FormAssistanceResponse(
            summary=f"Starter template for {request.form_name}. Customize per facility policy.",
            sections=FormAssistantService._fallback_sections(request),
            compliance_notes=[
                "Verify state-specific retention policies before publishing.",
                "Ensure personally identifiable information (PII) fields are encrypted at rest.",
            ],
        )

    @staticmethod
    def _fallback_sections(request: FormAssistanceRequest) -> List[FormSection]:
        return [
            FormSection(
                title="Submitter Information",
                description="Capture who is completing the form for audit tracking.",
                fields=[
                    FormFieldDescriptor(
                        name="submitter_name",
                        label="Full Name",
                        data_type="text",
                        required=True,
                        helper_text="Legal name as shown on HR records.",
                    ),
                    FormFieldDescriptor(
                        name="role",
                        label="Role / Title",
                        data_type="text",
                        required=True,
                    ),
                    FormFieldDescriptor(
                        name="contact_email",
                        label="Contact Email",
                        data_type="email",
                        required=True,
                        validations=["must_be_work_email"],
                    ),
                ],
            ),
            FormSection(
                title="Program Details",
                description=f"Key details supporting the {request.form_goal.lower()} goal.",
                fields=[
                    FormFieldDescriptor(
                        name="program_area",
                        label="Program Area",
                        data_type="select",
                        required=True,
                        helper_text="Select the impacted compliance program.",
                    ),
                    FormFieldDescriptor(
                        name="effective_date",
                        label="Effective Date",
                        data_type="date",
                        required=False,
                    ),
                    FormFieldDescriptor(
                        name="supporting_notes",
                        label="Supporting Notes",
                        data_type="textarea",
                        required=False,
                    ),
                ],
            ),
        ]

    @staticmethod
    def _record_usage(
        db: Session,
        user_id: int,
        facility_id: int | None,
        prompt: str,
        completion: str,
        model_name: str,
    ) -> None:
        prompt_tokens = FormAssistantService._estimate_tokens(prompt)
        completion_tokens = FormAssistantService._estimate_tokens(completion)
        total_tokens = prompt_tokens + completion_tokens
        cost = UsageBillingService.estimate_cost(total_tokens, model_name=model_name)
        UsageBillingService.record_usage(
            db,
            user_id=user_id,
            facility_id=facility_id,
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model_name=model_name,
            cost_usd=cost,
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

