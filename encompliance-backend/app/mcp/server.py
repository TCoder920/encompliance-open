"""
Model Context Protocol facade
-----------------------------

Exposes a lightweight MCP-compatible tool surface that remote GPT-style
clients can call once they present a valid EnCompliance API key.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.api_key import APIKey
from app.models.operational_task import OperationalTask
from app.models.user import User
from app.schemas.ai_assistance import FormAssistanceRequest
from app.schemas.mcp import (
    MCPExecuteRequest,
    MCPExecuteResponse,
    MCPToolDescriptor,
    MCPToolListResponse,
)
from app.services.ai import FormAssistantService
from app.services.api_key_service import api_key_service
from app.utils.rate_limiter import RateLimitExceeded, rate_limiter

router = APIRouter(prefix="/mcp", tags=["mcp"])
client_logger = logging.getLogger("client")


@dataclass
class AuthContext:
    api_key: APIKey
    user: User
    client_ip: str


ToolHandler = Callable[..., Awaitable[Dict[str, Any]]]


class MCPToolDefinition:
    def __init__(self, *, descriptor: MCPToolDescriptor, scope: str, handler: ToolHandler):
        self.descriptor = descriptor
        self.scope = scope
        self.handler = handler


class MCPToolRegistry:
    _tools: Dict[str, MCPToolDefinition] = {}

    @classmethod
    def register(cls, definition: MCPToolDefinition) -> None:
        cls._tools[definition.descriptor.name] = definition

    @classmethod
    def available_descriptors(cls, scopes: List[str]) -> List[MCPToolDescriptor]:
        allowed = set(scopes or [])
        return [
            tool.descriptor
            for tool in cls._tools.values()
            if tool.scope in allowed
        ]

    @classmethod
    def get(cls, name: str) -> MCPToolDefinition:
        tool = cls._tools.get(name)
        if not tool:
            raise KeyError(name)
        return tool


async def list_operational_tasks_handler(
    *,
    arguments: Dict[str, Any],
    db: Session,
    ctx: AuthContext,
) -> Dict[str, Any]:
    facility_id = ctx.api_key.facility_id or ctx.user.facility_id
    if not facility_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API key is not mapped to a facility.")

    limit = arguments.get("limit", 10)
    try:
        limit = max(1, min(int(limit), 50))
    except (ValueError, TypeError):
        limit = 10

    tasks = (
        db.query(OperationalTask)
        .filter(OperationalTask.facility_id == facility_id)
        .order_by(OperationalTask.start_date.asc())
        .limit(limit)
        .all()
    )

    payload = [
        {
            "id": task.id,
            "title": task.title,
            "taskType": task.task_type,
            "priority": task.priority,
            "startDate": task.start_date.isoformat() if task.start_date else None,
            "isRecurring": task.is_recurring,
        }
        for task in tasks
    ]

    return {"tasks": payload, "count": len(payload)}


async def form_blueprint_handler(
    *,
    arguments: Dict[str, Any],
    db: Session,
    ctx: AuthContext,
) -> Dict[str, Any]:
    facility_id = ctx.api_key.facility_id or ctx.user.facility_id
    if not facility_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API key is not mapped to a facility.")

    form_context = arguments.get("form_context")
    if not form_context:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="form_context is required.")

    request_model = FormAssistanceRequest(**form_context)
    response = await FormAssistantService.generate_form_blueprint(
        request=request_model,
        db=db,
        current_user_id=ctx.user.id,
        facility_id=facility_id,
    )
    return jsonable_encoder(response)


MCPToolRegistry.register(
    MCPToolDefinition(
        descriptor=MCPToolDescriptor(
            name="listOperationalTasks",
            description="Return active operational tasks for the API key's facility.",
            scope="tasks:read",
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "description": "Maximum number of tasks to return (default 10).",
                    }
                },
            },
        ),
        scope="tasks:read",
        handler=list_operational_tasks_handler,
    )
)

MCPToolRegistry.register(
    MCPToolDefinition(
        descriptor=MCPToolDescriptor(
            name="generateFormBlueprint",
            description="Invoke the AI form assistant to draft a compliance form template.",
            scope="ai:forms",
            input_schema={
                "type": "object",
                "properties": {
                    "form_context": {
                        "type": "object",
                        "description": "Payload accepted by the /ai/forms/assist endpoint.",
                    }
                },
                "required": ["form_context"],
            },
        ),
        scope="ai:forms",
        handler=form_blueprint_handler,
    )
)


def authenticate_request(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> AuthContext:
    client_ip = request.client.host if request.client else "unknown"
    try:
        api_key = api_key_service.authenticate_raw_key(db, raw_key=x_api_key, client_ip=client_ip)
    except (ValueError, PermissionError) as exc:
        client_logger.warning("[MCP][denied] reason=%s ip=%s", exc, client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    try:
        rate_limiter.hit(f"mcp:{api_key.id}", limit=60, window_seconds=60)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    user = db.query(User).filter(User.id == api_key.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key owner no longer exists.")

    scopes = ",".join(api_key.scopes or [])
    client_logger.info("[MCP][auth] prefix=%s ip=%s scopes=%s", api_key.prefix, client_ip, scopes)

    return AuthContext(api_key=api_key, user=user, client_ip=client_ip)


@router.post("/tools/list", response_model=MCPToolListResponse)
def list_tools(
    ctx: AuthContext = Depends(authenticate_request),
):
    tools = MCPToolRegistry.available_descriptors(ctx.api_key.scopes or [])
    client_logger.info("[MCP][list] prefix=%s ip=%s tools=%d", ctx.api_key.prefix, ctx.client_ip, len(tools))
    return MCPToolListResponse(tools=tools)


@router.post("/tools/execute", response_model=MCPExecuteResponse)
async def execute_tool(
    payload: MCPExecuteRequest,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(authenticate_request),
):
    try:
        tool = MCPToolRegistry.get(payload.tool_name)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found.")

    if tool.scope not in (ctx.api_key.scopes or []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key missing required scope.")

    result = await tool.handler(arguments=payload.arguments, db=db, ctx=ctx)
    client_logger.info(
        "[MCP][execute] prefix=%s ip=%s tool=%s",
        ctx.api_key.prefix,
        ctx.client_ip,
        payload.tool_name,
    )
    return MCPExecuteResponse(tool_name=tool.descriptor.name, result=result)

