"""
WebAuthn API Routes Module
---------------------
This module provides endpoints for WebAuthn (passkey) operations in the EnCompliance system.
It enables:
- Passkey registration flow
- Passkey authentication flow
- Credential management
- User verification
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import timedelta, datetime
import json

from app.database import get_db
from app.models.user import User
from app.models.webauthn_credential import WebAuthnCredential
from app.auth.dependencies import get_current_user
from app.auth.utils import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.webauthn_utils import WebAuthnManager
from app.schemas.webauthn import (
    RegistrationOptions, 
    RegistrationOptionsResponse,
    RegistrationVerification,
    CredentialResponse,
    AuthenticationOptions,
    AuthenticationOptionsResponse,
    AuthenticationVerification,
    CredentialSummary
)

router = APIRouter(prefix="/webauthn", tags=["webauthn"])

@router.post("/register/options", response_model=RegistrationOptionsResponse)
async def webauthn_register_begin(
    options: RegistrationOptions = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Begin WebAuthn registration process by generating registration options.
    
    Args:
        options: Registration options including authenticator type
        current_user: Authenticated user
        db: Database session
        
    Returns:
        RegistrationOptionsResponse: Contains options for WebAuthn client
    """
    try:
        options_data = WebAuthnManager.generate_registration_options_for_user(
            db=db,
            user=current_user,
            credential_name=options.credential_name,
            authenticator_attachment=options.authenticator_attachment
        )
        
        return {
            "options": options_data,
            "user_id": current_user.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate registration options: {str(e)}"
        )


@router.post("/register/verify", response_model=CredentialResponse)
async def webauthn_register_complete(
    verification: RegistrationVerification = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete WebAuthn registration by verifying the attestation and saving the credential.
    
    Args:
        verification: Registration verification data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        CredentialResponse: Details of the newly registered credential
    """
    try:
        # Process and verify the registration response
        credential = WebAuthnManager.verify_registration_response_and_save_credential(
            db=db,
            user=current_user,
            credential_data=verification.credential,
            credential_name=verification.credential_name,
            device_type=verification.device_type
        )
        
        # Return the credential information
        return {
            "id": credential.id,
            "name": credential.name,
            "created_at": credential.created_at,
            "device_type": credential.device_type,
            "message": "Registration successful"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/authenticate/options", response_model=AuthenticationOptionsResponse)
async def webauthn_authenticate_begin(
    options: AuthenticationOptions = Body(...), 
    db: Session = Depends(get_db)
):
    """
    Begin WebAuthn authentication by generating authentication options.
    
    Args:
        options: Authentication options
        db: Database session
        
    Returns:
        AuthenticationOptionsResponse: Contains options for WebAuthn client
    """
    print(f"[AUTH_OPTIONS_DEBUG] Received options: {options.dict()}")
    try:
        user = None
        user_id = None
        
        # If username is provided, find the user
        if options.username:
            user = db.query(User).filter(User.username == options.username).first()
            
        # If email is provided, find the user
        elif options.email:
            user = db.query(User).filter(User.email == options.email).first()
            
        # If user_id is provided, use that directly
        elif options.user_id:
            user_id = options.user_id
            
        # If we found a user by username/email, get their ID
        if user:
            user_id = user.id
            print(f"[AUTH_OPTIONS_DEBUG] Found user by identifier: user_id={user_id}")
            
        # If we still don't have a user_id, return an error
        if not user_id:
            print(f"[AUTH_OPTIONS_DEBUG] User not found for options: {options.dict()}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user found"
            )
            
        # Generate authentication options
        print(f"[AUTH_OPTIONS_DEBUG] Calling generate_authentication_options for user_id={user_id}")
        options_data = WebAuthnManager.generate_authentication_options(
            db=db,
            user_id=user_id,
            user_verification=options.user_verification
        )
        
        return {
            "options": options_data,
            "user_id": user_id
        }
    except Exception as e:
        print(f"[AUTH_OPTIONS_ERROR] Exception in webauthn_authenticate_begin: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate authentication options: {str(e)}"
        )


@router.post("/authenticate/verify")
async def webauthn_authenticate_complete(
    verification: AuthenticationVerification = Body(...),
    db: Session = Depends(get_db)
):
    """
    Complete WebAuthn authentication by verifying the assertion and creating a session.
    
    Args:
        verification: Authentication verification data
        db: Database session
        
    Returns:
        JWT token for authenticated session
    """
    try:
        # Verify the authentication
        success, credential = WebAuthnManager.verify_authentication_response(
            db=db,
            user_id=verification.user_id,
            credential_data=verification.credential
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
            
        # Get the user associated with this credential
        user = db.query(User).filter(User.id == credential.user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Update last login time
        user.last_login = datetime.now()
        db.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        # Return token details
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/credentials", response_model=List[CredentialSummary])
async def get_user_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get credentials associated with the current user.
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List[CredentialSummary]: List of user's registered WebAuthn credentials
    """
    credentials = db.query(WebAuthnCredential).filter(
        WebAuthnCredential.user_id == current_user.id
    ).all()
    
    return [
        {
            "id": cred.id,
            "name": cred.name,
            "created_at": cred.created_at,
            "last_used_at": cred.last_used_at,
            "device_type": cred.device_type
        }
        for cred in credentials
    ]


@router.delete("/credentials/{credential_id}", response_model=Dict[str, str])
async def delete_credential(
    credential_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a WebAuthn credential.
    
    Args:
        credential_id: ID of credential to delete
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Dict with success message
    """
    # Check that the credential exists and belongs to this user
    credential = db.query(WebAuthnCredential).filter(
        WebAuthnCredential.id == credential_id,
        WebAuthnCredential.user_id == current_user.id
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found or doesn't belong to you"
        )
    
    # Delete the credential
    db.delete(credential)
    
    # Check if this was the user's last WebAuthn credential
    remaining_credentials = db.query(WebAuthnCredential).filter(
        WebAuthnCredential.user_id == current_user.id
    ).count()
    
    # If no WebAuthn credentials remain and WebAuthn was the preferred method, reset MFA settings
    if remaining_credentials == 0 and current_user.preferred_mfa_method.value == "webauthn":
        from app.models.user import MFAMethod
        current_user.preferred_mfa_method = MFAMethod.NONE
        current_user.mfa_enabled = False
    
    db.commit()
    
    return {"message": "Credential deleted successfully"} 