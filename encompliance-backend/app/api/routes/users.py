"""
User Management Routes
--------------------
This module defines the user management API endpoints for the EnCompliance system.
It provides:
- User CRUD operations
- Profile management
- Role and permission management
- User preferences
- Account settings
- User activity tracking
- Quick access links management for dashboard customization
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.user_document import UserDocument
from app.models.regulation import Regulation
from app.schemas.user import User as UserSchema, UserUpdate, QuickAccessLink
from app.schemas.user_document import UserDocumentsResponse
from app.schemas.regulation import Regulation as RegulationSchema
from app.auth.dependencies import get_current_active_user, get_current_user
import logging
from sqlalchemy import func
from app.models.query_log import QueryLog
from app.models.document import Document
from app.core.security_utils import encrypt_settings, decrypt_settings
from app.schemas.settings import UserLLMSettings
from pydantic import BaseModel
import json
import asyncio
import traceback
from app.api.routes.auth import associate_user_documents
from app.utils.user_data_export import export_deleted_user_data
from app.utils.owasp_protections import PasswordPolicy

# Import necessary OpenAI utilities and config
from openai import AsyncOpenAI
from app.core.openai_utils import update_vector_store, delete_user_openai_files
from app.core.config import get_settings
from app.api.routes.documents import get_storage_path # Import storage path function
from app.services.admin_sync_service import AdminSyncService

# Set up logging
logger = logging.getLogger(__name__)

# Initialize settings and OpenAI client
settings = get_settings()
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Define UserLLMSettings schema if it doesn't exist
# (Alternatively, create app/schemas/settings.py)
class UserLLMSettings(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    # Add other relevant settings like model name, temperature etc.
    # Add local settings too, like localModelUrl
    localModelUrl: Optional[str] = None 
    otherApiUrl: Optional[str] = None # For provider='other'

router = APIRouter(tags=["Users"])

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get information about the currently authenticated user.
    """
    return current_user

@router.options("/me")
async def options_me():
    """
    Handle OPTIONS requests for the /me endpoint.
    """
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:5174",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, x-token",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(content={}, headers=headers)

