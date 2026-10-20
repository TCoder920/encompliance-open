"""
Authentication Module
-------------------
This module handles user authentication and authorization for the EnCompliance system.
It provides:
- User registration and login
- JWT token management
- Password hashing and verification
- Session management
- Authentication middleware
- Token refresh and revocation
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, Token, User as UserSchema, UserLogin
from app.auth.utils import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.dependencies import get_current_user

router = APIRouter(tags=["Authentication"])

@router.post("/signup", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    """
    # Check if email already exists
    db_user_email = db.query(User).filter(User.email == user.email).first()
    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate username if not provided
    username = user.get_username()
    
    # Check if username already exists
    db_user_username = db.query(User).filter(User.username == username).first()
    if db_user_username:
        # Add numeric suffix to username if it already exists
        base_username = username
        counter = 1
        while db_user_username:
            username = f"{base_username}{counter}"
            db_user_username = db.query(User).filter(User.username == username).first()
            counter += 1
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        operation_name=user.operation_name,
        operation_type=user.operation_type,
        state=user.state,
        phone_number=user.phone_number
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login")
async def login_for_access_token(request: Request, db: Session = Depends(get_db)):
    """Support JSON and legacy forms through the same account/OTP policy."""
    from app.api.routes.auth import LoginRequest, login
    try:
        values = await request.json() if request.headers.get("content-type", "").startswith("application/json") else await request.form()
        credentials = LoginRequest(username=values.get("username", ""), password=values.get("password", ""))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=422, detail="Invalid login payload")
    user = db.query(User).filter(User.email == credentials.username).first()
    if user:
        credentials.username = user.username
    return await login(credentials, db)


@router.post("/email-login")
async def login_with_email(login_data: UserLogin, db: Session = Depends(get_db)):
    """The legacy email endpoint must enforce the same account/OTP checks."""
    from app.api.routes.auth import LoginRequest, login
    user = db.query(User).filter(User.email == login_data.email).first()
    username = user.username if user else login_data.email
    return await login(LoginRequest(username=username, password=login_data.password), db)


@router.post("/refresh-token", response_model=Token)
async def refresh_access_token(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Header(None, alias="x-token"),
    db: Session = Depends(get_db)
):
    """
    Refresh an access token if it's valid.
    """
    # Extract token from Authorization header if provided
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided for refresh",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Verify the current token is valid by getting the user
        user = await get_current_user(token=token, db=db)
        
        # Create a new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        ) 