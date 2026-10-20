"""
Customer Support Portal Entry Point
-----------------------------------
Bootstrap FastAPI application that powers the secure support tooling API surface.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import support_portal_engine, SupportPortalBase
from app.api.routes import support_portal_auth, support_portal, support_tickets
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import all support portal models to ensure they're registered with SupportPortalBase.metadata
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.support_portal_account import SupportPortalAccount  # noqa: F401
from app.models.support_ticket import (  # noqa: F401
    SupportTicket,
    SupportTicketComment,
    SupportAgentProfile,
)

settings = get_settings()

try:
    SupportPortalBase.metadata.create_all(bind=support_portal_engine)
except Exception as e:
    print(f"Error creating support portal tables: {e}")
    print("Creating tables individually as a fallback...")
    try:
        SupportPortalBase.metadata.clear()
        from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
        from sqlalchemy.sql import func
        
        Table(
            'support_portal_users', 
            SupportPortalBase.metadata,
            Column('id', Integer, primary_key=True, index=True),
            Column('username', String, unique=True, index=True),
            Column('email', String, unique=True, index=True),
            Column('hashed_password', String),
            Column('roles', String),
            Column('created_at', DateTime(timezone=True), default=func.now()),
            Column('updated_at', DateTime(timezone=True), default=func.now(), onupdate=func.now()),
            Column('is_active', Boolean, default=True)
        )
        
        Table(
            'audit_logs',
            SupportPortalBase.metadata,
            Column('id', Integer, primary_key=True, index=True),
            Column('support_account_id', Integer, ForeignKey("support_portal_users.id"), nullable=True),
            Column('action', String, nullable=False, index=True),
            Column('target', String, nullable=True),
            Column('timestamp', DateTime(timezone=True), default=func.now(), index=True),
            Column('ip_address', String, nullable=True),
            Column('internal_ip_address', String, nullable=True),
            Column('details', JSON, nullable=True)
        )
        
        SupportPortalBase.metadata.create_all(bind=support_portal_engine)
        print("Successfully created support portal tables individually")
    except Exception as e2:
        print(f"Error in fallback table creation: {e2}")

support_portal_app = FastAPI(
    title="EnCompliance Customer Support API",
    description="API for customer support tooling, insights, and case management.",
    version="0.1.0"
)

allowed_origins = getattr(
    settings, 
    'SUPPORT_PORTAL_CORS_ORIGINS',
    [
        "http://localhost:5200"
    ]
)

support_portal_app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@support_portal_app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    import traceback
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Log the exception with context
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred", "error_type": str(type(exc).__name__)},
    )

support_portal_app.include_router(support_portal_auth.router, prefix="/auth", tags=["Support Portal Auth"])
support_portal_app.include_router(support_portal.router, prefix="/support", tags=["Support Portal Operations"])
support_portal_app.include_router(support_tickets.router, prefix="/api/v1/support", tags=["Support Tickets"])

# Import WebSocket routes
from app.api.routes import support_websocket
support_portal_app.include_router(support_websocket.router, prefix="/api/v1/support", tags=["WebSocket"])

@support_portal_app.on_event("startup")
async def startup_event():
    """Start background tasks for support ticket automation."""
    import asyncio
    from app.tasks.support_ticket_tasks import run_support_ticket_tasks
    
    # Schedule periodic tasks (run every hour)
    async def periodic_tasks():
        while True:
            await asyncio.sleep(3600)  # Wait 1 hour
            await run_support_ticket_tasks()
    
    # Start background task
    asyncio.create_task(periodic_tasks())
    logger.info("Support ticket background tasks started")

@support_portal_app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the EnCompliance Customer Support API"}


@support_portal_app.get("/health", tags=["Health"])
async def health_check():
    """
    Public health check endpoint for monitoring and load balancers.
    Does not require authentication.
    """
    from datetime import datetime
    from sqlalchemy import text
    try:
        # Quick database connectivity check
        from app.database import support_portal_engine
        with support_portal_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)[:100]}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "support-portal",
        "version": "0.1.0",
        "database": db_status
    }


@support_portal_app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint - verifies the service is ready to accept traffic.
    More comprehensive than /health.
    """
    from datetime import datetime
    from sqlalchemy import text
    checks = {
        "database": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        from app.database import support_portal_engine
        with support_portal_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    
    all_ready = all(checks.values() if k != "timestamp" else True for k in checks.keys())
    
    status_code = 200 if all_ready else 503
    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks
    }