@router.get("/user-info")
async def get_user_info(
    request: Request,
    token: Optional[str] = Header(None, alias="x-token"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Alternative endpoint for getting user info with explicit CORS handling.
    """
    pass  # Sensitive authentication data must not be logged.
    
    # Extract token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5174",
                "Access-Control-Allow-Credentials": "true"
            }
        )
    
    try:
        # Get user using the dependency
        user = await get_current_user(token=token, db=db)
        
        # Create a serializable user dict
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "operation_name": user.operation_name,
            "facility_type": user.facility_type,
            "state": user.state,
            "phone_number": user.phone_number,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "subscription_status": "team_member" if user.user_role.value == "team_member" else (user.subscription_status or "free"),
            "subscription_end_date": getattr(user, "subscription_end_date", None),
            "user_role": user.user_role.value if user.user_role else "FREE_USER",
            "role_description": getattr(user, "role_description", None),
        }
        
        # Create response with CORS headers
        response = JSONResponse(
            content=user_dict,
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5174",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Authorization, Content-Type, x-token",
                "Access-Control-Allow-Credentials": "true",
            }
        )
        return response
    except Exception as e:
        logger.error(f"Error in user-info endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5174",
                "Access-Control-Allow-Credentials": "true"
            }
        )

@router.options("/user-info")
async def options_user_info():
    """
    Handle OPTIONS requests for the /user-info endpoint.
    """
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:5174",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, x-token",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(content={}, headers=headers)

@router.get("/auth-debug")
async def auth_debug(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Debug endpoint to check authentication headers.
    """
    headers = {k: v for k, v in request.headers.items()}
    return {
        "headers": headers,
        "authorization": authorization,
        "message": "This endpoint helps debug authentication issues."
    }

@router.get("/token-test")
async def token_test(
    request: Request,
    authorization: Optional[str] = Header(None),
    token_info: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Test endpoint to check token parsing.
    """
    headers = {k: v for k, v in request.headers.items()}
    return {
        "headers": headers,
        "authorization": authorization,
        "token_info": "Valid token" if token_info else "Invalid token", 
        "user": token_info,
        "message": "This endpoint helps debug token issues."
    }

@router.put("/me", response_model=UserSchema)
async def update_current_user(
    user_update: UserUpdate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's information.
    """
    logger.info(f"--- Starting update_current_user for user {current_user.id} ---")
    logger.debug(f"Incoming user_update data: {user_update.dict()}") # Log incoming data
    
    # Store original values to check for changes
    original_state = current_user.state
    original_facility_type = current_user.facility_type # Assuming this exists
    needs_document_update = False
    
    # Update user fields from the request
    update_data = user_update.dict(exclude_unset=True)
    logger.debug(f"Data to update (exclude_unset=True): {update_data}")
    
    for key, value in update_data.items():
        current_value = getattr(current_user, key, None)
        logger.debug(f"Checking field '{key}': Current='{current_value}', New='{value}'")
        if current_value != value:
            logger.info(f"Field '{key}' changed for user {current_user.id}")
            if key in ['state', 'facility_type']:
                logger.info(f"Change detected in '{key}', setting needs_document_update=True")
                needs_document_update = True
            setattr(current_user, key, value)
    
    # Save user profile changes first
    if update_data: # Only commit if there were changes
        logger.info(f"Committing profile updates for user {current_user.id}")
        db.commit()
        db.refresh(current_user) # Refresh after commit
        logger.info(f"Profile updates committed and user object refreshed for user {current_user.id}")
    else:
        logger.info(f"No fields changed in the request for user {current_user.id}. Skipping commit.")

    # Log the flag status before the check
    logger.info(f"Checking document update condition: needs_document_update={needs_document_update}, current_user.state='{current_user.state}'")
    
    # If state or facility type changed, update document associations
    if needs_document_update and current_user.state:
        try:
            logger.info(f"State or facility type changed for user {current_user.id}. Triggering document association function.")
            
            # Deletion logic is now handled within associate_user_documents
            # # Step 1: Delete existing UserDocument associations for this user
            # num_deleted = db.query(UserDocument).filter(UserDocument.user_id == current_user.id).delete()
            # db.commit() # Commit the deletion
            # logger.info(f"Deleted {num_deleted} existing document associations for user {current_user.id}.")

            # Step 2 (now Step 1 in call): Associate new documents based on the updated state and facility type
            new_facility_types = []
            if current_user.facility_type:
                new_facility_types = [ft.strip() for ft in current_user.facility_type.split(',') if ft.strip()]
            
            await associate_user_documents(db, current_user.id, current_user.state, new_facility_types)
            logger.info(f"Document association call completed for user {current_user.id}.")
            
            # Commit the changes made by associate_user_documents
            db.commit()
            logger.info(f"Committed document association changes for user {current_user.id}.")
            # Refresh user object again after association changes
            db.refresh(current_user)

        except Exception as e:
            # Don't rollback here, as profile changes were already committed.
            # The associate function handles its own rollback on error.
            logger.error(f"Error calling document association update for user {current_user.id}: {str(e)}", exc_info=True)
            # Log the error but don't block the response / re-raise
    
    # Refresh the user object to reflect potential changes
    db.refresh(current_user)

    # If document associations were updated, trigger OpenAI sync
    if needs_document_update:
        try:
            logger.info(f"Triggering OpenAI vector store update for user {current_user.id} after profile change.")
            storage_path = get_storage_path()
            sync_result = await update_vector_store(
                user_id=current_user.id,
                db=db,
                openai_client=openai_client,
                storage_path=storage_path
            )
            if sync_result.get("success"):
                logger.info(f"OpenAI vector store update successful for user {current_user.id}. Details: {sync_result}")
            else:
                logger.error(f"OpenAI vector store update failed for user {current_user.id}. Errors: {sync_result.get('errors')}")
                # Log the error, but don't fail the entire profile update
        except Exception as e:
            logger.error(f"Error calling update_vector_store for user {current_user.id} after profile update: {str(e)}", exc_info=True)
            # Log the error, but don't fail the entire profile update
    
    # Trigger account sync if facility admin updated their info (affects team members)
    if current_user.is_facility_admin and current_user.facility_id and needs_document_update:
        try:
            admin_sync_service = AdminSyncService(db)
            await admin_sync_service.trigger_account_sync(current_user.facility_id, current_user.id)
            logger.info(f"Triggered account sync for facility {current_user.facility_id} after admin profile update")
        except Exception as sync_error:
            logger.error(f"Failed to trigger account sync after admin profile update: {sync_error}")

    logger.info(f"--- Finished update_current_user for user {current_user.id} ---")
    return current_user

@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_update: dict = Body(..., example={"current_password": "oldpassword", "new_password": "newpassword"}),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change the current user's password.
    
    Requires current password for verification and new password.
    """
    logger.info(f"--- Starting change_password for user {current_user.id} ---")
    
    # Validate required fields
    if "current_password" not in password_update or "new_password" not in password_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both current_password and new_password must be provided"
        )
    
    # Verify current password
    from app.auth.utils import verify_password, get_password_hash
    
    if not verify_password(password_update["current_password"], current_user.hashed_password):
        logger.warning(f"Invalid current password provided for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate password strength
    password_validation = PasswordPolicy.validate_password_strength(password_update["new_password"])
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_validation["message"]
        )
    
    # Hash and set new password
    new_password_hash = get_password_hash(password_update["new_password"])
    current_user.hashed_password = new_password_hash
    
    # Save to database
    db.commit()
    
    logger.info(f"Password successfully changed for user {current_user.id}")
    return

@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete the current user's profile and all associated data.
    """
    try:
        # Export data before deletion
        try:
            export_path = export_deleted_user_data(current_user, db)
            logger.info(f"Exported deleted user data to {export_path}")
        except Exception as export_err:
            logger.error(f"Failed to export deleted user data: {export_err}")

        # Call the OpenAI resource cleanup function
        logger.info(f"Attempting OpenAI resource cleanup for user {current_user.id} during account deletion.")
        cleanup_result = await delete_user_openai_files(current_user.id, db, openai_client)
        if not cleanup_result["success"]:
            logger.error(f"OpenAI resource cleanup failed for user {current_user.id}: {cleanup_result['errors']}")
            # Continue with deletion even if OpenAI cleanup fails
        else:
            logger.info(f"OpenAI resource cleanup successful for user {current_user.id}.")

        user_id = current_user.id
        
        # Import necessary models for deletion
        from app.models.user_document import UserDocument
        from app.models.thread_map import ThreadMap
        from app.models.export_quota import ExportQuota
        from app.models.export_request import ExportRequest
        from app.models.token import BlacklistedToken
        from app.models.user_otp import UserOTP
        from app.models.magic_link import MagicLink
        from app.models.oauth_identity import OAuthIdentity
        from app.models.webauthn_credential import WebAuthnCredential
        from app.models.staff_member import StaffMember
        from app.models.training_assignment import TrainingAssignment
        from app.models.training_material import TrainingMaterial
        
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
        db.query(QueryLog).filter(QueryLog.user_id == user_id).delete()
        
        # Handle documents - hard delete them when user is deleted to avoid foreign key constraints
        from app.models.document import Document
        db.query(Document).filter(Document.uploaded_by == user_id).delete(synchronize_session=False)
        
        # Handle facility administration - delete all facility users when admin is deleted
        if current_user.administered_facility:
            facility_id = current_user.administered_facility.id
            
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
        
        logger.info(f"Successfully deleted user {user_id} and all associated data")
        return {"message": "User profile and all associated data deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {str(e)}")
        
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
                return {"message": "User profile and all associated data deleted successfully"}
            except Exception as fallback_error:
                db.rollback()
                logger.error(f"Aggressive cleanup also failed for user {user_id}: {str(fallback_error)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the user profile. Contact support if this persists."
        )

@router.put("/me/settings", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_llm_settings(
    settings_data: UserLLMSettings,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the LLM settings for the currently authenticated user.
    API key is masked in the response.
    """
    try:
        # Store settings directly without encryption
        settings_dict = settings_data.dict(exclude_unset=True)
        
        # Store the settings as JSON in the user's encrypted_settings field
        # Even though we're not encrypting, we'll use the same field for compatibility
        current_user.encrypted_settings = json.dumps(settings_dict).encode()
        
        db.commit()
        logger.info(f"User {current_user.id} settings updated successfully")
        return
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )

@router.get("/me/settings", response_model=UserLLMSettings)
async def get_user_llm_settings(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the LLM settings for the currently authenticated user.
    API keys are masked in the response.
    """
    try:
        # If settings exist, parse them from JSON
        if current_user.encrypted_settings:
            try:
                settings_dict = json.loads(current_user.encrypted_settings.decode())
            except Exception:
                logger.warning(f"Could not parse settings for user {current_user.id}")
                settings_dict = {}
        else:
            settings_dict = {}
        
        # Mask the API key before returning
        if settings_dict.get('api_key'):
            settings_dict['api_key'] = "********" 
            
        # Create the response object with default values for missing fields
        response = UserLLMSettings(
            provider=settings_dict.get('provider', 'auto'),
            api_key=settings_dict.get('api_key', ''),
            localModelUrl=settings_dict.get('localModelUrl', 'http://127.0.0.1:1234/v1'),
            otherApiUrl=settings_dict.get('otherApiUrl', '')
        )
        
        return response
    except Exception as e:
        logger.error(f"Error retrieving user settings: {str(e)}")
        # Return default empty settings on error
        return UserLLMSettings()

@router.get("/me/documents", response_model=UserDocumentsResponse)
async def get_user_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all documents associated with the current user
    """
    # Get user documents with regulation information
    user_docs_with_regulations = (
        db.query(Regulation)
        .join(UserDocument, UserDocument.regulation_id == Regulation.id)
        .filter(UserDocument.user_id == current_user.id)
        .all()
    )
    
    return {"documents": user_docs_with_regulations}

@router.get("/me/quick-access-links", response_model=List[QuickAccessLink])
async def get_quick_access_links(current_user: User = Depends(get_current_active_user)):
    """
    Get the current user's quick access links for dashboard customization.
    If no links are configured, returns an empty list.
    """
    if not current_user.quick_access_links:
        return []
    return current_user.quick_access_links

@router.put("/me/quick-access-links", response_model=List[QuickAccessLink])
async def update_quick_access_links(
    links: List[QuickAccessLink],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's quick access links.
    Replaces the existing links with the provided list.
    Returns the updated list of links.
    """
    # Validate maximum number of links (prevent abuse)
    if len(links) > 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 8 quick access links allowed"
        )
    
    # Update the user's links
    current_user.quick_access_links = [link.dict() for link in links]
    db.commit()
    db.refresh(current_user)
    
    return current_user.quick_access_links 
