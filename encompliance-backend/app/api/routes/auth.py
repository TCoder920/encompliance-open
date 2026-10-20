"""
Authentication Routes
-------------------
This module defines the authentication-related API endpoints for the EnCompliance system.
It provides:
- User registration endpoints
- Login and logout functionality
- Password reset and recovery
- Email verification
- Multi-factor authentication
- Session management
- Session-based signup for deferred user creation

Educational Note: Implements session-based signup pattern to minimize database
pollution from incomplete registrations, following data minimization principles.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from typing import List
from fastapi.responses import JSONResponse
import logging
from jose import jwt

from app.database import get_db
from app.models.user import User
from app.models.facility_type import FacilityType
from app.models.regulation import Regulation
from app.models.user_document import UserDocument
from app.models.otp import OTP, OTPType
from app.models.signup_session import SignupSession
from app.schemas.user import (
    UserSignupStep1, 
    UserSignupStep2, 
    UserSignupStep3, 
    User as UserSchema,
    OTPVerification,
    SessionSignupStep1,
    SessionSignupStep1Point5,
    SessionSignupStep2,
    SessionSignupStep3,
    SessionSignupStep3FacilityAdmin,
    SessionSignupResponse,
    SessionOTPVerification,
    SessionSignupStep1Point75
)
from app.services.signup_session_service import SignupSessionService
from app.auth.otp_utils import (
    generate_otp,
    create_otp_record,
    verify_otp as verify_otp_util,
    send_email_otp
)
from app.auth.utils import get_password_hash, create_access_token, blacklist_token, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.dependencies import get_current_user, get_token_from_request
from datetime import timedelta, datetime
from app.core.config import get_settings
from app.models.facility_invitation import FacilityInvitation
from openai import AsyncOpenAI
from app.core.openai_utils import (
    get_or_create_user_vector_store, 
    upload_regulation_to_openai,
    update_vector_store,
    delete_user_openai_files,
    configure_assistant_with_user_model,
    create_user_assistant
)
from app.utils.owasp_protections import PasswordPolicy
import asyncio
import traceback
from app.models.token import BlacklistedToken
from sqlalchemy.sql import func

settings = get_settings()
router = APIRouter(tags=["authentication"])

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# NEW SESSION-BASED SIGNUP ENDPOINTS

@router.post("/session-signup/step1", response_model=SessionSignupResponse, status_code=status.HTTP_201_CREATED)
async def session_signup_step1(signup_data: SessionSignupStep1, db: Session = Depends(get_db)):
    """
    Session-based Step 1: Create temporary signup session with basic information
    No permanent user record created until email verification
    """
    # Validate password strength
    password_validation = PasswordPolicy.validate_password_strength(signup_data.password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_validation["message"]
        )
    
    # Create signup session
    session = SignupSessionService.create_session(
        db=db,
        email=signup_data.email,
        password=signup_data.password,
        full_name=signup_data.full_name,
        operation_name=signup_data.operation_name,
        phone_number=signup_data.phone_number
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered or rate limit exceeded"
        )
    
    return SessionSignupResponse(
        session_token=session.session_token,
        step_completed=int(session.step_completed),
        expires_at=session.expires_at
    )

@router.post("/session-signup/step1point5", response_model=SessionSignupResponse)
async def session_signup_step1point5(signup_data: SessionSignupStep1Point5, db: Session = Depends(get_db)):
    """
    Session-based Step 1.5: User role selection (Facility Administrator vs Regular User)
    
    Note: Facility administrators are users with a pro subscription who manage facility operations.
    """
    session = SignupSessionService.update_session_step1point5(
        db=db,
        session_token=signup_data.session_token,
        user_role=signup_data.user_role
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found, expired, or invalid role"
        )
    
    return SessionSignupResponse(
        session_token=session.session_token,
        step_completed=int(session.step_completed),
        expires_at=session.expires_at
    )

@router.post("/session-signup/step1point75", response_model=SessionSignupResponse)
async def session_signup_step1point75(signup_data: SessionSignupStep1Point75, db: Session = Depends(get_db)):
    """
    Session-based Step 1.75: Tier selection (Free vs Pro)
    """
    session = SignupSessionService.update_session_step1point75(
        db=db,
        session_token=signup_data.session_token,
        selected_tier=signup_data.selected_tier
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found, expired, or invalid tier"
        )
    
    return SessionSignupResponse(
        session_token=session.session_token,
        step_completed=int(session.step_completed),
        expires_at=session.expires_at
    )

@router.post("/session-signup/step2", response_model=SessionSignupResponse)
async def session_signup_step2(signup_data: SessionSignupStep2, db: Session = Depends(get_db)):
    """
    Session-based Step 2: Update session with state information
    """
    session = SignupSessionService.update_session_step2(
        db=db,
        session_token=signup_data.session_token,
        state=signup_data.state
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    return SessionSignupResponse(
        session_token=session.session_token,
        step_completed=int(session.step_completed),
        expires_at=session.expires_at
    )

@router.post("/session-signup/step3-facility-admin")
async def session_signup_step3_facility_admin(signup_data: SessionSignupStep3FacilityAdmin, db: Session = Depends(get_db)):
    """
    Session-based Step 3 for Facility Administrators: Create facility and send verification email
    
    Note: Facility administrators are users with a pro subscription who manage facility operations.
    """
    # Prepare facility data
    facility_data = {
        "facility_name": signup_data.facility_name,
        "facility_address": signup_data.facility_address,
        "facility_city": signup_data.facility_city,
        "facility_state": signup_data.facility_state,
        "facility_zip": signup_data.facility_zip,
        "facility_phone": signup_data.facility_phone,
        "facility_email": signup_data.facility_email,
        "trial_days": signup_data.trial_days
    }
    
    session = SignupSessionService.update_session_step3_facility_admin(
        db=db,
        session_token=signup_data.session_token,
        facility_data=facility_data
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    # Generate and send OTP for session verification
    try:
        otp_code = generate_otp()
        
        # Create OTP record linked to session token
        create_otp_record(db, None, session.session_token, OTPType.EMAIL, otp_code)
        
        # Send email
        success, message = send_email_otp(session.email, otp_code)
        
        if not success:
            logger.error(f"Failed to send email OTP for session {session.session_token}: {message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send verification email: {message}"
            )
        
        logger.info(f"Generated and sent email OTP for facility admin session {session.session_token}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "session_signup_pending_email_verification",
                "session_token": session.session_token,
                "email": session.email,
                "user_type": "facility_admin"
            }
        )
        
    except Exception as e:
        logger.error(f"Error during facility admin session OTP process: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the OTP process. Please try again later."
        )

@router.post("/session-signup/step3")
async def session_signup_step3(signup_data: SessionSignupStep3, db: Session = Depends(get_db)):
    """
    Session-based Step 3: Complete signup data and send verification email
    Still no permanent user record created
    """
    session = SignupSessionService.update_session_step3(
        db=db,
        session_token=signup_data.session_token,
        facility_types=signup_data.selected_facility_types
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    # Generate and send OTP for session verification
    try:
        otp_code = generate_otp()
        
        # Create OTP record linked to session token
        create_otp_record(db, None, session.session_token, OTPType.EMAIL, otp_code)
        
        # Send email
        success, message = send_email_otp(session.email, otp_code)
        
        if not success:
            logger.error(f"Failed to send email OTP for session {session.session_token}: {message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send verification email: {message}"
            )
        
        logger.info(f"Generated and sent email OTP for session {session.session_token}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "session_signup_pending_email_verification",
                "session_token": session.session_token,
                "email": session.email
            }
        )
        
    except Exception as e:
        logger.error(f"Error during session OTP process: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the OTP process. Please try again later."
        )


@router.post("/session-signup/step3-invitation")
async def session_signup_step3_invitation(signup_data: dict, db: Session = Depends(get_db)):
    """
    Complete signup for invited users.
    Validates invitation and stores invitation code in session.
    """
    session_token = signup_data.get("session_token")
    invitation_code = signup_data.get("invitation_code")
    
    pass  # Sensitive authentication data must not be logged.
    
    if not session_token or not invitation_code:
        logger.error(f"Missing required parameters - session_token: {bool(session_token)}, invitation_code: {bool(invitation_code)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session token and invitation code are required"
        )
    
    try:
        pass  # Sensitive authentication data must not be logged.
        # Validate invitation
        invitation = db.query(FacilityInvitation).filter(
            FacilityInvitation.invitation_code == invitation_code
        ).first()
        
        if not invitation:
            pass  # Sensitive authentication data must not be logged.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
            
        logger.info(f"Found invitation: {invitation.id}, status: {invitation.status}, is_valid: {invitation.is_valid}")
            
        if not invitation.is_valid:
            status_reason = "expired" if invitation.is_expired else "already used or cancelled"
            logger.error(f"Invalid invitation: {status_reason}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invitation is {status_reason}"
            )
        
        pass  # Sensitive authentication data must not be logged.
        # Update session with invitation code
        session = SignupSessionService.update_session_invitation(
            db=db,
            session_token=session_token,
            invitation_code=invitation_code
        )
        
        if not session:
            pass  # Sensitive authentication data must not be logged.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired"
            )
        
        logger.info(f"Session updated successfully, generating OTP for email: {session.email}")
        # Generate and send OTP for session verification
        otp_code = generate_otp()
        
        # Create OTP record linked to session token
        create_otp_record(db, None, session.session_token, OTPType.EMAIL, otp_code)
        
        # Send email
        success, message = send_email_otp(session.email, otp_code)
        
        if not success:
            logger.error(f"Failed to send email OTP for invitation session {session.session_token}: {message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send verification email: {message}"
            )
        
        logger.info(f"Generated and sent email OTP for invitation session {session.session_token}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "session_signup_pending_email_verification",
                "session_token": session.session_token,
                "email": session.email
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in invitation signup: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete invitation signup"
        )


@router.post("/verify-session-signup-email")
async def verify_session_signup_email(otp_data: SessionOTPVerification, db: Session = Depends(get_db)):
    """
    Verify session-based signup email OTP and create permanent user account
    This is where the actual user record is created
    """
    # Get session
    session = SignupSessionService.get_session(db, otp_data.session_token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    # Verify OTP using session token as recipient
    is_valid_otp, message = verify_otp_util(db, None, session.session_token, OTPType.EMAIL, otp_data.otp_code)
    
    if not is_valid_otp:
        # Increment verification attempts
        if not SignupSessionService.increment_verification_attempts(db, otp_data.session_token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum verification attempts exceeded. Please start signup again."
            )
        
        logger.warning(f"Invalid session OTP attempt for session {otp_data.session_token}: {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Create permanent user account from session data
    try:
        signup_data = session.signup_data
        
        # Generate username
        username = signup_data["email"].split('@')[0]
        
        # Check if username already exists and add suffix if needed
        db_user_username = db.query(User).filter(User.username == username).first()
        if db_user_username:
            base_username = username
            counter = 1
            while db_user_username:
                username = f"{base_username}{counter}"
                db_user_username = db.query(User).filter(User.username == username).first()
                counter += 1
        
        # Create user with all session data
        user_role_str = signup_data.get("user_role", "regular_user")
        is_facility_admin = user_role_str == "facility_admin"
        is_invitation = "invitation_code" in signup_data
        
        # Import UserRole enum
        from app.models.user import UserRole
        
        # Determine user role and subscription status
        if is_invitation:
            # Invited users are team members with pro access through facility
            subscription_status = "free"  # Individual subscription remains free
            user_role = UserRole.TEAM_MEMBER
        elif is_facility_admin:
            # Use selected tier from session data, fallback to pro for facility admins
            selected_tier = signup_data.get("selected_tier", "pro")
            subscription_status = selected_tier
            user_role = UserRole.FACILITY_ADMIN
        else:
            # Regular users (both free and pro)
            selected_tier = signup_data.get("selected_tier", "free")
            # All regular users start as free - pro users upgrade after payment
            subscription_status = "free"
            user_role = UserRole.FREE_USER
        
        db_user = User(
            email=signup_data["email"],
            username=username,
            hashed_password=signup_data["hashed_password"],
            full_name=signup_data["full_name"],
            operation_name=signup_data["operation_name"],
            phone_number=signup_data.get("phone_number"),
            state=signup_data.get("state"),
            facility_type=", ".join(signup_data.get("facility_types", [])),
            subscription_status=subscription_status,
            user_role=user_role,
            is_active=True,  # User is immediately active after verification
            email_verified=True,  # Email is verified
            last_login=datetime.utcnow()
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Created permanent user account from session: {session.session_token}")
        
        # Handle facility administrator setup
        if is_facility_admin and "facility_data" in signup_data:
            try:
                from app.models.facility import Facility
                from app.services.stripe_service import StripeService
                
                facility_data = signup_data["facility_data"]
                
                # Create facility
                db_facility = Facility(
                    facility_name=facility_data["facility_name"],
                    facility_address=facility_data.get("facility_address"),
                    facility_city=facility_data.get("facility_city"),
                    facility_state=facility_data.get("facility_state"),
                    facility_zip=facility_data.get("facility_zip"),
                    facility_phone=facility_data.get("facility_phone"),
                    facility_email=facility_data.get("facility_email"),
                    admin_user_id=db_user.id,
                    is_active=False  # Facility starts inactive until payment is completed
                )
                
                db.add(db_facility)
                db.commit()
                db.refresh(db_facility)
                
                # Link user to facility
                db_user.facility_id = db_facility.id
                db.commit()
                db.refresh(db_user)
                
                logger.info(f"Created facility {db_facility.id} for admin user {db_user.id}")
                
                # Create Stripe customer but NOT the subscription yet
                # The subscription will be created when user completes payment via upgrade-to-pro
                try:
                    stripe_service = StripeService()
                    
                    # Create customer
                    customer = stripe_service.create_customer(
                        email=db_user.email,
                        name=db_user.full_name,
                        facility_name=db_facility.facility_name
                    )
                    
                    # Update facility with Stripe customer ID
                    db_facility.stripe_customer_id = customer.id
                    
                    db.commit()
                    db.refresh(db_user)
                    db.refresh(db_facility)
                    
                    logger.info(f"Created Stripe customer for facility {db_facility.id}, user {db_user.id} remains free until payment completion")
                    
                except Exception as e:
                    logger.error(f"Error creating Stripe customer: {str(e)}")
                    # Don't fail the whole process for Stripe errors
                
            except Exception as e:
                logger.error(f"Error creating facility for admin user: {str(e)}")
                # Don't fail the whole process for facility creation errors
        
        # Handle invitation signup - join user to facility
        if "invitation_code" in signup_data:
            try:
                from app.models.facility_invitation import FacilityInvitation
                from app.models.subscription import Subscription
                from app.services.stripe_service import StripeService
                from sqlalchemy.orm import joinedload
                
                invitation = db.query(FacilityInvitation).options(
                    joinedload(FacilityInvitation.facility)
                ).filter(
                    FacilityInvitation.invitation_code == signup_data["invitation_code"]
                ).first()
                
                if invitation and invitation.is_valid:
                    # Add user to facility
                    db_user.facility_id = invitation.facility.id
                    
                    # Get facility admin to inherit state and facility_type
                    facility_admin = db.query(User).filter(
                        User.id == invitation.facility.admin_user_id
                    ).first()
                    
                    if facility_admin:
                        # Inherit admin's state and facility_type
                        db_user.state = facility_admin.state
                        db_user.facility_type = facility_admin.facility_type
                        logger.info(f"New user {db_user.id} inheriting state '{facility_admin.state}' and facility_type '{facility_admin.facility_type}' from admin")
                        
                        # Commit the user changes first
                        db.commit()
                        db.refresh(db_user)
                        
                        # Associate documents based on inherited state and facility types
                        if db_user.state and db_user.facility_type:
                            try:
                                facility_types = [ft.strip() for ft in db_user.facility_type.split(',') if ft.strip()]
                                await associate_user_documents(db, db_user.id, db_user.state, facility_types)
                                db.commit()
                                logger.info(f"Associated documents for new team member {db_user.id} based on inherited state/facility types")
                            except Exception as e:
                                logger.error(f"Error associating documents for invited user {db_user.id}: {str(e)}")
                    
                    # Mark invitation as used
                    invitation.mark_as_used(db_user.id)
                    
                    # NOTE: Removed automatic seat addition - invitations should only work when capacity exists
                    # The seat capacity is checked when the invitation is created, not when it's accepted
                    
                    db.commit()
                    logger.info(f"User {db_user.id} joined facility {invitation.facility.id} via invitation")
                    
                    # Send welcome notification
                    from app.models.notification import Notification, NotificationType
                    notification = Notification(
                        user_id=db_user.id,
                        sender_id=invitation.created_by_user_id,
                        title="Welcome to the Facility",
                        message=f"Welcome to {invitation.facility.facility_name}! You now have access to facility-wide training and compliance resources.",
                        type=NotificationType.FACILITY_JOINED.value
                    )
                    db.add(notification)
                    
                    # Notify admin
                    admin_notification = Notification(
                        user_id=invitation.created_by_user_id,
                        sender_id=db_user.id,
                        title="User Joined Facility",
                        message=f"{db_user.full_name} has joined {invitation.facility.facility_name}.",
                        type=NotificationType.FACILITY_UPDATE.value
                    )
                    db.add(admin_notification)
            
            except Exception as e:
                logger.error(f"Error processing invitation for user {db_user.id}: {str(e)}")
                # Don't fail the signup for invitation errors
        
        # Associate user with relevant documents (for all regular users, both free and pro)
        if not is_facility_admin and not is_invitation:
            try:
                await associate_user_documents(
                    db, 
                    db_user.id, 
                    signup_data.get("state"), 
                    signup_data.get("facility_types", [])
                )
                db.commit()
                logger.info(f"Associated documents for user {db_user.id}")
            except Exception as e:
                logger.error(f"Error associating documents for user {db_user.id}: {str(e)}")
        
        # Initialize OpenAI resources
        try:
            logger.info(f"Initializing OpenAI resources for new user {db_user.id}")
            storage_path = settings.PDF_STORAGE_PATH
            
            # Determine model based on subscription status
            model_name = 'gpt-4.1-mini' if db_user.subscription_status == 'pro' else 'gpt-4.1-nano'
            
            # Create assistant for new user
            await create_user_assistant(db_user.id, db, openai_client, model_name=model_name)
            db.refresh(db_user)
            logger.info(f"Created assistant for new user {db_user.id}")
            
            # Update vector store with user documents
            result = await update_vector_store(db_user.id, db, openai_client, storage_path)
            if not result["success"]:
                logger.warning(f"Errors occurred during vector store initialization: {result['errors']}")
            else:
                logger.info(f"Successfully initialized vector store for user {db_user.id}")
            
        except Exception as e:
            logger.error(f"Error initializing OpenAI resources: {str(e)}")
        
        # Clean up session
        SignupSessionService.delete_session(db, otp_data.session_token)
        
        # Create and return access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.username},
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        logger.error(f"Error creating user from session: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred creating your account. Please try again."
        )

@router.post("/resend-session-signup-email")
async def resend_session_signup_email(data: dict, db: Session = Depends(get_db)):
    """
    Resend verification email for a signup session
    """
    session_token = data.get("session_token")
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session token is required"
        )
    
    session = SignupSessionService.get_session(db, session_token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    if session.step_completed < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete signup steps before requesting email verification"
        )
    
    try:
        otp_code = generate_otp()
        create_otp_record(db, None, session.session_token, OTPType.EMAIL, otp_code)
        
        success, message = send_email_otp(session.email, otp_code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send verification email: {message}"
            )
        
        return {"success": True, "message": "Verification email sent successfully"}
        
    except Exception as e:
        logger.error(f"Error resending session verification email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email"
        )

# LEGACY ENDPOINTS (kept for backward compatibility)

@router.post("/signup/step1", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def signup_step1(user_data: UserSignupStep1, db: Session = Depends(get_db)):
    """
    LEGACY: Step 1 of the signup process: Create a new inactive user with basic information
    """
    # Check if email already exists
    db_user_email = db.query(User).filter(User.email == user_data.email).first()
    
    # If the email exists but the account was never verified (email_verified=False)
    # delete it to allow immediate reuse
    if db_user_email and not db_user_email.email_verified:
        logger.info(f"Found existing unverified account for email {user_data.email} created on {db_user_email.created_at}")
        
        # Use the helper function to properly delete the account and all its data
        delete_success = await delete_user_account(db, db_user_email)
        
        if not delete_success:
            # If deletion failed, raise an error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to prepare account for reuse. Please try again later."
            )
        
        # Set to None to allow creation of new account
        db_user_email = None
    
    # If the email exists and is verified, prevent reuse        
    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    password_validation = PasswordPolicy.validate_password_strength(user_data.password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_validation["message"]
        )
    
    # Generate username if not provided
    username = user_data.username or user_data.email.split('@')[0]
    
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
    
    # Create new user (inactive until step 3 is complete)
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        operation_name=user_data.operation_name,
        phone_number=user_data.phone_number,
        is_active=False,  # User is inactive until signup is complete
        email_verified=False  # Email not verified until OTP verification
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/signup/step2", response_model=UserSchema)
async def signup_step2(user_data: UserSignupStep2, db: Session = Depends(get_db)):
    """
    Step 2 of the signup process: Update user with state information
    """
    # Get user by ID
    user = db.query(User).filter(User.id == user_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user state
    user.state = user_data.state
    db.commit()
    db.refresh(user)
    
    return user

@router.post("/signup/step3")
async def signup_step3(user_data: UserSignupStep3, db: Session = Depends(get_db)):
    """
    Step 3 of the signup process: Select facility types, associate relevant documents, and send email verification OTP.
    User remains inactive until verified via /verify-signup-email.
    """
    user = None  # Initialize user to None
    try:
        print(f"Processing signup step 3 for user ID: {user_data.user_id}")
        print(f"Selected facility types: {user_data.selected_facility_types}")
        
        # Get user by ID
        user = db.query(User).filter(User.id == user_data.user_id).first()
        if not user:
            print(f"User with ID {user_data.user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_active:
             print(f"User {user_data.user_id} is already active.")
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail="User is already active."
             )

        if not user.state:
            print(f"User {user_data.user_id} has no state set")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User state must be set in step 2 before proceeding to step 3"
            )
        
        # Associate the selected facility types with user
        user.facility_type = ", ".join(user_data.selected_facility_types)
        print(f"Updated user facility_type to: {user.facility_type}")
        
        # --- Email OTP Generation and Sending ---
        try:
            # Generate OTP code
            otp_code = generate_otp()
            
            # Store hashed OTP record
            create_otp_record(db, user.id, user.email, OTPType.EMAIL, otp_code)
            
            # Send email (send_email_otp is synchronous)
            success, message = send_email_otp(user.email, otp_code)
            
            if not success:
                 # Log the specific error message from send_email_otp
                 logger.error(f"Failed to send email OTP during signup step 3 for user {user.id}: {message}")
                 db.rollback() # Rollback facility type change and OTP record
                 raise HTTPException(
                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                     detail=f"Failed to send verification email: {message}"
                 )

            print(f"Generated and sent email OTP for user {user.id}")
        except Exception as e:
            # Catch other potential errors (e.g., DB error in create_otp_record)
            db.rollback() # Rollback changes
            logger.error(f"Error during OTP process in signup step 3 for user {user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during the OTP process. Please try again later."
            )
        # --- End Email OTP ---

        # Activate user first - REMOVED, user stays inactive
        # user.is_active = True 
        db.commit() # Commit facility type update
        # db.refresh(user) # No need to refresh as user state didn't change fundamentally for next steps
        
        # print(f"User {user.id} successfully activated") # REMOVED
        print(f"User {user.id} facility type updated. Awaiting email verification.")
        
        # Try to associate user with relevant documents (DB only now) - Keep this
        try:
            await associate_user_documents(db, user.id, user.state, user_data.selected_facility_types)
            db.commit() # Commit the associations
            print(f"Associated DB documents for user {user.id}")
        except Exception as e:
            db.rollback() # Rollback association changes on error
            # Log the error but don't stop the signup process
            print(f"Error associating documents in DB but continuing: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
        
        # Initialize OpenAI resources (Assistant & Vector Store) after user activation - Keep this, even if inactive
        # These resources can be prepared while waiting for verification.
        try:
            logger.info(f"Initializing OpenAI resources for new user {user.id} (pending verification)")
            storage_path = settings.PDF_STORAGE_PATH
            
            # 1. Ensure Assistant exists (this also creates the vector store if needed)
            # Create assistant for new user (basic model for regular users)
            await create_user_assistant(user.id, db, openai_client, model_name='gpt-4.1-nano')
            db.refresh(user) # Refresh user to get updated assistant/vs IDs if created
            
            # 2. Synchronize vector store (now includes associated regulations)
            result = await update_vector_store(user.id, db, openai_client, storage_path)
            if not result["success"]:
                logger.warning(f"Errors occurred during vector store initialization/update: {result['errors']}")
            else:
                logger.info(f"Successfully initialized/updated vector store for user {user.id}: added {result['new_files_added']} files, removed {result['files_removed']} files")
            
            # 3. Configure the assistant model
            await configure_assistant_with_user_model(user.id, db, openai_client)
            logger.info(f"Configured assistant for user {user.id}")
            
        except Exception as e:
            # Log the error but don't stop the signup process
            logger.error(f"Error initializing OpenAI resources but continuing: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}") # Added traceback
        
        # Create and return access token - REMOVED
        # access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        # access_token = create_access_token(
        #     data={"sub": user.username},
        #     expires_delta=access_token_expires
        # )
        
        # print(f"Created access token for user {user.id}")
        # return {"access_token": access_token, "token_type": "bearer"}

        # Return pending verification status
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "signup_pending_email_verification", "user_id": user.id}
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as they contain specific error details
        raise
    except Exception as e:
        # For other exceptions, log and return a 500 error
        print(f"Unexpected error in signup_step3: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        # Rollback potential partial changes if user object was fetched
        if user:
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during signup: {str(e)}"
        )

@router.post("/verify-signup-email")
async def verify_signup_email(otp_data: OTPVerification, db: Session = Depends(get_db)):
    """
    Verify the email OTP provided during signup step 3.
    Activates the user and returns an access token upon successful verification.
    """
    user = db.query(User).filter(User.id == otp_data.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already active"
        )

    # Verify OTP (Note: verify_otp_util is synchronous)
    is_valid_otp, message = verify_otp_util(db, user.id, user.email, OTPType.EMAIL, otp_data.otp_code)

    if not is_valid_otp:
        logger.warning(f"Invalid signup OTP attempt for user {user.id}: {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message # Return the specific reason (Invalid, Expired, Too many attempts)
        )

    # Activate user and set email verified
    user.is_active = True
    user.email_verified = True # Assuming email verification implies OTP success
    user.last_login = datetime.utcnow() # Set initial last_login time
    db.commit()
    db.refresh(user)

    # Invalidate the used OTP (assuming verify_otp doesn't do this automatically)
    # If verify_otp handles invalidation, this can be removed.
    # await otp_service.invalidate_otp(db, user.id, otp_data.otp_code, OTPType.EMAIL) 

    logger.info(f"User {user.id} successfully verified email and activated.")

    # Create and return access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/facility-types", response_model=List[str])
async def get_facility_types(state: str, db: Session = Depends(get_db)):
    """
    Get available facility types for a given state
    """
    # Find regulations for the specified state
    query = (
        db.query(FacilityType.name)
        .join(FacilityType.regulations)
        .filter(Regulation.state_territory == state)
        .distinct()
    )
    
    facility_types = [ft[0] for ft in query.all()]
    
    return facility_types

@router.options("/facility-types")
async def options_facility_types():
    """
    Handle OPTIONS requests for the facility-types endpoint.
    This is needed for CORS preflight requests.
    """
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:5174",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, x-token",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(content={}, headers=headers)

async def associate_user_documents(db: Session, user_id: int, state: str, facility_types: List[str]):
    """
    Associates a user with relevant regulations based on state and facility types
    by creating UserDocument entries in the database.
    Does NOT interact with OpenAI directly anymore.
    """
    try:
        print(f"Starting DB document association for user {user_id}, state: {state}, facility types: {facility_types}")
        
        # Step 1: Delete existing UserDocument associations for this user
        # Wrap in a sub-transaction or handle potential errors carefully
        num_deleted = db.query(UserDocument).filter(UserDocument.user_id == user_id).delete()
        # Need to commit this deletion or handle it within the main transaction context
        # For simplicity, let's assume the caller (signup_step3) handles the commit/rollback
        # db.commit() # Avoid commit here, let caller manage transaction
        print(f"Deleted {num_deleted} existing document associations for user {user_id}.")
        
        # Step 2: Find matching regulations based on state and facility types
        regulations_query = (
            db.query(Regulation)
            .join(Regulation.facility_types) # Use the relationship attribute name
            .filter(Regulation.state_territory == state)
            .filter(FacilityType.name.in_(facility_types))
            .distinct() # Ensure we get unique regulations
        )
        matching_regulations = regulations_query.all()
        print(f"Found {len(matching_regulations)} matching regulations in DB for association.")
        
        # Step 3: Create new UserDocument associations
        new_associations = []
        for regulation in matching_regulations:
            print(f"Creating DB association for user {user_id} with regulation: id={regulation.id}, title={regulation.document_title}")
            new_association = UserDocument(
                user_id=user_id,
                regulation_id=regulation.id
                # document_id is for manually uploaded docs, leave as None here
            )
            new_associations.append(new_association)
        
        if new_associations:
            db.add_all(new_associations)
            # Again, let the caller handle the commit
            # db.commit()
            print(f"Added {len(new_associations)} new document associations to the session.")
        else:
            print("No new associations to add.")
        
    except Exception as e:
        # Log the error and re-raise to be caught by the caller
        print(f"Error during DB document association for user {user_id}: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise # Re-raise the exception

@router.post("/logout")
async def logout(
    token: str = Depends(get_token_from_request),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Logs the user out and blacklists the current token.
    Also cleans up OpenAI files.
    """
    try:
        # Blacklist the current token
        logger.info(f"Blacklisting token for user {current_user.id}")
        
        # Decode the token to get the payload
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # Add token to blacklist
            blacklist_token(db, payload, current_user.id)
            logger.info(f"Successfully blacklisted token with JTI: {payload.get('jti')}")
        except Exception as e:
            logger.error(f"Failed to blacklist token: {str(e)}")
            logger.error(traceback.format_exc())
            # Continue with logout even if blacklisting fails
    
        # Attempt to delete user's OpenAI files (documents and potentially regulation links)
        try:
            logger.info(f"Attempting to delete OpenAI files for user {current_user.id} during logout.")
            result = await delete_user_openai_files(current_user.id, db, openai_client, delete_all_resources=False)
            if not result["success"]:
                logger.error(f"Errors occurred during OpenAI file deletion for user {current_user.id}: {result['errors']}")
            else:
                logger.info(f"OpenAI file deletion process completed for user {current_user.id}. Files deleted: {result.get('files_deleted_from_openai', 0)}, Files removed from VS: {result.get('files_removed_from_vs', 0)}")
        except Exception as e:
            logger.error(f"Failed to delete OpenAI files for user {current_user.id} during logout: {str(e)}")
            # Log error but allow logout to succeed
    
        return {"message": "Logout successful"}
    except Exception as e:
        logger.error(f"Unexpected error during logout: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )

@router.post("/sync-openai-resources")
async def sync_openai_resources(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Synchronizes the OpenAI resources (assistants, files, vector store) for the authenticated user.
    This ensures the user's resources are up-to-date when a session is restored or after login.
    """
    try:
        logger.info(f"Starting manual sync of OpenAI resources for user {current_user.id}")
        storage_path = settings.PDF_STORAGE_PATH
        
        # 1. Ensure the assistant exists and is up-to-date
        # Get existing assistant ID (should already exist from registration)
        from app.core.openai_utils import get_user_assistant_id
        assistant_id = await get_user_assistant_id(current_user.id, db)
        
        if not assistant_id:
            # Fallback: create assistant if somehow missing
            model_name = 'gpt-4.1-mini' if current_user.subscription_status == 'pro' else 'gpt-4.1-nano'
            assistant_id = await create_user_assistant(current_user.id, db, openai_client, model_name=model_name)
        
        # 2. Synchronize the vector store with the latest documents
        sync_result = await update_vector_store(current_user.id, db, openai_client, storage_path)
        
        # 3. Configure the assistant with the appropriate model based on user subscription
        await configure_assistant_with_user_model(current_user.id, db, openai_client)
        
        if not sync_result["success"]:
            logger.warning(f"OpenAI resource sync completed with errors for user {current_user.id}: {sync_result['errors']}")
            return {
                "success": False,
                "message": "OpenAI resource synchronization completed with errors",
                "errors": sync_result["errors"],
                "assistant_id": assistant_id,
                "files_added": sync_result.get("new_files_added", 0),
                "files_removed": sync_result.get("files_removed", 0)
            }
        else:
            logger.info(f"OpenAI resource sync successful for user {current_user.id}. Assistant ID: {assistant_id}, Files added: {sync_result['new_files_added']}, Files removed: {sync_result['files_removed']}")
            return {
                "success": True,
                "message": "OpenAI resources synchronized successfully",
                "assistant_id": assistant_id,
                "files_added": sync_result["new_files_added"],
                "files_removed": sync_result["files_removed"]
            }
    except Exception as e:
        logger.error(f"Failed to synchronize OpenAI resources for user {current_user.id}: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": "Failed to synchronize OpenAI resources",
            "error": str(e)
        }

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Log in a user with email and password or via passkey.
    Triggers email OTP verification if login is via password and user is inactive (last_login > 7 days).
    """
    username = login_data.username
    password = login_data.password
    
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Both username and password are required"
        )

    user = db.query(User).filter(User.username == username).first()
    
    if not user or not user.verify_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
         # If user is inactive, they likely haven't verified signup OTP yet
         # Redirect them conceptually or return specific status
         # For now, just raise an error, but ideally return the signup verification required status
         # Or, resend the signup OTP?
         # Let's return the status consistent with Step 1
         if not user.email_verified: # Check if it's signup-related inactivity
             # Resend signup OTP might be helpful, but adds complexity. 
             # Let's stick to the defined flow for now.
             logger.warning(f"Inactive user login attempt (email not verified): {username}")
             # Return status indicating signup verification is needed
             # We can't return JSONResponse directly here due to response_model=Token
             # Modify endpoint definition to allow Union[Token, JSONResponse] or remove response_model
             # For now, raising an error to indicate the state.
             raise HTTPException(
                 status_code=status.HTTP_403_FORBIDDEN,
                 detail="Account not activated. Please verify your email first using the link sent during signup."
             )
         else:
             # User was active but became inactive? This shouldn't happen with current logic.
             logger.error(f"Login attempt by inactive but email-verified user: {username}")
             raise HTTPException(
                 status_code=status.HTTP_403_FORBIDDEN,
                 detail="Account is inactive. Please contact support."
             )

    # --- Check for inactivity (last_login > 7 days) ---
    needs_email_verification = False
    if user.last_login is None:
        needs_email_verification = True
        logger.info(f"User {user.username} logging in for the first time after activation. Triggering email OTP.")
    else:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        if user.last_login < seven_days_ago:
            needs_email_verification = True
            logger.info(f"User {user.username} inactive for >7 days. Triggering email OTP.")

    if needs_email_verification:
        # Generate, store, and send email OTP
        try:
            # Generate OTP code
            otp_code = generate_otp()
            
            # Store hashed OTP record
            create_otp_record(db, user.id, user.email, OTPType.EMAIL, otp_code)
            
            # Send email (send_email_otp is synchronous)
            success, message = send_email_otp(user.email, otp_code)
            
            if not success:
                 # Log specific error
                 logger.error(f"Failed to send login email OTP for user {user.id}: {message}")
                 # Don't block login completely, but return error
                 raise HTTPException(
                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                     detail=f"Failed to send verification email: {message}"
                 )

            logger.info(f"Generated and sent login email OTP for user {user.id}")
            # Return pending status
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED, # 202 Accepted
                content={"status": "login_pending_email_verification", "user_id": user.id}
            )
        except Exception as e:
            # Catch other potential errors
            logger.error(f"Error during login OTP process for user {user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred sending the login verification email. Please try again later."
            )
    else:
        # Update last login time for active users
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        logger.info(f"User {user.username} logged in successfully (active session). Updated last_login.")

        # Create and return access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

