"""
Signup Session Service Module

This module provides service methods for managing temporary signup sessions
before user account creation and email verification.

Key functionalities:
- Session creation and token generation
- Session data retrieval and validation
- Session updates and progress tracking
- Automatic cleanup of expired sessions
- Rate limiting and abuse prevention

Educational Note: Implements service layer pattern for session management,
following separation of concerns and single responsibility principles.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.orm.attributes import flag_modified

from app.models.signup_session import SignupSession
from app.models.user import User
from app.auth.utils import get_password_hash

logger = logging.getLogger(__name__)

class SignupSessionService:
    """Service for managing signup sessions"""
    
    # Configuration constants
    DEFAULT_SESSION_HOURS = 24
    MAX_SESSIONS_PER_EMAIL = 3
    MAX_VERIFICATION_ATTEMPTS = 5
    
    @staticmethod
    def create_session(
        db: Session,
        email: str,
        password: str,
        full_name: str,
        operation_name: str,
        phone_number: Optional[str] = None
    ) -> Optional[SignupSession]:
        """
        Create a new signup session with step 1 data
        
        Args:
            db: Database session
            email: User email
            password: Plain text password (will be hashed)
            full_name: User's full name
            operation_name: Operation name
            phone_number: Optional phone number
            
        Returns:
            SignupSession object or None if creation failed
        """
        try:
            # Check if email already exists in verified users
            existing_user = db.query(User).filter(
                and_(User.email == email, User.email_verified == True)
            ).first()
            
            if existing_user:
                logger.warning(f"Attempt to create session for verified email: {email}")
                return None
            
            # Clean up existing sessions for this email
            SignupSessionService._cleanup_email_sessions(db, email)
            
            # Check session rate limiting
            recent_sessions = db.query(SignupSession).filter(
                and_(
                    SignupSession.email == email,
                    SignupSession.created_at > datetime.now(timezone.utc) - timedelta(hours=1)
                )
            ).count()
            
            if recent_sessions >= SignupSessionService.MAX_SESSIONS_PER_EMAIL:
                logger.warning(f"Rate limit exceeded for email: {email}")
                return None
            
            # Generate session token
            session_token = SignupSession.generate_session_token()
            
            # Hash password
            hashed_password = get_password_hash(password)
            
            # Prepare session data
            signup_data = {
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "operation_name": operation_name,
                "phone_number": phone_number
            }
            
            # Create session
            session = SignupSession(
                session_token=session_token,
                email=email,
                signup_data=signup_data,
                step_completed=10,  # Step 1 = 10 (using integers to allow intermediate steps like 15, 18)
                expires_at=datetime.now(timezone.utc) + timedelta(hours=SignupSessionService.DEFAULT_SESSION_HOURS)
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            logger.info(f"Created signup session for email: {email}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating signup session: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    def get_session(db: Session, session_token: str) -> Optional[SignupSession]:
        """
        Retrieve and validate a signup session
        
        Args:
            db: Database session
            session_token: Session token
            
        Returns:
            SignupSession object or None if not found/expired
        """
        try:
            session = db.query(SignupSession).filter(
                SignupSession.session_token == session_token
            ).first()
            
            if not session:
                return None
            
            if session.is_expired():
                pass  # Sensitive authentication data must not be logged.
                db.delete(session)
                db.commit()
                return None
            
            # Update last activity
            session.last_activity = datetime.now(timezone.utc)
            db.commit()
            
            return session
            
        except Exception as e:
            logger.error(f"Error retrieving session: {str(e)}")
            return None
    
    @staticmethod
    def update_session_step2(
        db: Session,
        session_token: str,
        state: str
    ) -> Optional[SignupSession]:
        """
        Update session with step 2 data (state selection)
        
        Args:
            db: Database session
            session_token: Session token
            state: Selected state
            
        Returns:
            Updated SignupSession or None if failed
        """
        try:
            session = SignupSessionService.get_session(db, session_token)
            if not session:
                return None
            
            # Update signup data - create a new dict to ensure SQLAlchemy detects the change
            updated_data = session.signup_data.copy()
            updated_data["state"] = state
            session.signup_data = updated_data
            
            # Mark the JSON field as modified so SQLAlchemy knows to update it
            flag_modified(session, "signup_data")
            
            session.step_completed = 20  # Step 2 = 20
            session.extend_session()
            
            db.commit()
            db.refresh(session)
            
            pass  # Sensitive authentication data must not be logged.
            return session
            
        except Exception as e:
            logger.error(f"Error updating session step 2: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    def update_session_step3(
        db: Session,
        session_token: str,
        facility_types: list
    ) -> Optional[SignupSession]:
        """
        Update session with step 3 data (facility types)
        
        Args:
            db: Database session
            session_token: Session token
            facility_types: Selected facility types
            
        Returns:
            Updated SignupSession or None if failed
        """
        try:
            session = SignupSessionService.get_session(db, session_token)
            if not session:
                return None
            
            # Update signup data - create a new dict to ensure SQLAlchemy detects the change
            updated_data = session.signup_data.copy()
            updated_data["facility_types"] = facility_types
            session.signup_data = updated_data
            
            # Mark the JSON field as modified so SQLAlchemy knows to update it
            flag_modified(session, "signup_data")
            
            session.step_completed = 30  # Step 3 = 30
            session.email_verification_sent = True
            session.extend_session()
            
            db.commit()
            db.refresh(session)
            
            pass  # Sensitive authentication data must not be logged.
            return session
            
        except Exception as e:
            logger.error(f"Error updating session step 3: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    def update_session_step3_facility_admin(
        db: Session,
        session_token: str,
        facility_data: Dict[str, Any]
    ) -> Optional[SignupSession]:
        """
        Update session with step 3 data for facility administrators (facility creation)
        
        Args:
            db: Database session
            session_token: Session token
            facility_data: Dictionary containing facility information
            
        Returns:
            Updated SignupSession or None if failed
        """
        try:
            session = SignupSessionService.get_session(db, session_token)
            if not session:
                return None
            
            if session.step_completed < 20:
                pass  # Sensitive authentication data must not be logged.
                return None
            
            # Verify this is a facility admin session
            if session.signup_data.get("user_role") != "facility_admin":
                pass  # Sensitive authentication data must not be logged.
                return None
            
            # Update signup data with facility information
            updated_data = session.signup_data.copy()
            updated_data["facility_data"] = facility_data
            session.signup_data = updated_data
            
            # Mark the JSON field as modified
            flag_modified(session, "signup_data")
            
            session.step_completed = 30  # Step 3 = 30
            session.extend_session()
            
            db.commit()
            db.refresh(session)
            
            pass  # Sensitive authentication data must not be logged.
            return session
            
        except Exception as e:
            logger.error(f"Error updating session step 3 (facility admin): {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    def increment_verification_attempts(db: Session, session_token: str) -> bool:
        """
        Increment verification attempts for a session
        
        Args:
            db: Database session
            session_token: Session token
            
        Returns:
            True if successful, False if max attempts reached
        """
        try:
            session = SignupSessionService.get_session(db, session_token)
            if not session:
                return False
            
            session.verification_attempts += 1
            
            if session.verification_attempts >= SignupSessionService.MAX_VERIFICATION_ATTEMPTS:
                pass  # Sensitive authentication data must not be logged.
                db.delete(session)
                db.commit()
                return False
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing verification attempts: {str(e)}")
            return False
    
    @staticmethod
    def cleanup_expired_sessions(db: Session) -> int:
        """
        Clean up expired signup sessions
        
        Args:
            db: Database session
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            expired_sessions = db.query(SignupSession).filter(
                SignupSession.expires_at < datetime.now(timezone.utc)
            ).all()
            
            count = len(expired_sessions)
            
            for session in expired_sessions:
                db.delete(session)
            
            db.commit()
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired signup sessions")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            db.rollback()
            return 0
    
    @staticmethod
    def _cleanup_email_sessions(db: Session, email: str) -> None:
        """
        Clean up existing sessions for an email address
        
        Args:
            db: Database session
            email: Email address
        """
        try:
            existing_sessions = db.query(SignupSession).filter(
                SignupSession.email == email
            ).all()
            
            for session in existing_sessions:
                db.delete(session)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning up email sessions: {str(e)}")
            db.rollback()
    
    @staticmethod
    def delete_session(db: Session, session_token: str) -> bool:
        """
        Delete a specific signup session
        
        Args:
            db: Database session
            session_token: Session token
            
        Returns:
            True if deleted successfully
        """
        try:
            session = db.query(SignupSession).filter(
                SignupSession.session_token == session_token
            ).first()
            
            if session:
                db.delete(session)
                db.commit()
                pass  # Sensitive authentication data must not be logged.
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def update_session_step1point5(
        db: Session,
        session_token: str,
        user_role: str
    ) -> Optional[SignupSession]:
        """
        Update session with step 1.5 data (role selection)
        
        Args:
            db: Database session
            session_token: Session token
            user_role: Selected user role ('facility_admin' or 'regular_user')
            
        Returns:
            Updated SignupSession or None if failed
        """
        try:
            session = SignupSessionService.get_session(db, session_token)
            if not session:
                return None
            
            if session.step_completed < 10:
                pass  # Sensitive authentication data must not be logged.
                return None
            
            # Validate user role
            if user_role not in ['facility_admin', 'regular_user']:
                logger.warning(f"Invalid user role: {user_role}")
                return None
            
            # Update signup data
            updated_data = session.signup_data.copy()
            updated_data["user_role"] = user_role
            session.signup_data = updated_data
            
            # Mark the JSON field as modified
            flag_modified(session, "signup_data")
            
            session.step_completed = 15  # Step 1.5 = 15
            session.extend_session()
            
            db.commit()
            db.refresh(session)
            
            pass  # Sensitive authentication data must not be logged.
            return session
            
        except Exception as e:
            logger.error(f"Error updating session step 1.5: {str(e)}")
            db.rollback()
            return None

    @staticmethod
    def update_session_step1point75(
        db: Session,
        session_token: str,
        selected_tier: str
    ) -> Optional[SignupSession]:
        """
        Update session with step 1.75 data (tier selection)
        
        Args:
            db: Database session
            session_token: Session token
            selected_tier: Selected subscription tier ('free' or 'pro')
            
        Returns:
            Updated SignupSession or None if failed
        """
        try:
            session = SignupSessionService.get_session(db, session_token)
            if not session:
                return None
            
            if session.step_completed < 15:
                pass  # Sensitive authentication data must not be logged.
                return None
            
            # Validate tier selection
            if selected_tier not in ['free', 'pro']:
                logger.warning(f"Invalid tier selection: {selected_tier}")
                return None
            
            # Update signup data
            updated_data = session.signup_data.copy()
            updated_data["selected_tier"] = selected_tier
            session.signup_data = updated_data
            
            # Mark the JSON field as modified
            flag_modified(session, "signup_data")
            
            session.step_completed = 18  # Step 1.75 = 18
            session.extend_session()
            
            db.commit()
            db.refresh(session)
            
            pass  # Sensitive authentication data must not be logged.
            return session
            
        except Exception as e:
            logger.error(f"Error updating session step 1.75: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    def update_session_invitation(
        db: Session,
        session_token: str,
        invitation_code: str
    ) -> Optional[SignupSession]:
        """
        Update session with invitation code for invited user signup
        
        Args:
            db: Database session
            session_token: Session token
            invitation_code: Facility invitation code
            
        Returns:
            Updated SignupSession or None if failed
        """
        try:
            pass  # Sensitive authentication data must not be logged.
            session = SignupSessionService.get_session(db, session_token)
            if not session:
                pass  # Sensitive authentication data must not be logged.
                return None
            
            # Validate invitation exists and is active
            from app.models.facility_invitation import FacilityInvitation
            invitation = db.query(FacilityInvitation).filter(
                FacilityInvitation.invitation_code == invitation_code,
                FacilityInvitation.status == 'pending'
            ).first()
            
            if not invitation:
                pass  # Sensitive authentication data must not be logged.
                return None
                
            # For invited users, we don't require step 2 completion
            # They inherit facility admin's state and settings
            # Store invitation_code in signup_data JSON field
            updated_data = session.signup_data.copy()
            updated_data["invitation_code"] = invitation_code
            session.signup_data = updated_data
            
            session.step_completed = 30  # Mark as ready for completion (Step 3 = 30)
            
            # Mark the JSON field as modified so SQLAlchemy knows to update it
            flag_modified(session, "signup_data")
            db.commit()
            db.refresh(session)
            
            pass  # Sensitive authentication data must not be logged.
            return session
            
        except Exception as e:
            logger.error(f"Error updating session invitation: {str(e)}")
            db.rollback()
            return None 