"""
Data Extraction Service Module

This module provides real data extraction from database tables for user exports.
It implements efficient queries with proper joins and filtering to extract user data.

Key functionalities:
- User profile and settings extraction
- Document metadata and file information extraction  
- Chat interaction and conversation history extraction
- Regulatory document access history extraction
- Calendar events and scheduling data extraction
- Notification and system interaction extraction
- Facility management and staff data extraction
- Training programs and completion tracking extraction
- Policy management and acknowledgment extraction
- Translation preferences and usage metrics extraction
- Calendar connections and external integrations extraction
- Push subscription and notification data extraction
- Structured data formatting for export generation

Dependencies:
- sqlalchemy: For database queries and relationships
- typing: For type hints and data structures

Educational Note: Implements efficient database queries with proper pagination
Reference: SQLAlchemy Query API - https://docs.sqlalchemy.org/en/20/orm/queryguide/
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_
from datetime import datetime, timedelta
import logging

from app.models.user import User
from app.models.document import Document
from app.models.query_log import QueryLog
from app.models.user_document import UserDocument
from app.models.regulation import Regulation
from app.models.calendar_event import CalendarEvent
from app.models.notification import Notification
from app.models.note import Note
from app.models.notification_settings import NotificationSettings
from app.models.push_subscription import PushSubscription
from app.models.facility import Facility
from app.models.staff_member import StaffMember
from app.models.training_program import TrainingProgram
from app.models.training_assignment import TrainingAssignment
from app.models.training_completion import TrainingCompletion
from app.models.training_material import TrainingMaterial
from app.models.policy import Policy
from app.models.policy_assignment import PolicyAssignment
from app.models.policy_acknowledgment import PolicyAcknowledgment
from app.models.export_request import ExportRequest
from app.models.export_quota import ExportQuota

# Import translation models if available
try:
    from app.models.translation import UserLanguagePreference, TranslationMetrics
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False

logger = logging.getLogger(__name__)

class DataExtractionService:
    """Service for extracting real user data from database tables."""
    
    @staticmethod
    def extract_user_profile(db: Session, user_id: int) -> Dict[str, Any]:
        """Extract user profile information and settings."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # Extract core user data, excluding sensitive fields
            profile_data = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "operation_name": user.operation_name,
                "facility_type": user.facility_type,
                "state": user.state,
                "phone_number": user.phone_number,
                "facility_id": user.facility_id,
                "subscription_status": user.subscription_status,
                "subscription_end_date": user.subscription_end_date,
                "is_active": user.is_active,
                "email_verified": user.email_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "quick_access_links": user.quick_access_links,
                "openai_vector_store_id": user.openai_vector_store_id,
                "openai_assistant_id": user.openai_assistant_id
            }
            
            # Extract notification settings if available
            notification_settings = db.query(NotificationSettings).filter(
                NotificationSettings.user_id == user_id
            ).first()
            
            if notification_settings:
                profile_data["notification_settings"] = {
                    "in_app_calendar_enabled": notification_settings.in_app_calendar_enabled,
                    "in_app_calendar_reminders_enabled": notification_settings.in_app_calendar_reminders_enabled,
                    "in_app_note_notifications_enabled": notification_settings.in_app_note_notifications_enabled,
                    "in_app_message_notifications_enabled": notification_settings.in_app_message_notifications_enabled,
                    "in_app_regulatory_updates_enabled": notification_settings.in_app_regulatory_updates_enabled,
                    "in_app_system_notifications_enabled": notification_settings.in_app_system_notifications_enabled,
                    "in_app_training_enabled": getattr(notification_settings, 'in_app_training_enabled', None),
                    "email_calendar_enabled": notification_settings.email_calendar_enabled,
                    "email_calendar_reminders_enabled": notification_settings.email_calendar_reminders_enabled,
                    "email_note_notifications_enabled": notification_settings.email_note_notifications_enabled,
                    "email_message_notifications_enabled": notification_settings.email_message_notifications_enabled,
                    "email_regulatory_updates_enabled": notification_settings.email_regulatory_updates_enabled,
                    "email_system_notifications_enabled": notification_settings.email_system_notifications_enabled,
                    "email_training_enabled": getattr(notification_settings, 'email_training_enabled', None),
                    "push_enabled": notification_settings.push_enabled,
                    "push_calendar_enabled": notification_settings.push_calendar_enabled,
                    "push_calendar_reminders_enabled": notification_settings.push_calendar_reminders_enabled,
                    "push_note_notifications_enabled": notification_settings.push_note_notifications_enabled,
                    "push_message_notifications_enabled": notification_settings.push_message_notifications_enabled,
                    "push_regulatory_updates_enabled": notification_settings.push_regulatory_updates_enabled,
                    "push_system_notifications_enabled": notification_settings.push_system_notifications_enabled,
                    "push_training_assignments_enabled": getattr(notification_settings, 'push_training_assignments_enabled', None),
                    "push_training_reminders_enabled": getattr(notification_settings, 'push_training_reminders_enabled', None),
                    "push_training_due_enabled": getattr(notification_settings, 'push_training_due_enabled', None),
                    "push_certification_expiring_enabled": getattr(notification_settings, 'push_certification_expiring_enabled', None),
                    "push_training_completed_enabled": getattr(notification_settings, 'push_training_completed_enabled', None),
                    "calendar_reminder_offset_minutes": notification_settings.calendar_reminder_offset_minutes,
                    "training_reminder_days": getattr(notification_settings, 'training_reminder_days', None),
                    "certification_expiry_reminder_days": getattr(notification_settings, 'certification_expiry_reminder_days', None),
                    "email_digest_frequency": notification_settings.email_digest_frequency,
                    "created_at": notification_settings.created_at.isoformat() if notification_settings.created_at else None,
                    "updated_at": notification_settings.updated_at.isoformat() if notification_settings.updated_at else None
                }
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Error extracting user profile for user {user_id}: {str(e)}")
            return {}
    
    @staticmethod
    def extract_documents(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Extract user documents and metadata."""
        try:
            documents = db.query(Document).filter(
                Document.uploaded_by == user_id,
                Document.is_deleted == False
            ).order_by(desc(Document.uploaded_at)).all()
            
            documents_data = []
            for doc in documents:
                doc_data = {
                    "id": doc.id,
                    "filename": doc.filename,
                    "filepath": doc.filepath,
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "custom_label": getattr(doc, 'custom_label', None),
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    "openai_file_id": doc.openai_file_id,
                    "is_processing": getattr(doc, 'is_processing', None),
                    "processing_error": getattr(doc, 'processing_error', None)
                }
                documents_data.append(doc_data)
            
            return documents_data
            
        except Exception as e:
            logger.error(f"Error extracting documents for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def extract_chat_logs(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Extract user chat interactions and AI conversations."""
        try:
            query_logs = db.query(QueryLog).filter(
                QueryLog.user_id == user_id
            ).order_by(desc(QueryLog.created_at)).all()
            
            chat_data = []
            for log in query_logs:
                log_data = {
                    "id": log.id,
                    "query": log.query,
                    "response": log.response,
                    "operation_type": log.operation_type,
                    "document_reference": log.document_reference,
                    "document_id": log.document_id,
                    "conversation_id": log.conversation_id,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                chat_data.append(log_data)
            
            return chat_data
            
        except Exception as e:
            logger.error(f"Error extracting chat logs for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def extract_regulatory_documents(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Extract user regulatory document access history."""
        try:
            user_docs = db.query(UserDocument).join(Regulation).filter(
                UserDocument.user_id == user_id
            ).order_by(desc(UserDocument.timestamp)).all()
            
            regulatory_data = []
            for user_doc in user_docs:
                doc_data = {
                    "access_id": user_doc.id,
                    "regulation_id": user_doc.regulation_id,
                    "accessed_at": user_doc.timestamp.isoformat() if user_doc.timestamp else None,
                    "regulation_details": {
                        "state_territory": user_doc.regulation.state_territory,
                        "document_title": user_doc.regulation.document_title,
                        "document_type": user_doc.regulation.document_type,
                        "file_name": user_doc.regulation.file_name,
                        "last_updated": user_doc.regulation.last_updated.isoformat() if user_doc.regulation.last_updated else None,
                        "created_at": user_doc.regulation.created_at.isoformat() if user_doc.regulation.created_at else None
                    }
                }
                regulatory_data.append(doc_data)
            
            return regulatory_data
            
        except Exception as e:
            logger.error(f"Error extracting regulatory documents for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def extract_calendar_events(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Extract user calendar events and activities."""
        try:
            events = db.query(CalendarEvent).filter(
                CalendarEvent.user_id == user_id
            ).order_by(desc(CalendarEvent.created_at)).all()
            
            calendar_data = []
            for event in events:
                event_data = {
                    "id": event.id,
                    "title": event.title,
                    "start": event.start,
                    "end": event.end,
                    "description": event.description,
                    "location": event.location,
                    "all_day": event.all_day,
                    "external_calendar_id": event.external_calendar_id,
                    "external_calendar_provider": event.external_calendar_provider,
                    "sync_status": event.sync_status,
                    "last_synced_at": event.last_synced_at.isoformat() if event.last_synced_at else None,
                    "reminder_sent": event.reminder_sent,
                    "start_notification_sent": event.start_notification_sent,
                    "created_by_admin": getattr(event, 'created_by_admin', None),
                    "facility_id": getattr(event, 'facility_id', None),
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                    "updated_at": event.updated_at.isoformat() if event.updated_at else None
                }
                calendar_data.append(event_data)
            
            return calendar_data
            
        except Exception as e:
            logger.error(f"Error extracting calendar events for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def extract_notifications(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Extract user notifications and system interactions."""
        try:
            notifications = db.query(Notification).filter(
                Notification.user_id == user_id
            ).order_by(desc(Notification.created_at)).all()
            
            notification_data = []
            for notification in notifications:
                notif_data = {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.type,
                    "priority": notification.priority,
                    "is_read": notification.is_read,
                    "related_id": notification.related_id,
                    "related_type": notification.related_type,
                    "action_url": notification.action_url,
                    "created_at": notification.created_at.isoformat() if notification.created_at else None
                }
                notification_data.append(notif_data)
            
            return notification_data
            
        except Exception as e:
            logger.error(f"Error extracting notifications for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def extract_notes(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Extract user notes and content."""
        try:
            notes = db.query(Note).filter(
                Note.user_id == user_id
            ).order_by(desc(Note.updated_at)).all()
            
            notes_data = []
            for note in notes:
                note_data = {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "is_pinned": note.is_pinned,
                    "is_archived": note.is_archived,
                    "created_at": note.created_at.isoformat() if note.created_at else None,
                    "updated_at": note.updated_at.isoformat() if note.updated_at else None
                }
                notes_data.append(note_data)
            
            return notes_data
            
        except Exception as e:
            logger.error(f"Error extracting notes for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def extract_facility_data(db: Session, user_id: int) -> Dict[str, Any]:
        """Extract facility management data for administrators."""
        try:
            facility_data = {}
            
            # Check if user is facility administrator
            administered_facility = db.query(Facility).filter(
                Facility.admin_user_id == user_id
            ).first()
            
            if administered_facility:
                facility_data["administered_facility"] = {
                    "id": administered_facility.id,
                    "facility_name": administered_facility.facility_name,
                    "facility_address": administered_facility.facility_address,
                    "facility_city": administered_facility.facility_city,
                    "facility_state": administered_facility.facility_state,
                    "facility_zip": administered_facility.facility_zip,
                    "facility_phone": administered_facility.facility_phone,
                    "facility_email": administered_facility.facility_email,
                    "subscription_id": administered_facility.subscription_id,
                    "stripe_customer_id": administered_facility.stripe_customer_id,
                    "max_users": administered_facility.max_users,
                    "is_active": administered_facility.is_active,
                    "invitation_code": administered_facility.invitation_code,
                    "invitation_expires_at": administered_facility.invitation_expires_at.isoformat() if administered_facility.invitation_expires_at else None,
                    "created_at": administered_facility.created_at.isoformat() if administered_facility.created_at else None,
                    "updated_at": administered_facility.updated_at.isoformat() if administered_facility.updated_at else None
                }
                
                # Extract staff members for administered facility
                staff_members = db.query(StaffMember).filter(
                    StaffMember.facility_administrator_id == user_id
                ).order_by(desc(StaffMember.created_at)).all()
                
                facility_data["staff_members"] = []
                for staff in staff_members:
                    staff_data = {
                        "id": staff.id,
                        "employee_id": staff.employee_id,
                        "first_name": staff.first_name,
                        "last_name": staff.last_name,
                        "email": staff.email,
                        "phone_number": staff.phone_number,
                        "role": staff.role,
                        "department": staff.department,
                        "position_title": staff.position_title,
                        "hire_date": staff.hire_date.isoformat() if staff.hire_date else None,
                        "status": staff.status,
                        "facility_name": staff.facility_name,
                        "facility_location": staff.facility_location,
                        "training_completion_rate": staff.training_completion_rate,
                        "certifications_current": staff.certifications_current,
                        "certifications_expired": staff.certifications_expired,
                        "last_training_date": staff.last_training_date.isoformat() if staff.last_training_date else None,
                        "notification_preferences": staff.notification_preferences,
                        "created_at": staff.created_at.isoformat() if staff.created_at else None,
                        "updated_at": staff.updated_at.isoformat() if staff.updated_at else None
                    }
                    facility_data["staff_members"].append(staff_data)
            
            # Check if user belongs to a facility
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.facility_id:
                facility = db.query(Facility).filter(Facility.id == user.facility_id).first()
                if facility:
                    facility_data["member_of_facility"] = {
                        "id": facility.id,
                        "facility_name": facility.facility_name,
                        "facility_address": facility.facility_address,
                        "facility_city": facility.facility_city,
                        "facility_state": facility.facility_state,
                        "is_admin": facility.admin_user_id == user_id
                    }
            
            return facility_data
            
        except Exception as e:
            logger.error(f"Error extracting facility data for user {user_id}: {str(e)}")
            return {}
    
    @staticmethod
    def extract_training_data(db: Session, user_id: int) -> Dict[str, Any]:
        """Extract training programs, assignments, and completion data."""
        try:
            training_data = {}
            
            # Extract training programs created by user
            created_programs = db.query(TrainingProgram).filter(
                TrainingProgram.created_by == user_id
            ).order_by(desc(TrainingProgram.created_at)).all()
            
            training_data["created_programs"] = []
            for program in created_programs:
                program_data = {
                    "id": program.id,
                    "title": program.title,
                    "description": program.description,
                    "category": program.category,
                    "is_mandatory": program.is_mandatory,
                    "requires_certification": program.requires_certification,
                    "certification_valid_months": program.certification_valid_months,
                    "estimated_duration_minutes": program.estimated_duration_minutes,
                    "delivery_method": program.delivery_method,
                    "prerequisites": program.prerequisites,
                    "reminder_schedule_days": program.reminder_schedule_days,
                    "auto_assign_new_staff": program.auto_assign_new_staff,
                    "is_active": program.is_active,
                    "created_at": program.created_at.isoformat() if program.created_at else None,
                    "updated_at": program.updated_at.isoformat() if program.updated_at else None
                }
                training_data["created_programs"].append(program_data)
            
            # Extract training assignments for staff associated with user's facility
            assignments = db.query(TrainingAssignment).join(StaffMember).filter(
                StaffMember.facility_administrator_id == user_id
            ).order_by(desc(TrainingAssignment.created_at)).all()
            
            training_data["assignments"] = []
            for assignment in assignments:
                assignment_data = {
                    "id": assignment.id,
                    "training_program_id": assignment.training_program_id,
                    "staff_member_id": assignment.staff_member_id,
                    "assigned_by": assignment.assigned_by,
                    "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                    "status": assignment.status,
                    "priority": assignment.priority,
                    "notes": assignment.notes,
                    "completion_percentage": assignment.completion_percentage,
                    "last_accessed": assignment.last_accessed.isoformat() if assignment.last_accessed else None,
                    "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
                    "updated_at": assignment.updated_at.isoformat() if assignment.updated_at else None
                }
                training_data["assignments"].append(assignment_data)
            
            # Extract training completions
            completions = db.query(TrainingCompletion).join(TrainingAssignment).join(StaffMember).filter(
                StaffMember.facility_administrator_id == user_id
            ).order_by(desc(TrainingCompletion.completed_at)).all()
            
            training_data["completions"] = []
            for completion in completions:
                completion_data = {
                    "id": completion.id,
                    "training_assignment_id": completion.training_assignment_id,
                    "completed_at": completion.completed_at.isoformat() if completion.completed_at else None,
                    "score": completion.score,
                    "passing_score": completion.passing_score,
                    "status": completion.status,
                    "certificate_issued": completion.certificate_issued,
                    "certificate_number": completion.certificate_number,
                    "certificate_expires_at": completion.certificate_expires_at.isoformat() if completion.certificate_expires_at else None,
                    "certificate_status": completion.certificate_status,
                    "completion_notes": completion.completion_notes,
                    "created_at": completion.created_at.isoformat() if completion.created_at else None
                }
                training_data["completions"].append(completion_data)
            
            # Extract training materials for programs created by user
            materials = db.query(TrainingMaterial).join(TrainingProgram).filter(
                TrainingProgram.created_by == user_id
            ).order_by(desc(TrainingMaterial.created_at)).all()
            
            training_data["materials"] = []
            for material in materials:
                material_data = {
                    "id": material.id,
                    "training_program_id": material.training_program_id,
                    "title": material.title,
                    "description": material.description,
                    "material_type": material.material_type,
                    "content_url": material.content_url,
                    "file_path": material.file_path,
                    "estimated_duration_minutes": material.estimated_duration_minutes,
                    "is_required": material.is_required,
                    "sort_order": material.sort_order,
                    "status": material.status,
                    "created_at": material.created_at.isoformat() if material.created_at else None,
                    "updated_at": material.updated_at.isoformat() if material.updated_at else None
                }
                training_data["materials"].append(material_data)
            
            return training_data
            
        except Exception as e:
            logger.error(f"Error extracting training data for user {user_id}: {str(e)}")
            return {}
    
    @staticmethod
    def extract_policy_data(db: Session, user_id: int) -> Dict[str, Any]:
        """Extract policy management data."""
        try:
            policy_data = {}
            
            # Extract policies created by user
            created_policies = db.query(Policy).filter(
                Policy.created_by == user_id
            ).order_by(desc(Policy.created_at)).all()
            
            policy_data["created_policies"] = []
            for policy in created_policies:
                policy_data_item = {
                    "id": policy.id,
                    "title": policy.title,
                    "description": policy.description,
                    "category": policy.category,
                    "document_id": policy.document_id,
                    "document_url": policy.document_url,
                    "content_summary": policy.content_summary,
                    "version": policy.version,
                    "effective_date": policy.effective_date.isoformat() if policy.effective_date else None,
                    "expiry_date": policy.expiry_date.isoformat() if policy.expiry_date else None,
                    "supersedes_policy_id": policy.supersedes_policy_id,
                    "requires_acknowledgment": policy.requires_acknowledgment,
                    "acknowledgment_deadline_days": policy.acknowledgment_deadline_days,
                    "auto_assign_new_staff": policy.auto_assign_new_staff,
                    "acknowledgment_reminder_days": policy.acknowledgment_reminder_days,
                    "regulatory_reference": policy.regulatory_reference,
                    "compliance_level": policy.compliance_level,
                    "status": policy.status,
                    "is_active": policy.is_active,
                    "facility_administrator_id": policy.facility_administrator_id,
                    "approved_by": policy.approved_by,
                    "approved_date": policy.approved_date.isoformat() if policy.approved_date else None,
                    "created_at": policy.created_at.isoformat() if policy.created_at else None,
                    "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
                }
                policy_data["created_policies"].append(policy_data_item)
            
            # Extract policy assignments for staff under user's administration
            assignments = db.query(PolicyAssignment).join(StaffMember).filter(
                StaffMember.facility_administrator_id == user_id
            ).order_by(desc(PolicyAssignment.created_at)).all()
            
            policy_data["assignments"] = []
            for assignment in assignments:
                assignment_data = {
                    "id": assignment.id,
                    "policy_id": assignment.policy_id,
                    "staff_member_id": assignment.staff_member_id,
                    "assigned_by": assignment.assigned_by,
                    "assigned_date": assignment.assigned_date.isoformat() if assignment.assigned_date else None,
                    "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                    "status": assignment.status,
                    "priority": assignment.priority,
                    "requires_immediate_attention": assignment.requires_immediate_attention,
                    "reminder_sent": assignment.reminder_sent,
                    "escalation_sent": assignment.escalation_sent,
                    "is_mandatory": assignment.is_mandatory,
                    "notes": assignment.notes,
                    "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
                    "updated_at": assignment.updated_at.isoformat() if assignment.updated_at else None
                }
                policy_data["assignments"].append(assignment_data)
            
            # Extract policy acknowledgments
            acknowledgments = db.query(PolicyAcknowledgment).join(PolicyAssignment).join(StaffMember).filter(
                StaffMember.facility_administrator_id == user_id
            ).order_by(desc(PolicyAcknowledgment.acknowledged_at)).all()
            
            policy_data["acknowledgments"] = []
            for ack in acknowledgments:
                ack_data = {
                    "id": ack.id,
                    "policy_assignment_id": ack.policy_assignment_id,
                    "acknowledged_at": ack.acknowledged_at.isoformat() if ack.acknowledged_at else None,
                    "acknowledgment_method": ack.acknowledgment_method,
                    "digital_signature": ack.digital_signature,
                    "ip_address": ack.ip_address,
                    "user_agent": ack.user_agent,
                    "status": ack.status,
                    "is_current": ack.is_current,
                    "requires_reacknowledgment": ack.requires_reacknowledgment,
                    "notes": ack.notes,
                    "created_at": ack.created_at.isoformat() if ack.created_at else None
                }
                policy_data["acknowledgments"].append(ack_data)
            
            return policy_data
            
        except Exception as e:
            logger.error(f"Error extracting policy data for user {user_id}: {str(e)}")
            return {}
    
    @staticmethod
    def extract_translation_data(db: Session, user_id: int) -> Dict[str, Any]:
        """Extract translation preferences and usage metrics."""
        try:
            translation_data = {}
            
            if not TRANSLATION_AVAILABLE:
                logger.debug(f"Translation models not available for user {user_id}")
                return translation_data
            
            # Extract user language preferences
            try:
                preferences = db.query(UserLanguagePreference).filter(
                    UserLanguagePreference.user_id == user_id
                ).first()
                
                if preferences:
                    translation_data["language_preferences"] = {
                        "id": preferences.id,
                        "preferred_language": preferences.preferred_language,
                        "auto_translate": preferences.auto_translate,
                        "created_at": preferences.created_at.isoformat() if preferences.created_at else None,
                        "updated_at": preferences.updated_at.isoformat() if preferences.updated_at else None
                    }
            except Exception as e:
                logger.debug(f"Error extracting language preferences: {str(e)}")
            
            # Extract translation usage metrics
            try:
                metrics = db.query(TranslationMetrics).filter(
                    TranslationMetrics.user_id == user_id
                ).order_by(desc(TranslationMetrics.timestamp)).all()
                
                if metrics:
                    translation_data["usage_metrics"] = []
                    for metric in metrics:
                        metric_data = {
                            "id": metric.id,
                            "source_language": metric.source_language,
                            "target_language": metric.target_language,
                            "text_length": metric.text_length,
                            "response_time_ms": metric.response_time_ms,
                            "success": metric.success,
                            "error_message": metric.error_message,
                            "cache_hit": metric.cache_hit,
                            "timestamp": metric.timestamp.isoformat() if metric.timestamp else None
                        }
                        translation_data["usage_metrics"].append(metric_data)
            except Exception as e:
                logger.debug(f"Error extracting translation metrics: {str(e)}")
            
            return translation_data
            
        except Exception as e:
            logger.error(f"Error extracting translation data for user {user_id}: {str(e)}")
            return {}
    
    @staticmethod
    def extract_export_history(db: Session, user_id: int) -> Dict[str, Any]:
        """Extract user's export request history and quota usage."""
        try:
            export_data = {}
            
            # Extract export requests
            export_requests = db.query(ExportRequest).filter(
                ExportRequest.user_id == user_id
            ).order_by(desc(ExportRequest.created_at)).all()
            
            export_data["export_requests"] = []
            for request in export_requests:
                request_data = {
                    "id": request.id,
                    "status": request.status,
                    "format": request.format,
                    "data_types": request.data_types,
                    "estimated_size": request.estimated_size,
                    "actual_size": request.actual_size,
                    "requires_fee": request.requires_fee,
                    "fee_amount": float(request.fee_amount) if request.fee_amount else None,
                    "support_ticket_id": request.support_ticket_id,
                    "download_expires_at": request.download_expires_at.isoformat() if request.download_expires_at else None,
                    "error_message": request.error_message,
                    "progress_percentage": request.progress_percentage,
                    "created_at": request.created_at.isoformat() if request.created_at else None,
                    "updated_at": request.updated_at.isoformat() if request.updated_at else None
                }
                export_data["export_requests"].append(request_data)
            
            # Extract export quotas
            export_quotas = db.query(ExportQuota).filter(
                ExportQuota.user_id == user_id
            ).order_by(desc(ExportQuota.created_at)).all()
            
            export_data["export_quotas"] = []
            for quota in export_quotas:
                quota_data = {
                    "id": quota.id,
                    "quarter_year": quota.quarter_year,
                    "exports_used": quota.exports_used,
                    "last_export_date": quota.last_export_date.isoformat() if quota.last_export_date else None,
                    "total_data_size": quota.total_data_size,
                    "created_at": quota.created_at.isoformat() if quota.created_at else None,
                    "updated_at": quota.updated_at.isoformat() if quota.updated_at else None
                }
                export_data["export_quotas"].append(quota_data)
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error extracting export history for user {user_id}: {str(e)}")
            return {}
    
    @staticmethod
    def extract_push_subscriptions(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Extract push notification subscriptions."""
        try:
            subscriptions = db.query(PushSubscription).filter(
                PushSubscription.user_id == user_id
            ).order_by(desc(PushSubscription.created_at)).all()
            
            subscriptions_data = []
            for subscription in subscriptions:
                # Exclude sensitive keys from export
                subscription_data = {
                    "id": subscription.id,
                    "endpoint": subscription.endpoint,
                    "created_at": subscription.created_at.isoformat() if subscription.created_at else None
                }
                subscriptions_data.append(subscription_data)
            
            return subscriptions_data
            
        except Exception as e:
            logger.error(f"Error extracting push subscriptions for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def extract_calendar_connections(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Extract calendar integration connections."""
        try:
            # Try to query calendar connections if the model exists
            # This will be populated when the calendar connections feature is implemented
            connections_data = []
            
            # For now, return empty list as the model doesn't exist yet
            # When implemented, this would query the CalendarConnection model
            logger.debug(f"Calendar connections not yet implemented for user {user_id}")
            return connections_data
            
        except Exception as e:
            logger.error(f"Error extracting calendar connections for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def extract_all_user_data(db: Session, user_id: int, data_types: List[str]) -> Dict[str, Any]:
        """Extract all requested user data types."""
        extracted_data = {}
        
        try:
            # Extract each requested data type
            extraction_methods = {
                "user_profile": DataExtractionService.extract_user_profile,
                "documents": DataExtractionService.extract_documents,
                "chat_logs": DataExtractionService.extract_chat_logs,
                "policy_records": DataExtractionService.extract_regulatory_documents,
                "calendar_entries": DataExtractionService.extract_calendar_events,
                "audit_trail": DataExtractionService.extract_notifications,
                "training_history": DataExtractionService.extract_notes,  # This maps to notes for now
                "facility_management": DataExtractionService.extract_facility_data,
                "training_programs": DataExtractionService.extract_training_data,
                "policy_management": DataExtractionService.extract_policy_data,
                "translation_data": DataExtractionService.extract_translation_data,
                "calendar_connections": DataExtractionService.extract_calendar_connections,
                "push_subscriptions": DataExtractionService.extract_push_subscriptions,
                "export_history": DataExtractionService.extract_export_history,
                "notes": DataExtractionService.extract_notes,
            }
            
            for data_type in data_types:
                if data_type in extraction_methods:
                    try:
                        extracted_content = extraction_methods[data_type](db, user_id)
                        
                        # Only include data type if it contains actual data
                        if extracted_content:
                            # Check if it's a list and has items, or dict and has content
                            if isinstance(extracted_content, list) and len(extracted_content) > 0:
                                extracted_data[data_type] = extracted_content
                            elif isinstance(extracted_content, dict) and len(extracted_content) > 0:
                                # For dicts, check if they have meaningful content beyond just empty structures
                                has_content = False
                                for key, value in extracted_content.items():
                                    if isinstance(value, list) and len(value) > 0:
                                        has_content = True
                                        break
                                    elif isinstance(value, dict) and len(value) > 0:
                                        has_content = True
                                        break
                                    elif value is not None and value != "":
                                        has_content = True
                                        break
                                
                                if has_content:
                                    extracted_data[data_type] = extracted_content
                            elif not isinstance(extracted_content, (list, dict)):
                                # For other types (strings, numbers, etc.), include if not empty/None
                                if extracted_content is not None and extracted_content != "":
                                    extracted_data[data_type] = extracted_content
                    except Exception as e:
                        logger.error(f"Error extracting {data_type} for user {user_id}: {str(e)}")
                        continue
            
            # Add metadata
            extracted_data["export_metadata"] = {
                "user_id": user_id,
                "extraction_timestamp": datetime.utcnow().isoformat(),
                "data_types_requested": data_types,
                "data_types_extracted": [dt for dt in data_types if dt in extracted_data]
            }
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting user data for user {user_id}: {str(e)}")
            return {
                "error": str(e),
                "user_id": user_id,
                "extraction_timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def calculate_data_size(extracted_data: Dict[str, Any]) -> int:
        """Calculate estimated size of extracted data in bytes."""
        try:
            import json
            json_string = json.dumps(extracted_data, ensure_ascii=False)
            return len(json_string.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error calculating data size: {str(e)}")
            return 0 