# --- NEW LOGIN VERIFICATION ENDPOINT ---

@router.post("/verify-login-email")
async def verify_login_email(otp_data: OTPVerification, db: Session = Depends(get_db)):
    """
    Verify the email OTP provided during login for an inactive user (> 7 days).
    Updates last_login and returns an access token upon successful verification.
    """
    user = db.query(User).filter(User.id == otp_data.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # This verification is only for already active users who were inactive
    if not user.is_active:
        logger.warning(f"Attempt to verify login email for inactive user {otp_data.user_id}")
        # If inactive and email not verified, they need signup verification
        if not user.email_verified:
             raise HTTPException(
                 status_code=status.HTTP_403_FORBIDDEN,
                 detail="Account not activated. Please verify your email using the link sent during signup."
             )
        # Otherwise, it's an unexpected state
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not active. Cannot verify login OTP."
        )

    # Verify OTP (Note: verify_otp_util is synchronous)
    is_valid_otp, message = verify_otp_util(db, user.id, user.email, OTPType.EMAIL, otp_data.otp_code)

    if not is_valid_otp:
        logger.warning(f"Invalid login OTP attempt for user {user.id}: {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message # Return specific reason
        )

    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    # Invalidate the used OTP (if needed)
    # await otp_service.invalidate_otp(db, user.id, otp_data.otp_code, OTPType.EMAIL)

    logger.info(f"User {user.id} successfully verified login email OTP. Updated last_login.")

    # Create and return access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# --- END NEW LOGIN VERIFICATION ENDPOINT ---

