from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app import main
from app.database import SessionLocal
from app.models.facility import Facility
from app.models.operational_task import OperationalTask, TaskType
from app.models.user import User, UserRole
from app.services.api_key_service import api_key_service

client = TestClient(main.app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def facility_admin(db):
    user = User(
        email="mcp-admin@example.com",
        username="mcp_admin",
        hashed_password="hashed",
        full_name="MCP Admin",
        is_active=True,
        subscription_status="pro",
        user_role=UserRole.FACILITY_ADMIN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    facility = Facility(
        facility_name="MCP Facility",
        admin_user_id=user.id,
        facility_state="TX",
    )
    db.add(facility)
    db.commit()
    db.refresh(facility)

    user.facility_id = facility.id
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def api_key_header(db, facility_admin):
    api_key, secret = api_key_service.create_api_key(
        db,
        owner=facility_admin,
        label="GPT",
        scopes=["tasks:read", "ai:forms"],
        expires_in_days=30,
        ip_allowlist=None,
    )
    return {"X-API-Key": secret}, api_key


@pytest.fixture
def seeded_tasks(db, facility_admin):
    task = OperationalTask(
        title="Deep Clean Kitchen",
        description="Full sanitation checklist",
        task_type=TaskType.ONE_TIME.value,
        facility_id=facility_admin.facility_id,
        created_by=facility_admin.id,
        start_date=datetime.utcnow(),
    )
    db.add(task)
    db.commit()
    return [task]


def test_list_tools(api_key_header):
    headers, _ = api_key_header
    response = client.post("/api/v1/mcp/tools/list", headers=headers)
    assert response.status_code == 200
    tools = response.json()["tools"]
    assert any(tool["name"] == "listOperationalTasks" for tool in tools)


def test_execute_list_operational_tasks(api_key_header, seeded_tasks):
    headers, _ = api_key_header
    response = client.post(
        "/api/v1/mcp/tools/execute",
        headers=headers,
        json={"tool_name": "listOperationalTasks", "arguments": {"limit": 5}},
    )
    assert response.status_code == 200
    payload = response.json()["result"]
    assert payload["count"] == 1
    assert payload["tasks"][0]["title"] == "Deep Clean Kitchen"


def test_execute_form_blueprint(monkeypatch, api_key_header):
    headers, _ = api_key_header
    mock_result = {"sections": ["Intro"], "status": "ok"}
    monkeypatch.setattr(
        "app.mcp.server.FormAssistantService.generate_form_blueprint",
        AsyncMock(return_value=mock_result),
    )

    response = client.post(
        "/api/v1/mcp/tools/execute",
        headers=headers,
        json={
            "tool_name": "generateFormBlueprint",
            "arguments": {
                "form_context": {
                    "form_name": "Daily Kitchen Checklist",
                    "form_goal": "Provide a step-by-step sanitation workflow.",
                    "facility_type": "child_care"
                }
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["result"] == mock_result

