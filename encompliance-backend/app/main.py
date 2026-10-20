"""
# Description: Main entry point for the EnCompliance backend application.
# Purpose: Initializes the FastAPI app, configures middleware, and registers all API routers for the compliance platform.
---------------------------
This file serves as the primary entry point for the EnCompliance backend application.
It initializes the FastAPI application, configures middleware, and sets up the main API routes.
The application handles:
- API routing and endpoint registration
- Middleware configuration (CORS, authentication, etc.)
- Application startup and shutdown events
- Health check endpoints
- API documentation setup
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from app.database import engine, get_db, SessionLocal
from app.models.user import Base
from app.models.document import Document
from app.models.query_log import QueryLog
from app.models.facility_type import FacilityType
from app.models.regulation import Regulation
from app.models.user_document import UserDocument
from app.models.token import BlacklistedToken
from app.models.user_otp import UserOTP  # Import the UserOTP model
from app.models import training  # Import training models for database table creation
from app.models.operational_task import OperationalTask  # Import operational task model for database table creation
from app.models.task_assignment import TaskAssignment  # Import task assignment model for database table creation
from app.models.task_reference_image import TaskReferenceImage  # Import task reference image model for database table creation
from app.models.organization import Organization  # Ensure org table metadata is registered
import os
from dotenv import load_dotenv
from app.core.config import get_settings
from app.core.schema_compat import ensure_organization_schema
from app.utils.performance_monitor import ResponseTimeMiddleware
from app.utils.sentry_logger import init_sentry
from app.utils.security import CSPMiddleware
from app.utils.csrf_protection import CSRFProtection
from app.utils.owasp_protections import SecurityHeaders
from fastapi_utils.tasks import repeat_every
from app.auth.utils import clean_expired_tokens
from app.core.cleanup import run_daily_cleanup  # Add the cleanup module
from datetime import datetime
import traceback
from app.api.routes import activities as activity_router
from app.api.routes import activity_signups as activity_signup_router
from app.api.routes import activity_suggestions as activity_suggestion_router
from app.api.routes import scheduling as scheduling_router
from app.api.routes import ai_assist as ai_assist_router
from app.api.routes import team_comms as team_comms_router
from app.api.routes import imports as data_import_router
from app.api.routes import google_config as google_config_router
# from app.api.routes import translation as translation_router
from app.api.routes import rbac as rbac_router
from app.api.routes import analytics as analytics_router
from app.api.routes import policy_distribution as policy_distribution_router
from app.api.routes import usage_billing as usage_billing_router
from app.api.routes import storage as storage_router
from app.api.routes import staff_directory as staff_directory_router
from app.api.routes import escalations as escalations_router
from app.api.routes import audit as audit_router
from app.api.routes import manager_controls as manager_controls_router
from app.services.escalation_service import EscalationService

# Load environment variables
load_dotenv()

# Get settings with hardcoded storage path
settings = get_settings()
print(f"Using storage path: {settings.PDF_STORAGE_PATH}")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry
environment = os.getenv("ENVIRONMENT", "development")
init_sentry(environment)

# Create database tables
try:
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    ensure_organization_schema(engine, logger)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing database tables: {str(e)}")

# Custom middleware for debugging
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log request details
        logger.info(f"Request: {request.method} {request.url.path}")
        pass  # Sensitive authentication data must not be logged.
        
        # Process the request
        response = await call_next(request)
        
        # Log response details
        logger.info(f"Response status: {response.status_code}")
        
        return response

# Create the app
app = FastAPI(
    title="Encompliance.io API",
    description="Backend API for Encompliance.io compliance platform",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.encompliance.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization", "Content-Type", "x-token", "Cache-Control", "Pragma", "Expires", "Origin", "Accept", "X-Requested-With"],
    expose_headers=["*", "Access-Control-Allow-Origin"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Add debug middleware
app.add_middleware(RequestLoggingMiddleware)

# Add performance monitoring middleware
app.add_middleware(ResponseTimeMiddleware)

# Add Content Security Policy middleware
app.add_middleware(
    CSPMiddleware,
    default_src=["'self'"],
    script_src=["'self'", "'unsafe-inline'", "'unsafe-eval'"],  # Allow eval for development tools
    style_src=["'self'", "'unsafe-inline'"],
    img_src=["'self'", "data:", "https:", "http:"],  # More permissive for development
    font_src=["'self'", "https:", "data:"],  # More permissive for fonts
    connect_src=["'self'", "http:", "https:"],  # Allow all connections in development
    report_only=True  # Keep in report-only mode to avoid breaking functionality
)

# Skip CSRF in development to avoid login issues initially
if environment != "development":
    # Add CSRF protection middleware - exclude all auth endpoints
    app.add_middleware(
        CSRFProtection,
        cookie_secure=False if environment == "development" else True,
        exclude_paths=[
            "/api/v1/auth/login", 
            "/api/v1/auth/signup",
            "/api/v1/login",
            "/api/auth/login",
            "/api/v1/token",
            "/api/token",
            "/api/v1/users/me",
            "/api/users/me"
        ]
    )

# Add middleware to apply security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add security headers to all responses
    security_headers = SecurityHeaders.get_security_headers()
    for header_name, header_value in security_headers.items():
        response.headers[header_name] = header_value
    
    return response

# Import routers after creating the app to avoid circular imports
from app.api.routes import users
from app.api import auth
from app.api.routes import auth as auth_routes  # Import the multi-step signup routes
from app.api.routes import chat
from app.api.routes import documents
from app.api.routes import queries
from app.api.routes import settings
from app.api import survey # <<< Import the new survey router
from app.api.routes import logs  # Import the new logs router
from app.api import contact # <<< Import the new contact router
from app.api.routes import webauthn  # Import the WebAuthn router
from app.api import otp  # Import the OTP router
from app.api.routes import calendar  # Import the calendar router
from app.api.routes import notes  # Import the notes router
from app.api.routes import notifications  # Import the notifications router
from app.services.calendar_reminder_service import CalendarReminderService
from app.api.routes import calendar_integration
from app.api.routes import export  # Import the export router
from app.api.routes import training  # Import the training router
from app.api.routes import policy  # Import the policy router
from app.api.routes import payments  # Import the payments router
from app.api.routes import facilities  # Import the facility management router
from app.api.routes import team_members  # Import the team member management router
from app.api.routes import sync  # Import the sync router
from app.api.routes import maryland_integration  # Import the Maryland COMAR integration router
from app.api.routes import manual_regulation_import  # Import the manual regulation import router
from app.api.routes import operational_tasks  # Import the operational tasks router
from app.api.routes import assignment_images  # Import the assignment images router
from app.api.routes import task_reference_images  # Import the task reference images router
from app.api.routes import support  # Import the consumer support router
from app.api.routes import api_keys as api_keys_router
from app.mcp import server as mcp_server

# Include routers
app.include_router(users.router, prefix="/api/v1/users")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(auth_routes.router, prefix="/api/v1")  # Add multi-step signup routes
app.include_router(chat.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")  # Primary document routes
app.include_router(queries.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(survey.router, prefix="/api/v1") # <<< Register the survey router
app.include_router(logs.router, prefix="/api/v1")  # Register the logs router
app.include_router(contact.router, prefix="/api/v1") # <<< Register the contact router
app.include_router(webauthn.router, prefix="/api/v1")  # Register the WebAuthn router
app.include_router(otp.router, prefix="/api/v1")  # Register the OTP router
app.include_router(calendar.router, prefix="/api/v1")  # Add calendar router to /api/v1 prefix
app.include_router(calendar_integration.router, prefix="/api/v1")  # Add calendar integration router
app.include_router(notes.router, prefix="/api/v1/notes")  # Corrected notes router prefix
app.include_router(notifications.router, prefix="/api/v1/notifications")  # Register the notifications router
app.include_router(export.router)  # Register the export router (already has /api/v1/export prefix)
app.include_router(training.router, prefix="/api/v1/training")  # Register the training router
app.include_router(policy.router, prefix="/api/v1")  # Register the policy router
app.include_router(payments.router, prefix="/api/v1/payments")  # Register the payments router
app.include_router(facilities.router, prefix="/api/v1")  # Register the facility management router
app.include_router(team_members.router)  # Register the team member management router
app.include_router(sync.router, prefix="/api/v1/sync")  # Register the sync router
app.include_router(maryland_integration.router, prefix="/api/v1")  # Register the Maryland COMAR integration router
app.include_router(manual_regulation_import.router, prefix="/api/v1")  # Register the manual regulation import router
app.include_router(operational_tasks.router, prefix="/api/v1")  # Register the operational tasks router
app.include_router(assignment_images.router, prefix="/api")
app.include_router(task_reference_images.router, prefix="/api/v1")  # Register the task reference images router
app.include_router(activity_router.router, prefix="/api/v1")
app.include_router(activity_signup_router.router, prefix="/api/v1")
app.include_router(activity_suggestion_router.router, prefix="/api/v1")
app.include_router(scheduling_router.router, prefix="/api/v1")
app.include_router(ai_assist_router.router, prefix="/api/v1")
app.include_router(team_comms_router.router, prefix="/api/v1")
app.include_router(data_import_router.router, prefix="/api/v1")
app.include_router(google_config_router.router, prefix="/api/v1")
# app.include_router(translation_router.router, prefix="/api/v1")
app.include_router(rbac_router.router, prefix="/api/v1")
app.include_router(analytics_router.router, prefix="/api/v1")
app.include_router(policy_distribution_router.router, prefix="/api/v1")
app.include_router(usage_billing_router.router, prefix="/api/v1")
app.include_router(storage_router.router, prefix="/api/v1")
app.include_router(staff_directory_router.router, prefix="/api/v1")
app.include_router(escalations_router.router, prefix="/api/v1")
app.include_router(audit_router.router, prefix="/api/v1")
app.include_router(manager_controls_router.router, prefix="/api/v1")
app.include_router(support.router)  # Consumer support tickets (already has /api/v1/support prefix)
app.include_router(api_keys_router.router, prefix="/api/v1")
app.include_router(mcp_server.router, prefix="/api/v1")

# Add a root level router for certain API endpoints that are being called directly with /api/ prefix
app.include_router(queries.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")  # Add documents router to /api prefix
app.include_router(settings.router, prefix="/api")  # Add settings router to /api prefix
app.include_router(logs.router, prefix="/api")
app.include_router(webauthn.router, prefix="/api")  # Add WebAuthn router to /api prefix
app.include_router(otp.router, prefix="/api")  # Add OTP router to /api prefix
app.include_router(calendar.router, prefix="/api")  # Add calendar router to /api prefix
app.include_router(notes.router, prefix="/api/notes")  # Add notes router to /api prefix for compatibility
app.include_router(notifications.router, prefix="/api/notifications")  # Add notifications router to /api prefix
app.include_router(activity_router.router, prefix="/api")
app.include_router(activity_signup_router.router, prefix="/api")
app.include_router(activity_suggestion_router.router, prefix="/api")
app.include_router(scheduling_router.router, prefix="/api")
app.include_router(ai_assist_router.router, prefix="/api")
app.include_router(team_comms_router.router, prefix="/api")
app.include_router(data_import_router.router, prefix="/api")
app.include_router(google_config_router.router, prefix="/api")
    # app.include_router(translation_router.router, prefix="/api")
app.include_router(rbac_router.router, prefix="/api")
app.include_router(analytics_router.router, prefix="/api")
app.include_router(policy_distribution_router.router, prefix="/api")
app.include_router(usage_billing_router.router, prefix="/api")
app.include_router(storage_router.router, prefix="/api")
app.include_router(staff_directory_router.router, prefix="/api")
app.include_router(escalations_router.router, prefix="/api")
app.include_router(audit_router.router, prefix="/api")
app.include_router(manager_controls_router.router, prefix="/api")
app.include_router(api_keys_router.router, prefix="/api")
app.include_router(mcp_server.router, prefix="/api")

# Background integrations are opt-in for local, source-only development.
def background_startup(fn):
    if os.getenv("ENABLE_BACKGROUND_JOBS", "false").lower() == "true":
        app.add_event_handler("startup", fn)
    return fn

# Background task to clean up expired tokens and unverified accounts
@background_startup
@repeat_every(seconds=60 * 60 * 24)  # Run once per day
async def cleanup_task() -> None:
    """Run all cleanup tasks daily."""
    try:
        logger.info("Starting daily cleanup tasks")
        await run_daily_cleanup()
    except Exception as e:
        logger.error(f"Failed to run cleanup tasks: {str(e)}")
        logger.error(traceback.format_exc())

# Background task to process recurring tasks
@background_startup
@repeat_every(seconds=60 * 60)  # Run every hour
async def recurring_task_processor() -> None:
    """Process recurring tasks and create new assignments."""
    try:
        from app.services.recurring_task_scheduler import RecurringTaskScheduler
        logger.info("Starting recurring task processing")
        result = await RecurringTaskScheduler.process_recurring_tasks()
        logger.info(f"Recurring task processing completed: {result}")
    except Exception as e:
        logger.error(f"Failed to process recurring tasks: {str(e)}")
        logger.error(traceback.format_exc())


@background_startup
@repeat_every(seconds=60 * 5)
async def escalation_processor() -> None:
    """Process pending escalation incidents."""
    db = SessionLocal()
    try:
        processed = EscalationService.process_pending_incidents(db)
        if processed:
            logger.info(f"Processed {processed} escalation steps.")
    except Exception as exc:
        logger.error(f"Escalation processing failed: {exc}")
    finally:
        db.close()

# Background task to maintain recurring calendar events
@background_startup
@repeat_every(seconds=60 * 60 * 24)  # Run once per day
async def recurring_calendar_maintenance() -> None:
    """Maintain recurring calendar events by creating future events."""
    try:
        from app.database import SessionLocal
        from app.models.operational_task import OperationalTask, TaskType
        from app.models.user import User
        from app.services.task_calendar_integration_service import TaskCalendarIntegrationService
        
        logger.info("Starting recurring calendar maintenance")
        db = SessionLocal()
        
        try:
            # Get all active recurring tasks
            recurring_tasks = db.query(OperationalTask).filter(
                OperationalTask.task_type == TaskType.RECURRING.value,
                OperationalTask.is_active == True
            ).all()
            
            events_created = 0
            
            for task in recurring_tasks:
                try:
                    # Get the task creator
                    creator = db.query(User).filter(User.id == task.created_by).first()
                    if not creator:
                        continue
                    
                    # Check if we need to create more future calendar events
                    # (This will create events if we're running low on future events)
                    new_events = await TaskCalendarIntegrationService.create_recurring_task_calendar_events(
                        db=db,
                        task=task,
                        created_by_user=creator
                    )
                    events_created += len(new_events)
                    
                except Exception as e:
                    logger.error(f"Error maintaining calendar events for task {task.id}: {str(e)}")
                    continue
            
            logger.info(f"Recurring calendar maintenance completed: {events_created} events created for {len(recurring_tasks)} tasks")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in recurring calendar maintenance: {str(e)}")

# Background task to maintain training calendar events
@background_startup
@repeat_every(seconds=60 * 60 * 24)  # Run once per day
async def training_calendar_maintenance() -> None:
    """Maintain training calendar events by creating certification renewal reminders."""
    try:
        from app.database import SessionLocal
        from app.models.training_completion import TrainingCompletion
        from app.models.training_program import TrainingProgram
        from app.models.staff_member import StaffMember
        from app.services.training_calendar_integration_service import TrainingCalendarIntegrationService
        from datetime import datetime, timedelta
        
        logger.info("Starting training calendar maintenance")
        db = SessionLocal()
        
        try:
            # Get completions that will expire in the next 6 months and don't have renewal reminders yet
            future_date = datetime.now() + timedelta(days=180)
            
            completions_needing_reminders = db.query(TrainingCompletion).join(TrainingProgram).join(StaffMember).filter(
                TrainingCompletion.expires_date.isnot(None),
                TrainingCompletion.expires_date <= future_date,
                TrainingCompletion.expires_date > datetime.now(),
                TrainingProgram.requires_certification == True
            ).all()
            
            reminders_created = 0
            
            for completion in completions_needing_reminders:
                try:
                    # Check if renewal reminder already exists
                    from app.models.calendar_event import CalendarEvent
                    existing_reminder = db.query(CalendarEvent).filter(
                        CalendarEvent.training_completion_id == completion.id,
                        CalendarEvent.event_type == 'certification_renewal'
                    ).first()
                    
                    if existing_reminder:
                        continue
                    
                    # Get related entities
                    training_program = completion.training_program
                    staff_member = db.query(StaffMember).filter(
                        StaffMember.id == completion.staff_member_id
                    ).first()
                    
                    if not staff_member or not training_program:
                        continue
                    
                    # Create renewal reminder
                    reminder_event = await TrainingCalendarIntegrationService.create_certification_renewal_calendar_event(
                        db=db,
                        completion=completion,
                        training_program=training_program,
                        staff_member=staff_member
                    )
                    
                    if reminder_event:
                        reminders_created += 1
                    
                except Exception as e:
                    logger.error(f"Error creating renewal reminder for completion {completion.id}: {str(e)}")
                    continue
            
            logger.info(f"Training calendar maintenance completed: {reminders_created} renewal reminders created for {len(completions_needing_reminders)} completions")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in training calendar maintenance: {str(e)}")

# Start calendar reminder service
@background_startup
async def start_calendar_reminders():
    """Start the calendar reminder background service."""
    import asyncio
    asyncio.create_task(CalendarReminderService.start_reminder_scheduler())

# Start training reminder service
@background_startup
async def start_training_reminders():
    """Start the training reminder background service."""
    import asyncio
    from app.services.training_reminder_scheduler import TrainingReminderScheduler
    asyncio.create_task(TrainingReminderScheduler.start_training_reminder_scheduler())

# Document expiration reminder scheduler
@background_startup
@repeat_every(seconds=60 * 60 * 12)  # Run every 12 hours
async def document_expiration_reminders():
    """Check for expiring documents and send reminders to facility administrators."""
    try:
        from app.services.document_expiration_service import DocumentExpirationService
        logger.info("Starting document expiration reminder check")
        await DocumentExpirationService.check_and_send_document_expiration_reminders()
        await DocumentExpirationService.check_expired_documents()
        logger.info("Document expiration reminder check completed")
    except Exception as e:
        logger.error(f"Error in document expiration reminder scheduler: {str(e)}")
        logger.error(traceback.format_exc())

# Facility task notification scheduler
@background_startup
@repeat_every(seconds=60 * 60 * 6)  # Run every 6 hours
async def facility_task_notifications():
    """Check for upcoming and overdue facility tasks and send notifications."""
    try:
        from app.services.facility_task_notification_service import FacilityTaskNotificationService
        logger.info("Starting facility task notification check")
        await FacilityTaskNotificationService.check_and_send_task_reminders()
        await FacilityTaskNotificationService.check_and_send_overdue_task_notifications()
        logger.info("Facility task notification check completed")
    except Exception as e:
        logger.error(f"Error in facility task notification scheduler: {str(e)}")
        logger.error(traceback.format_exc())

# Daily facility digest scheduler
@background_startup
@repeat_every(seconds=60 * 60 * 24)  # Run once per day
async def daily_facility_digest():
    """Generate and send daily facility digests to administrators."""
    try:
        from app.services.facility_task_notification_service import FacilityTaskNotificationService
        from app.database import SessionLocal
        from app.models.facility import Facility
        
        logger.info("Starting daily facility digest generation")
        db = SessionLocal()
        
        try:
            # Get all active facilities
            facilities = db.query(Facility).filter(Facility.is_active == True).all()
            
            digests_sent = 0
            for facility in facilities:
                try:
                    result = await FacilityTaskNotificationService.generate_daily_facility_digest(
                        db, facility.id
                    )
                    if result.get("digest_sent", False):
                        digests_sent += 1
                except Exception as e:
                    logger.error(f"Error generating digest for facility {facility.id}: {str(e)}")
                    continue
            
            logger.info(f"Daily facility digest generation completed: {digests_sent} digests sent for {len(facilities)} facilities")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in daily facility digest scheduler: {str(e)}")
@app.get("/")
async def root():
    return {"message": "Welcome to Encompliance.io API"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()} 