# Add OPTIONS handlers if missing for login/logout
@router.options("/login")
@router.options("/logout")
@router.options("/sync-openai-resources")
async def options_auth():
    """
    Handle OPTIONS requests for login/logout endpoints.
    """
    headers = {
        "Access-Control-Allow-Origin": settings.CLIENT_ORIGIN, # Use setting
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, x-token",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(content={}, headers=headers)

@router.post("/resend-signup-email")
async def resend_signup_email(data: dict, db: Session = Depends(get_db)):
    """
    Resend the verification email for an unverified user account.
    
    Input: {"user_id": int}
    Output: {"success": bool, "message": str}
    """
    user_id = data.get("user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is required"
        )
    
    # Find the user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if the account is already verified
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Check if the account is already active
    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already active"
        )
    
    # Generate and send a new OTP
    try:
        # Generate OTP code
        otp_code = generate_otp()
        
        # Store OTP record
        create_otp_record(db, user.id, user.email, OTPType.EMAIL, otp_code)
        
        # Send email
        success, message = send_email_otp(user.email, otp_code)
        
        if not success:
            logger.error(f"Failed to resend verification email for user {user.id}: {message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send verification email: {message}"
            )
        
        logger.info(f"Successfully resent verification email for user {user.id}")
        return {"success": True, "message": "Verification email resent successfully"}
    
    except Exception as e:
        logger.error(f"Error during OTP generation and sending: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resending the verification email"
        )

