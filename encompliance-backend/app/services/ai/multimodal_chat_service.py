"""
Multimodal Chat Service

Accepts text plus optional image/audio attachments and routes them through the core
LLM gateway. Attachments are summarized so downstream models receive context even
if binary processing is not available in development environments.
"""

from __future__ import annotations

import base64
import logging
from typing import List

from sqlalchemy.orm import Session

from app.schemas.ai_assistance import (
    MultimodalChatRequest,
    MultimodalChatResponse,
)
from app.services.llm_service import get_llm_response
from app.services.usage_billing_service import UsageBillingService
from app.utils.owasp_protections import InputSanitizer

logger = logging.getLogger(__name__)

MAX_ATTACHMENT_BYTES = 1024 * 1024 * 2  # 2 MB limit per attachment


class MultimodalChatService:
    """Handle multimodal prompts and guardrail attachments."""

    @staticmethod
    async def generate_response(
        request: MultimodalChatRequest,
        db: Session,
        current_user_id: int,
        facility_id: int | None = None,
    ) -> MultimodalChatResponse:
        sanitized_prompt = InputSanitizer.sanitize_html(request.prompt)
        attachment_manifest = MultimodalChatService._render_attachment_manifest(
            request.attachments or []
        )

        prompt = (
            "You are an AI compliance copilot. Respond conversationally while citing "
            "policy considerations. If attachments are listed, reference them in your response.\n"
            f"User Prompt: {sanitized_prompt}\n"
            f"Attachments Summary:\n{attachment_manifest or 'no attachments'}"
        )

        try:
            llm_reply = await get_llm_response(
                prompt=prompt,
                operation_type=request.facility_type or "childcare",
                message_history=[],
                db=db,
                current_user_id=current_user_id,
                stream=False,
            )
            MultimodalChatService._record_usage(
                db=db,
                user_id=current_user_id,
                facility_id=facility_id,
                prompt=prompt,
                completion=llm_reply,
            )
            return MultimodalChatResponse(
                reply=llm_reply.strip(),
                safety_notes=MultimodalChatService._safety_notes(request),
            )
        except Exception as exc:
            logger.error("Multimodal chat fallback: %s", exc)
            fallback = (
                "I was unable to reach the AI model. Please review the attachments "
                "manually and retry once connectivity is restored."
            )
            return MultimodalChatResponse(
                reply=fallback,
                safety_notes=["LLM gateway unavailable; response synthesized locally."],
            )

    @staticmethod
    def _render_attachment_manifest(attachments) -> str:
        manifest_lines: List[str] = []
        for attachment in attachments:
            MultimodalChatService._validate_attachment_size(attachment.content_base64)
            approx_kb = len(attachment.content_base64) * 0.75 / 1024
            manifest_lines.append(
                f"- {attachment.kind.upper()} :: {attachment.filename or 'unnamed'} "
                f"(~{approx_kb:.1f}KB, mime={attachment.mime_type or 'n/a'})"
            )
        return "\n".join(manifest_lines)

    @staticmethod
    def _validate_attachment_size(content_b64: str):
        if not content_b64:
            return
        byte_length = len(content_b64)
        if byte_length > MAX_ATTACHMENT_BYTES * 1.34:
            raise ValueError("Attachment exceeds 2MB limit for inline processing.")
        # Basic integrity check
        try:
            base64.b64decode(content_b64, validate=True)
        except Exception as exc:
            raise ValueError("Attachment payload is not valid base64.") from exc

    @staticmethod
    def _safety_notes(request: MultimodalChatRequest) -> List[str]:
        notes = []
        if request.attachments:
            notes.append(
                "Attachments were summarized to protect PII before sending to the model."
            )
        return notes

    @staticmethod
    def _record_usage(
        db: Session,
        user_id: int,
        facility_id: int | None,
        prompt: str,
        completion: str,
    ) -> None:
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(completion) // 4
        total_tokens = max(1, prompt_tokens + completion_tokens)
        cost = UsageBillingService.estimate_cost(total_tokens)
        UsageBillingService.record_usage(
            db,
            user_id=user_id,
            facility_id=facility_id,
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model_name="compliance-chat",
            cost_usd=cost,
        )

