import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import jwt
from datetime import datetime, timedelta

from app import main
from app.database import Base, get_db
from app.models.user import User
from app.auth.utils import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

app = main.app


# Create a test database and session
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Setup function to override the get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test client
client = TestClient(app)


def create_test_user(db_session):
    """Helper function to create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$RvhLAbDcgYUaGh4p96W1EOeeTLvkW7yAe9REm3FkpvIU/fh/GKHF.", # 'password'
        full_name="Test User",
        operation_name="Test Operation",
        state="CA",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_test_token(username):
    """Helper function to create a test token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@pytest.fixture(scope="function")
def test_db():
    """Setup test database and override get_db dependency, cleanup after test"""
    # Store original dependency before overriding
    stored_original = main.app.dependency_overrides.get(get_db)
    
    # Override the dependency for this test
    main.app.dependency_overrides[get_db] = override_get_db
    
    # Import all models to ensure they're registered
    import app.models  # noqa: F401
    
    # Create the database tables
    Base.metadata.create_all(bind=test_engine)
    
    yield
    
    # Drop all tables after test
    Base.metadata.drop_all(bind=test_engine)
    
    # Restore original dependency or remove override
    if stored_original is not None:
        main.app.dependency_overrides[get_db] = stored_original
    else:
        main.app.dependency_overrides.pop(get_db, None)


def test_get_me_unauthorized():
    """Test that unauthorized access is prevented"""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.text


def test_get_me_success(test_db):
    """Test successful retrieval of user information"""
    # Create a test user and keep session open
    db = TestingSessionLocal()
    user = create_test_user(db)
    
    # Store user attributes before closing session
    user_email = user.email
    user_username = user.username
    user_full_name = user.full_name
    user_operation_name = user.operation_name
    user_state = user.state
    
    # Close the session
    db.close()
    
    # Create token for the user
    token = create_test_token(user_username)
    
    # Make request with token
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_email
    assert data["username"] == user_username
    assert data["full_name"] == user_full_name
    assert data["operation_name"] == user_operation_name
    assert data["state"] == user_state


def test_get_me_with_inactive_user(test_db):
    """Test that inactive users cannot access their profile"""
    # Create a test user who is inactive and keep session open
    db = TestingSessionLocal()
    user = create_test_user(db)
    
    # Store username before making changes
    username = user.username
    
    # Make user inactive
    user.is_active = False
    db.commit()
    db.close()
    
    # Create token for the user
    token = create_test_token(username)
    
    # Make request with token
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response
    assert response.status_code == 400
    assert "Inactive user" in response.text


def test_get_me_with_expired_token(test_db):
    """Test that expired tokens are rejected"""
    # Create a test user and capture username
    db = TestingSessionLocal()
    user = create_test_user(db)
    username = user.username
    db.close()
    
    # Create expired token for the user
    expire = datetime.utcnow() - timedelta(minutes=1)  # Token expired 1 minute ago
    to_encode = {"sub": username, "exp": expire}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Make request with expired token
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response
    assert response.status_code == 401
    assert "Could not validate credentials" in response.text 