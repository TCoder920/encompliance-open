from app.services.usage_billing_service import UsageBillingService
from app.models.ai_usage_log import AIUsageLog
from app.models.user import User
from app.models.role import Role  # noqa: F401
from app.models.task_reference_image import TaskReferenceImage  # noqa: F401


def test_usage_summary(db_session):
    user = User(email="usage@example.com", username="usage", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    UsageBillingService.record_usage(db_session, user.id, tokens_used=100, cost_usd=0.02)
    summary = UsageBillingService.get_usage_summary(db_session, user.id)
    assert summary.month_tokens >= 100
    assert summary.month_cost >= 0.02

