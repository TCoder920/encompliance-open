from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MCPToolDescriptor(BaseModel):
    name: str
    description: str
    scope: str
    input_schema: Dict[str, Any]


class MCPToolListResponse(BaseModel):
    tools: List[MCPToolDescriptor]


class MCPExecuteRequest(BaseModel):
    tool_name: str = Field(..., min_length=3)
    arguments: Dict[str, Any] = Field(default_factory=dict)


class MCPExecuteResponse(BaseModel):
    tool_name: str
    result: Dict[str, Any]
    warnings: Optional[List[str]] = None

