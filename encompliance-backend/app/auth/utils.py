"""
Authentication Utilities Module

This module provides core authentication utilities for the EnCompliance application.
It handles password hashing, JWT token creation and validation, and token blacklisting.

Key functionalities:
- Password hashing and verification using bcrypt
- JWT token creation and validation
- Token blacklisting system for secure logout
- User authentication against database
- Token expiration management

Dependencies:
- passlib: For password hashing
- jose: For JWT operations
- sqlalchemy: For database operations
"""

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import os
import uuid
from sqlalchemy.orm import Session
from app.models.token import BlacklistedToken

# Load environment variables
load_dotenv()

# JWT settings
from app.core.config import get_settings
SECRET_KEY = get_settings().JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
print(f"Token expiry: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add JWT ID and expiration time
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def is_token_blacklisted(db: Session, token_data: Dict[str, Any]) -> bool:
    """
    Check if a token is blacklisted.
    
    Args:
        db: Database session
        token_data: Decoded token data containing 'jti' and 'exp'
        
    Returns:
        True if token is blacklisted, False otherwise
    """
    # Get the JTI from the token
    jti = token_data.get("jti")
    
    # If no JTI, token is from before we added JTIs and is not blacklisted
    if not jti:
        return False
    
    # Check if JTI is in the blacklist table
    blacklisted_token = db.query(BlacklistedToken).filter(
        BlacklistedToken.token_jti == jti
    ).first()
    
    # Return True if found (blacklisted), False otherwise
    return blacklisted_token is not None

def blacklist_token(
    db: Session, 
    token_data: Dict[str, Any], 
    user_id: int
) -> BlacklistedToken:
    """
    Add a token to the blacklist.
    
    Args:
        db: Database session
        token_data: Decoded token data containing 'jti' and 'exp'
        user_id: ID of the user who owns the token
        
    Returns:
        The created BlacklistedToken instance
    
    Raises:
        ValueError: If token does not have a JTI or expiry
    """
    jti = token_data.get("jti")
    exp = token_data.get("exp")
    
    if not jti:
        raise ValueError("Token does not have a JTI")
    
    if not exp:
        raise ValueError("Token does not have an expiry")
    
    # Convert exp (Unix timestamp) to datetime
    expires_at = datetime.fromtimestamp(exp)
    
    # Create BlacklistedToken entry
    blacklisted_token = BlacklistedToken(
        token_jti=jti,
        user_id=user_id,
        expires_at=expires_at
    )
    
    # Add to database
    db.add(blacklisted_token)
    db.commit()
    db.refresh(blacklisted_token)
    
    return blacklisted_token

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user."""
    from app.models.user import User
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # Check if email was provided instead of username
        user = db.query(User).filter(User.email == username).first()
        if not user:
            return False

    if not verify_password(password, user.hashed_password):
        return False

    return user

def clean_expired_tokens(db: Session) -> int:
    """
    Remove expired tokens from the blacklist to prevent the table from growing indefinitely.
    
    Args:
        db: Database session
        
    Returns:
        int: The number of tokens that were removed
    """
    # Get current time
    now = datetime.utcnow()
    
    # Delete tokens that have expired
    result = db.query(BlacklistedToken).filter(
        BlacklistedToken.expires_at < now
    ).delete()
    
    # Commit the changes
    db.commit()
    
    return result 