"""
Customer Service Assistant Service

Triage support tickets, recommend automation attempts, and capture audit data
before escalating to humans. Enforces the "two auto attempts" policy defined in
the development plan.
"""

from __future__ import annotations

import json
import logging
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.schemas.ai_assistance import (
    CustomerServiceTicket,
    CustomerServiceResponse,
)
from app.services.llm_service import get_llm_response
from app.services.usage_billing_service import UsageBillingService
from app.utils.owasp_protections import InputSanitizer

logger = logging.getLogger(__name__)
AUTO_ATTEMPT_LIMIT = 2


class CustomerServiceAssistant:
    """AI helper that triages tickets and attempts lightweight automation."""

    @staticmethod
    async def triage_ticket(
        ticket: CustomerServiceTicket,
        db: Session,
        current_user_id: int,
        prior_attempts: int = 0,
        facility_id: int | None = None,
    ) -> CustomerServiceResponse:
        sanitized_description = InputSanitizer.sanitize_html(ticket.description)
        prompt = (
            "You are an AI support triage bot with compliance guardrails. "
            "Respond only as JSON with keys: classification, recommended_actions[], "
            "auto_resolution_attempted (bool), escalation_required (bool), "
            "customer_ready_summary.\n"
            f"Subject: {ticket.subject}\n"
            f"Priority: {ticket.priority}\n"
            f"Description: {sanitized_description}\n"
            f"Tags: {', '.join(ticket.tags or [])}\n"
            f"Remaining Auto Attempts: {max(0, AUTO_ATTEMPT_LIMIT - prior_attempts)}\n"
        )

        try:
            llm_raw = await get_llm_response(
                prompt=prompt,
                operation_type="support_triage",
                message_history=[],
                db=db,
                current_user_id=current_user_id,
                stream=False,
            )
            CustomerServiceAssistant._record_usage(
                db=db,
                user_id=current_user_id,
                facility_id=facility_id,
                prompt=prompt,
                completion=llm_raw,
            )
            return CustomerServiceAssistant._parse_ai_triage(
                llm_raw, ticket, prior_attempts
            )
        except Exception as exc:
            logger.error("Customer service triage fallback: %s", exc)
            return CustomerServiceAssistant._fallback_response(ticket, prior_attempts)

    @staticmethod
    def _parse_ai_triage(
        llm_raw: str, ticket: CustomerServiceTicket, prior_attempts: int
    ) -> CustomerServiceResponse:
        try:
            payload = json.loads(llm_raw)
        except json.JSONDecodeError:
            return CustomerServiceAssistant._fallback_response(ticket, prior_attempts)

        auto_attempted = bool(payload.get("auto_resolution_attempted"))
        if prior_attempts >= AUTO_ATTEMPT_LIMIT:
            auto_attempted = False

        return CustomerServiceResponse(
            classification=payload.get("classification", "general_inquiry"),
            suggested_actions=payload.get("recommended_actions", []),
            auto_resolution_attempted=auto_attempted,
            requires_human_review=payload.get("escalation_required", True),
            customer_facing_summary=payload.get(
                "customer_ready_summary",
                "We are reviewing your request and will follow up shortly.",
            ),
            audit_context={
                "tags": ticket.tags,
                "priority": ticket.priority,
                "auto_attempts_used": prior_attempts + (1 if auto_attempted else 0),
            },
        )

    @staticmethod
    def _fallback_response(
        ticket: CustomerServiceTicket, prior_attempts: int
    ) -> CustomerServiceResponse:
        requires_human = True
        auto_attempted = False
        if ticket.priority in {"low", "medium"} and prior_attempts < AUTO_ATTEMPT_LIMIT:
            auto_attempted = True
            requires_human = False

        actions = [
            "Acknowledge receipt to customer.",
            "Route transcript and metadata to compliance queue.",
        ]
        if auto_attempted:
            actions.insert(
                0, "Send knowledge-base article covering the reported scenario."
            )

        return CustomerServiceResponse(
            classification="fallback_review",
            suggested_actions=actions,
            auto_resolution_attempted=auto_attempted,
            requires_human_review=requires_human,
            customer_facing_summary="Your request is being reviewed. We will update you shortly.",
            audit_context={
                "fallback": True,
                "auto_attempts_used": prior_attempts + (1 if auto_attempted else 0),
            },
        )

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
        cost = UsageBillingService.estimate_cost(total_tokens, model_name="support-triage")
        UsageBillingService.record_usage(
            db,
            user_id=user_id,
            facility_id=facility_id,
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model_name="support-triage",
            cost_usd=cost,
        )

