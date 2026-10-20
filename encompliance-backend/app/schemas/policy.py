"""
Policy Schemas Module

This module defines Pydantic schemas for policy management API endpoints.
Includes schemas for policies, assignments, and acknowledgments.

Key functionalities:
- Policy CRUD operation schemas
- Policy assignment schemas
- Policy acknowledgment schemas
- Validation and response models

Dependencies:
- pydantic: For data validation and serialization
- datetime: For timestamp handling
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class PolicyCategory(str, Enum):
    SAFETY = "safety"
    HR = "hr"
    OPERATIONS = "operations"
    COMPLIANCE = "compliance"
    TRAINING = "training"
    SECURITY = "security"
    QUALITY = "quality"
    EMERGENCY = "emergency"

class PolicyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"

class PolicyAssignmentStatus(str, Enum):
    ASSIGNED = "assigned"
    ACKNOWLEDGED = "acknowledged"
    OVERDUE = "overdue"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class PolicyAssignmentPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AcknowledgmentMethod(str, Enum):
    DIGITAL_SIGNATURE = "digital_signature"
    CHECKBOX_CONFIRMATION = "checkbox_confirmation"
    VERBAL_CONFIRMATION = "verbal_confirmation"
    WRITTEN_SIGNATURE = "written_signature"

class AcknowledgmentStatus(str, Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    OVERDUE = "overdue"
    EXPIRED = "expired"

# Policy schemas
class PolicyBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: Optional[PolicyCategory] = None
    document_url: Optional[str] = Field(None, max_length=500)
    content_summary: Optional[str] = None
    version: str = Field(default="1.0", max_length=50)
    effective_date: datetime
    expiry_date: Optional[datetime] = None
    requires_acknowledgment: bool = True
    acknowledgment_deadline_days: int = Field(default=30, ge=1, le=365)
    auto_assign_new_staff: bool = False
    acknowledgment_reminder_days: Optional[str] = "[30, 14, 7, 1]"
    regulatory_reference: Optional[str] = Field(None, max_length=255)
    compliance_level: str = Field(default="mandatory", max_length=50)

class PolicyCreate(PolicyBase):
    document_id: Optional[int] = None
    supersedes_policy_id: Optional[int] = None

class PolicyUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[PolicyCategory] = None
    document_id: Optional[int] = None
    document_url: Optional[str] = Field(None, max_length=500)
    content_summary: Optional[str] = None
    version: Optional[str] = Field(None, max_length=50)
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    supersedes_policy_id: Optional[int] = None
    requires_acknowledgment: Optional[bool] = None
    acknowledgment_deadline_days: Optional[int] = Field(None, ge=1, le=365)
    auto_assign_new_staff: Optional[bool] = None
    acknowledgment_reminder_days: Optional[str] = None
    regulatory_reference: Optional[str] = Field(None, max_length=255)
    compliance_level: Optional[str] = Field(None, max_length=50)
    status: Optional[PolicyStatus] = None
    is_active: Optional[bool] = None

class Policy(PolicyBase):
    id: int
    document_id: Optional[int] = None
    supersedes_policy_id: Optional[int] = None
    status: PolicyStatus = PolicyStatus.DRAFT
    is_active: bool = True
    created_by: int
    facility_administrator_id: int
    approved_by: Optional[int] = None
    approved_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_expired: bool = False
    is_effective: bool = False
    days_until_expiry: Optional[int] = None
    
    class Config:
        from_attributes = True

# Policy Assignment schemas
class PolicyAssignmentBase(BaseModel):
    due_date: datetime
    priority: PolicyAssignmentPriority = PolicyAssignmentPriority.MEDIUM
    assignment_reason: Optional[str] = Field(None, max_length=255)
    custom_message: Optional[str] = None
    requires_immediate_attention: bool = False
    is_mandatory: bool = True
    compliance_deadline: Optional[datetime] = None
    regulatory_requirement: Optional[str] = Field(None, max_length=255)

class PolicyAssignmentCreate(PolicyAssignmentBase):
    policy_id: int
    staff_member_ids: List[int]  # Support bulk assignment
    assignment_notes: Optional[str] = None

class PolicyAssignmentUpdate(BaseModel):
    due_date: Optional[datetime] = None
    priority: Optional[PolicyAssignmentPriority] = None
    status: Optional[PolicyAssignmentStatus] = None
    assignment_reason: Optional[str] = Field(None, max_length=255)
    custom_message: Optional[str] = None
    requires_immediate_attention: Optional[bool] = None
    assignment_notes: Optional[str] = None
    completion_notes: Optional[str] = None
    admin_notes: Optional[str] = None
    is_mandatory: Optional[bool] = None
    compliance_deadline: Optional[datetime] = None
    regulatory_requirement: Optional[str] = Field(None, max_length=255)

class PolicyAssignment(PolicyAssignmentBase):
    id: int
    policy_id: int
    staff_member_id: int
    assigned_by: int
    status: PolicyAssignmentStatus = PolicyAssignmentStatus.ASSIGNED
    assigned_date: datetime
    acknowledged_date: Optional[datetime] = None
    viewed_date: Optional[datetime] = None
    time_spent_reading: Optional[int] = None
    escalation_sent: bool = False
    escalation_date: Optional[datetime] = None
    escalation_recipient: Optional[int] = None
    assignment_notes: Optional[str] = None
    completion_notes: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_overdue: bool = False
    days_until_due: Optional[int] = None
    days_overdue: int = 0
    is_acknowledged: bool = False
    
    class Config:
        from_attributes = True

# Policy Acknowledgment schemas
class PolicyAcknowledgmentBase(BaseModel):
    acknowledgment_method: AcknowledgmentMethod = AcknowledgmentMethod.DIGITAL_SIGNATURE
    digital_signature: Optional[str] = None
    signature_metadata: Optional[Dict[str, Any]] = None
    acknowledgment_text: Optional[str] = None
    witness_name: Optional[str] = Field(None, max_length=255)
    witness_signature: Optional[str] = None
    notes: Optional[str] = None

class PolicyAcknowledgmentCreate(PolicyAcknowledgmentBase):
    policy_assignment_id: int
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)
    device_fingerprint: Optional[str] = Field(None, max_length=255)
    geolocation: Optional[Dict[str, Any]] = None

class PolicyAcknowledgmentUpdate(BaseModel):
    status: Optional[AcknowledgmentStatus] = None
    verification_notes: Optional[str] = None
    compliance_score: Optional[int] = Field(None, ge=0, le=100)
    requires_reacknowledgment: Optional[bool] = None
    reacknowledgment_reason: Optional[str] = Field(None, max_length=255)

class PolicyAcknowledgment(PolicyAcknowledgmentBase):
    id: int
    policy_id: int
    staff_member_id: int
    policy_assignment_id: Optional[int] = None
    acknowledged_date: Optional[datetime] = None
    status: AcknowledgmentStatus = AcknowledgmentStatus.PENDING
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    geolocation: Optional[Dict[str, Any]] = None
    verified_by: Optional[int] = None
    verification_date: Optional[datetime] = None
    verification_notes: Optional[str] = None
    is_current: bool = True
    compliance_score: Optional[int] = None
    requires_reacknowledgment: bool = False
    reacknowledgment_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_overdue: bool = False
    days_overdue: int = 0
    is_verified: bool = False
    
    class Config:
        from_attributes = True

# Dashboard and Analytics schemas
class PolicyDashboard(BaseModel):
    total_policies: int
    active_policies: int
    draft_policies: int
    expired_policies: int
    total_assignments: int
    pending_acknowledgments: int
    overdue_acknowledgments: int
    acknowledgment_rate: float
    policies_expiring_soon: int
    recent_acknowledgments: List[PolicyAcknowledgment]
    overdue_assignments: List[PolicyAssignment]

class StaffPolicyProgress(BaseModel):
    staff_member_id: int
    staff_name: str
    department: Optional[str]
    assigned_policies: List[PolicyAssignment]
    acknowledged_policies: List[PolicyAcknowledgment]
    overdue_count: int
    acknowledgment_rate: float
    next_due_date: Optional[datetime]

class PolicyAnalytics(BaseModel):
    acknowledgment_rates_by_policy: Dict[str, float]
    acknowledgment_rates_by_department: Dict[str, float]
    overdue_trends: List[Dict[str, Any]]
    policy_expiry_forecast: List[Dict[str, Any]]
    compliance_metrics: Dict[str, Any]
    summary_stats: Dict[str, Any]

# Compliance Report schemas
class PolicyComplianceReport(BaseModel):
    report_type: str
    generated_at: datetime
    filters: Dict[str, Any]
    data: List[Dict[str, Any]]
    summary: Dict[str, Any] 