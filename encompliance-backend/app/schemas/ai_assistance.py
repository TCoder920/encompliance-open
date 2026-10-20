"""
AI Assistance Schemas

Structured request/response models for AI form assistance, multimodal chat,
and customer service automation endpoints.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class FormFieldDescriptor(BaseModel):
    name: str
    label: str
    data_type: str = Field(..., description="UI data type such as text/email/select.")
    required: bool = True
    helper_text: Optional[str] = None
    validations: Optional[List[str]] = None


class FormSection(BaseModel):
    title: str
    description: Optional[str] = None
    fields: List[FormFieldDescriptor]


class FormAssistanceRequest(BaseModel):
    form_name: str = Field(..., max_length=200)
    form_goal: str = Field(..., max_length=2000)
    facility_type: Optional[str] = Field(None, max_length=100)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    context_summary: Optional[str] = Field(None, max_length=4000)


class FormAssistanceResponse(BaseModel):
    summary: str
    sections: List[FormSection]
    compliance_notes: List[str] = Field(default_factory=list)


class AttachmentPayload(BaseModel):
    kind: Literal["image", "audio"]
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    content_base64: str = Field(..., description="Base64 encoded payload (no data URI).")


class MultimodalChatRequest(BaseModel):
    prompt: str = Field(..., max_length=4000)
    facility_type: Optional[str] = None
    attachments: List[AttachmentPayload] = Field(default_factory=list)


class MultimodalChatResponse(BaseModel):
    reply: str
    safety_notes: List[str] = Field(default_factory=list)


class CustomerServiceTicket(BaseModel):
    subject: str = Field(..., max_length=200)
    description: str = Field(..., max_length=6000)
    priority: Literal["low", "medium", "high", "urgent"] = "low"
    tags: List[str] = Field(default_factory=list)


class CustomerServiceResponse(BaseModel):
    classification: str
    suggested_actions: List[str]
    auto_resolution_attempted: bool
    requires_human_review: bool
    customer_facing_summary: str
    audit_context: Optional[dict] = None

