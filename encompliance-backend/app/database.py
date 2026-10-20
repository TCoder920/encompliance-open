"""
Database Configuration
---------------------
This file manages the database connection and session configuration for the EnCompliance backend.
It provides:
- SQLAlchemy engine configuration
- Database session management
- Connection pooling settings
- Database URL configuration
- Session dependency injection for FastAPI routes
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# --- Main Application Database ---
# Get database URL from environment variables or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/encompliance")

# Create SQLAlchemy engine with SQLite-specific configurations
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models (shared or separate?) - Assuming separate for now
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Support Portal Database ---
SUPPORT_PORTAL_DATABASE_URL = os.getenv(
    "SUPPORT_PORTAL_DATABASE_URL",
    "sqlite:///./support-portal.db",
)
support_portal_engine = create_engine(
    SUPPORT_PORTAL_DATABASE_URL, connect_args={"check_same_thread": False}
)  # SQLite specific arg
SupportPortalSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=support_portal_engine
)
SupportPortalBase = declarative_base()  # Separate Base for support portal models


def get_support_portal_db():
    """Dependency to provide a session for the support portal database."""
    db = SupportPortalSessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Potentially shared utility (if needed) ---
# You might want a way to initialize both databases or manage migrations separately.
