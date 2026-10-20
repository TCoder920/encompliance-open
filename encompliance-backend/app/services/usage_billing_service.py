"""
Usage Billing Service
"""

from datetime import datetime
from typing import Dict

from sqlalchemy.orm import Session

from app.models.ai_usage_log import AIUsageLog
from app.schemas.usage_billing import UsageSummary


class UsageBillingService:
    """Aggregates AI usage for billing."""

    MODEL_RATES = {
        "default": 0.000002,
        "gpt-4o-mini": 0.000005,
    }

    @staticmethod
    def record_usage(
        db: Session,
        user_id: int,
        tokens_used: int,
        cost_usd: float,
        facility_id: int | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        model_name: str | None = None,
    ):
        log = AIUsageLog(
            user_id=user_id,
            facility_id=facility_id,
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens or 0,
            completion_tokens=completion_tokens or 0,
            cost_usd=cost_usd,
            model_name=model_name,
        )
        db.add(log)
        db.commit()
        db.refresh(log)

    @staticmethod
    def estimate_cost(tokens: int, model_name: str | None = None) -> float:
        if tokens <= 0:
            return 0.0
        rate = UsageBillingService.MODEL_RATES.get(model_name or "default", UsageBillingService.MODEL_RATES["default"])
        return round(tokens * rate, 6)

    @staticmethod
    def get_usage_summary(db: Session, user_id: int) -> UsageSummary:
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        logs = (
            db.query(AIUsageLog)
            .filter(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at >= start_of_month,
            )
            .order_by(AIUsageLog.created_at.desc())
            .all()
        )
        month_tokens = sum(log.tokens_used for log in logs)
        month_cost = sum(log.cost_usd for log in logs)
        return UsageSummary(
            month_tokens=month_tokens,
            month_cost=round(month_cost, 4),
            logs=logs,
        )

    @staticmethod
    def get_facility_summary(db: Session, facility_id: int) -> Dict[str, float]:
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        logs = (
            db.query(AIUsageLog)
            .filter(
                AIUsageLog.facility_id == facility_id,
                AIUsageLog.created_at >= start_of_month,
            )
            .all()
        )
        total_tokens = sum(log.tokens_used for log in logs)
        total_cost = sum(log.cost_usd for log in logs)
        return {"tokens": total_tokens, "cost": round(total_cost, 4)}