async def delete_user_account(db: Session, user: User):
    """
    Delete a user account and all associated data.
    
    Args:
        db: Database session
        user: User object to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import necessary models for deletion
        from app.models.user_document import UserDocument
        from app.models.thread_map import ThreadMap
        from app.models.export_quota import ExportQuota
        from app.models.export_request import ExportRequest
        from app.models.user_otp import UserOTP
        from app.models.magic_link import MagicLink
        from app.models.oauth_identity import OAuthIdentity
        from app.models.webauthn_credential import WebAuthnCredential
        from app.models.staff_member import StaffMember
        from app.models.training_assignment import TrainingAssignment
        from app.models.training_material import TrainingMaterial
        
        user_id = user.id
        
        # Delete records that don't have cascade delete configured
        db.query(UserDocument).filter(UserDocument.user_id == user_id).delete()
        db.query(ThreadMap).filter(ThreadMap.user_id == user_id).delete()
        db.query(ExportQuota).filter(ExportQuota.user_id == user_id).delete()
        db.query(ExportRequest).filter(ExportRequest.user_id == user_id).delete()
        db.query(BlacklistedToken).filter(BlacklistedToken.user_id == user_id).delete()
        db.query(UserOTP).filter(UserOTP.user_id == user_id).delete()
        db.query(MagicLink).filter(MagicLink.user_id == user_id).delete()
        db.query(OAuthIdentity).filter(OAuthIdentity.user_id == user_id).delete()
        db.query(WebAuthnCredential).filter(WebAuthnCredential.user_id == user_id).delete()
        
        # Delete training-related records where user is referenced
        db.query(StaffMember).filter(StaffMember.facility_administrator_id == user_id).delete()
        db.query(TrainingAssignment).filter(TrainingAssignment.assigned_by_admin_id == user_id).delete()
        db.query(TrainingMaterial).filter(TrainingMaterial.created_by == user_id).delete()
        
        # Fix any notifications with invalid priority values before deletion
        from app.models.notification import Notification, NotificationPriority
        notifications = db.query(Notification).filter(Notification.user_id == user_id).all()
        for notification in notifications:
            if hasattr(notification.priority, 'value'):
                # Already an enum, skip
                continue
            elif isinstance(notification.priority, str):
                # Convert string to enum
                if notification.priority.lower() == 'low':
                    notification.priority = NotificationPriority.LOW
                elif notification.priority.lower() == 'medium':
                    notification.priority = NotificationPriority.MEDIUM
                elif notification.priority.lower() == 'high':
                    notification.priority = NotificationPriority.HIGH
                else:
                    # Default to MEDIUM for unknown values
                    notification.priority = NotificationPriority.MEDIUM
        
        # Delete query logs
        try:
            from app.models.query_log import QueryLog
            db.query(QueryLog).filter(QueryLog.user_id == user_id).delete()
        except Exception as e:
            logger.warning(f"Error deleting query logs for user {user_id}: {str(e)}")
        
        # Handle documents - hard delete them when user is deleted to avoid foreign key constraints
        from app.models.document import Document
        db.query(Document).filter(Document.uploaded_by == user_id).delete(synchronize_session=False)
        
        # Handle facility administration - delete all facility users when admin is deleted
        if hasattr(user, 'administered_facility') and user.administered_facility:
            facility_id = user.administered_facility.id
            
            # Get all other users in the facility for deletion
            facility_users = db.execute(text("SELECT id FROM users WHERE facility_id = :facility_id AND id != :user_id"), 
                                      {"facility_id": facility_id, "user_id": user_id}).fetchall()
            
            facility_user_ids = [row[0] for row in facility_users]
            logger.info(f"Found {len(facility_user_ids)} facility users to delete along with admin {user_id}")
            
            # Delete all facility users first (excluding the admin who will be deleted separately)
            for facility_user_id in facility_user_ids:
                try:
                    # Export data for each facility user before deletion
                    facility_user = db.query(User).filter(User.id == facility_user_id).first()
                    if facility_user:
                        try:
                            from app.utils.user_data_export import export_deleted_user_data
                            export_path = export_deleted_user_data(facility_user, db)
                            logger.info(f"Exported deleted facility user data to {export_path}")
                        except Exception as export_err:
                            logger.error(f"Failed to export deleted facility user data for user {facility_user_id}: {export_err}")
                        
                        # Clean up OpenAI resources for facility user
                        try:
                            cleanup_result = await delete_user_openai_files(facility_user_id, db, openai_client)
                            if not cleanup_result["success"]:
                                logger.error(f"OpenAI resource cleanup failed for facility user {facility_user_id}: {cleanup_result['errors']}")
                            else:
                                logger.info(f"OpenAI resource cleanup successful for facility user {facility_user_id}")
                        except Exception as openai_err:
                            logger.error(f"Error during OpenAI cleanup for facility user {facility_user_id}: {openai_err}")
                    
                    # Delete all related records for this facility user
                    db.execute(text("DELETE FROM user_documents WHERE user_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM thread_maps WHERE user_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM export_quotas WHERE user_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM export_requests WHERE user_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM blacklisted_tokens WHERE user_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM user_otps WHERE user_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM magic_links WHERE user_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM oauth_identities WHERE user_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM webauthn_credentials WHERE user_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM staff_members WHERE facility_administrator_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM training_assignments WHERE assigned_by_admin_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM training_materials WHERE created_by = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM notifications WHERE user_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM query_logs WHERE user_id = :user_id"), {"user_id": facility_user_id})
                    db.execute(text("DELETE FROM documents WHERE uploaded_by = :user_id"), {"user_id": facility_user_id})
                    
                    # Finally delete the facility user
                    db.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": facility_user_id})
                    logger.info(f"Successfully deleted facility user {facility_user_id}")
                    
                except Exception as facility_user_error:
                    logger.error(f"Error deleting facility user {facility_user_id}: {str(facility_user_error)}")
                    # Continue with other users even if one fails
            
            # Delete the facility using raw SQL to bypass relationship constraints
            db.execute(text("DELETE FROM facilities WHERE id = :facility_id"), {"facility_id": facility_id})
            logger.info(f"Deleted facility {facility_id} and {len(facility_user_ids)} facility users due to admin deletion")
        
        # Finally, delete the user using raw SQL to ensure no relationship issues
        db.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
        db.commit()
        logger.info(f"Successfully deleted user {user_id} ({user.email})")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting user account {user_id}: {str(e)}")
        db.rollback()
        
        # If deletion fails due to foreign key constraints, try a more aggressive approach
        if "constraint failed" in str(e).lower() or "foreign key" in str(e).lower():
            logger.warning(f"Foreign key constraint detected during user {user_id} deletion. Attempting aggressive cleanup.")
            try:
                # Use raw SQL to force delete any remaining references
                db.execute(text("PRAGMA foreign_keys = OFF"))  # SQLite specific
                db.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
                db.execute(text("PRAGMA foreign_keys = ON"))   # Re-enable foreign keys
                db.commit()
                logger.info(f"Successfully deleted user {user_id} using aggressive cleanup")
                return True
            except Exception as fallback_error:
                db.rollback()
                logger.error(f"Aggressive cleanup also failed for user {user_id}: {str(fallback_error)}")
        
        return False 