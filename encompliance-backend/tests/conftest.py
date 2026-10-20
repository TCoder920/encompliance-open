import os

# Force tests to use a local SQLite database before any app imports occur.
# Use an absolute path to avoid CWD surprises when tests are executed from different locations.
TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_app.db"))
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

# CRITICAL: Import all models BEFORE importing app.database or app.main
# This ensures Base.metadata has all tables registered before the engine is created
import app.models  # noqa: F401

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.user import User


@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a clean database session for testing."""
    # Import all models to ensure they're registered
    import app.models  # noqa: F401
    
    # Create an in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables in the test database
    Base.metadata.create_all(engine)
    
    # Create a session factory bound to the engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create a session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Dispose the engine to close all connections
        engine.dispose()


@pytest.fixture
def db() -> Session:
    """
    Database session bound to the same engine the FastAPI app/TestClient uses.
    This keeps integration tests (e.g., calendar API) consistent with route dependencies.
    """
    from app.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = AsyncMock()
    
    # Configure the mock vector stores create method
    mock_vector_store = MagicMock()
    mock_vector_store.id = "mock-vector-store-id"
    mock_client.beta.vector_stores.create.return_value = mock_vector_store
    
    return mock_client


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="session", autouse=True)
def mock_env_variables():
    """Set up environment variables for testing."""
    os.environ["SMTP_SERVER"] = "localhost"
    os.environ["SMTP_PORT"] = "1025"
    os.environ["SMTP_USERNAME"] = "testuser"
    os.environ["SMTP_PASSWORD"] = "testpassword"
    os.environ["SMTP_FROM_EMAIL"] = "noreply@encompliance.com"
    os.environ["OTP_EXPIRY_MINUTES"] = "10"
    os.environ["MAX_OTP_ATTEMPTS"] = "3"
    os.environ["TESTING"] = "true"
    
    # Yield to tests
    yield
    
    # Clean up if needed
    # os.environ.pop("SMTP_SERVER", None)
    # etc.


@pytest.fixture(autouse=True)
def mock_smtp_server():
    """Mock SMTP server for all tests."""
    with patch('smtplib.SMTP') as mock_smtp:
        # Setup mock
        instance = mock_smtp.return_value
        instance.starttls.return_value = (220, b'Ready to start TLS')
        instance.login.return_value = (235, b'Authentication successful')
        instance.send_message.return_value = {}
        instance.quit.return_value = (221, b'Bye')
        
        yield mock_smtp


@pytest.fixture(scope="session", autouse=True)
def init_test_database():
    """
    Ensure the core tables exist on the same engine used by the FastAPI TestClient.
    This prevents OperationalError errors when API tests hit the database before any
    fixtures have created tables (e.g., the 'users' table for OTP/WebAuthn flows).
    """
    # Import all models to ensure they're registered with Base.metadata
    # This must happen before importing app.main or creating the engine
    import app.models  # noqa: F401
    
    # Now import database after models are registered
    from app.database import engine
    
    # Create all tables - this is idempotent (won't recreate existing tables)
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Optional: cleanup after all tests (commented out to preserve test data for debugging)
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True, scope="function")
def ensure_tables_exist_before_test():
    """
    Ensure tables exist on the actual SessionLocal engine before each test.
    This is a safety net to ensure tables are present even if they were dropped.
    Uses create_all which is idempotent - won't recreate existing tables.
    """
    # Import all models to ensure they're registered with Base.metadata
    import app.models  # noqa: F401
    from app.database import engine

    # Create all tables - idempotent operation
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Don't drop tables between tests - keep data for debugging and test isolation
