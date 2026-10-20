# Main Application Models
from app.models.user import User
from app.models.document import Document
from app.models.pdf import PDF
from app.models.query_log import QueryLog
from app.models.facility_type import FacilityType, regulation_facility_types
from app.models.regulation import Regulation
from app.models.user_document import UserDocument
from app.models.note import Note
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.push_subscription import PushSubscription
from app.models.notification_settings import NotificationSettings
from app.models.calendar_event import CalendarEvent

# Training Models
from app.models.training_program import TrainingProgram, training_program_facility_types
from app.models.staff_member import StaffMember, StaffRole, StaffStatus
from app.models.training_assignment import TrainingAssignment, AssignmentStatus, AssignmentPriority
from app.models.training_material import TrainingMaterial, MaterialType, MaterialStatus
from app.models.training_completion import TrainingCompletion, CompletionStatus, CertificateStatus

# Policy Models
from app.models.policy import Policy, PolicyCategory, PolicyStatus
from app.models.policy_assignment import PolicyAssignment, PolicyAssignmentStatus, PolicyAssignmentPriority
from app.models.policy_acknowledgment import PolicyAcknowledgment, AcknowledgmentMethod, AcknowledgmentStatus

# Task Management Models
from app.models.operational_task import OperationalTask, TaskType, TaskStatus, TaskPriority, RecurrencePattern
from app.models.task_assignment import TaskAssignment, TaskAssignmentStatus, TaskAssignmentPriority
from app.models.task_reference_image import TaskReferenceImage

# Scheduling Models
from app.models.scheduling import (
    Shift,
    ShiftStatus,
    ShiftRecurrencePattern,
    StaffAvailability,
    AvailabilityStatus,
    TimeOffRequest,
    TimeOffStatus,
    TimeOffCategory,
    ShiftSwapRequest,
    ShiftSwapStatus,
)
from app.models.team_channel import TeamChannel
from app.models.team_message import TeamMessage
from app.models.email_campaign import EmailCampaign, EmailCampaignStatus
from app.models.organization import Organization
from app.models.role import Role, Permission, UserRoleAssignment
from app.models.ai_usage_log import AIUsageLog
from app.models.api_key import APIKey, APIKeyStatus

# Activity Models
from app.models.activity_signup import ActivitySignup, ActivitySignupStatus
from app.models.activity_suggestion import ActivitySuggestion, ActivitySuggestionStatus, ActivitySuggestionVote

# Export Models
from app.models.export_quota import ExportQuota
from app.models.export_request import ExportRequest, ExportStatus, ExportFormat

# Authentication Models
from app.models.token import BlacklistedToken
from app.models.webauthn_credential import WebAuthnCredential
from app.models.user_otp import UserOTP, OTPChannel, OTPPurpose
from app.models.magic_link import MagicLink, MagicLinkPurpose
from app.models.oauth_identity import OAuthIdentity, OAuthProvider
from app.models.signup_session import SignupSession

# Support portal models
from app.models.support_portal_account import SupportPortalAccount
from app.models.audit_log import AuditLog

# New facility management models
from .facility import Facility
from .subscription import Subscription
from .facility_invitation import FacilityInvitation
from .sync_event import SyncEvent
from .calendar_connection import CalendarConnection 

from app.models.assignment_image import AssignmentImage, ImageType, ConversionStatus
from app.models.storage_meter import StorageMeter, StorageUsageEvent
from app.models.staff_directory import StaffFacilityAssignment, StaffTransferRequest
from app.models.escalation import EscalationPolicy, EscalationStep, EscalationIncident
from app.models.activity_audit_log import ActivityAuditLog
from app.models.manager_override_request import ManagerOverrideRequest
from app.models.support_ticket import SupportTicket, SupportTicketComment, SupportAgentProfile

# Export all models for easy importing
__all__ = [
    # ... existing models ...
    'AssignmentImage',
    'ImageType',
    'ConversionStatus',
    'ActivitySignup',
    'ActivitySignupStatus',
    'ActivitySuggestion',
    'ActivitySuggestionStatus',
    'ActivitySuggestionVote',
    'Shift',
    'ShiftStatus',
    'ShiftRecurrencePattern',
    'StaffAvailability',
    'AvailabilityStatus',
    'TimeOffRequest',
    'TimeOffStatus',
    'TimeOffCategory',
    'ShiftSwapRequest',
    'ShiftSwapStatus',
    'TeamChannel',
    'TeamMessage',
    'EmailCampaign',
    'EmailCampaignStatus',
    'Organization',
    'Role',
    'Permission',
    'UserRoleAssignment',
    'AIUsageLog',
    'StorageMeter',
    'StorageUsageEvent',
    'StaffFacilityAssignment',
    'StaffTransferRequest',
    'EscalationPolicy',
    'EscalationStep',
    'EscalationIncident',
    'ActivityAuditLog',
    'ManagerOverrideRequest',
    'SupportTicket',
    'SupportTicketComment',
    'SupportAgentProfile',
    'TaskReferenceImage',
    'APIKey',
    'APIKeyStatus',
    # ... rest of existing models ...
] 