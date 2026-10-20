"""
WebAuthn Utilities Module
---------------------
This module provides utility functions for WebAuthn (passkey) integration in the EnCompliance system.
It provides:
- WebAuthn registration (attestation) generation and verification
- WebAuthn authentication (assertion) generation and verification
- Credential storage and management
- Passkey authentication flow helpers
"""

import os
import base64
import secrets
from typing import Dict, Optional, List, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import json

from fastapi import HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from webauthn import (
    generate_registration_options, 
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes
)
# Add our own implementation of bytes_to_base64url
def bytes_to_base64url(bytes_data: bytes) -> str:
    """Convert bytes to base64url encoded string without padding."""
    return base64.urlsafe_b64encode(bytes_data).decode('utf-8').rstrip('=')

from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    AuthenticatorSelectionCriteria,
    RegistrationCredential,
    AttestationConveyancePreference,
    UserVerificationRequirement,
    ResidentKeyRequirement,
    AuthenticatorAttachment,
    AuthenticationCredential,
    AuthenticatorAttestationResponse,
    PublicKeyCredentialType,
    AuthenticatorAssertionResponse
)
from webauthn.helpers.exceptions import (
    InvalidRegistrationResponse,
    InvalidAuthenticationResponse
)

from app.models.user import User
from app.models.webauthn_credential import WebAuthnCredential
from app.core.config import get_settings

settings = get_settings()

class WebAuthnManager:
    """
    Manager class for WebAuthn operations.
    """
    
    # WebAuthn Relying Party ID and name - should come from settings
    RP_ID = settings.WEBAUTHN_RP_ID
    RP_NAME = settings.WEBAUTHN_RP_NAME
    RP_ORIGIN = settings.WEBAUTHN_RP_ORIGIN

    @classmethod
    def _store_challenge_for_user(cls, db: Session, user_id: int, challenge: str) -> None:
        """
        Store WebAuthn challenge in the database for a user.
        
        Args:
            db: Database session
            user_id: User ID
            challenge: WebAuthn challenge
        """
        # Get the user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Store the challenge (this could be a separate table, but for simplicity we'll use a User column)
        # In a production environment, challenges should be stored with an expiration time
        user.webauthn_challenge = challenge
        db.commit()

    @classmethod
    def _get_stored_challenge_for_user(cls, db: Session, user_id: int) -> Optional[str]:
        """
        Get stored WebAuthn challenge from the database for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Challenge string or None if not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.webauthn_challenge:
            return None
        return user.webauthn_challenge
    
    @classmethod
    def _clear_challenge_for_user(cls, db: Session, user_id: int) -> None:
        """
        Clear WebAuthn challenge from the database for a user.
        
        Args:
            db: Database session
            user_id: User ID
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.webauthn_challenge = None
            db.commit()
    
    @classmethod
    def generate_registration_options_for_user(cls, db: Session, user: User, 
                                               credential_name: str = None,
                                               authenticator_attachment: str = None) -> Dict:
        """
        Generate WebAuthn registration options for a user.
        
        Args:
            db: Database session
            user: User object
            credential_name: Optional friendly name for the credential
            authenticator_attachment: Optional authenticator attachment type
            
        Returns:
            WebAuthn registration options dictionary
        """
        # Generate a new challenge
        challenge = secrets.token_urlsafe(32)
        
        # Store the challenge in the database
        cls._store_challenge_for_user(db, user.id, challenge)
        
        # Get existing credentials for the user to exclude
        existing_credentials = db.query(WebAuthnCredential).filter(
            WebAuthnCredential.user_id == user.id
        ).all()
        
        # Convert to exclude list format
        exclude_credentials = []
        for cred in existing_credentials:
            exclude_credentials.append(
                PublicKeyCredentialDescriptor(
                    id=base64url_to_bytes(cred.credential_id),
                    type="public-key"
                )
            )
        
        # Set authenticator attachment if specified
        authenticator_selection = None
        if authenticator_attachment:
            authenticator_selection = AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment(authenticator_attachment),
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.PREFERRED
            )
            
        # Generate registration options
        options = generate_registration_options(
            rp_id=cls.RP_ID,
            rp_name=cls.RP_NAME,
            user_id=str(user.id).encode('utf-8'),
            user_name=user.username,
            user_display_name=user.full_name or user.username,
            challenge=challenge.encode('utf-8'),
            exclude_credentials=exclude_credentials,
            authenticator_selection=authenticator_selection,
            attestation=AttestationConveyancePreference.NONE
        )
        
        # Convert to JSON serializable format and return
        options_json = options_to_json(options)
        return json.loads(options_json)
    
    @classmethod
    def verify_registration_response_and_save_credential(
        cls, 
        db: Session, 
        user: User, 
        credential_data: Dict,
        credential_name: str = "My passkey",
        device_type: str = None
    ) -> WebAuthnCredential:
        """
        Verify WebAuthn registration response and save the credential.
        
        Args:
            db: Database session
            user: User object
            credential_data: WebAuthn credential data
            credential_name: Optional friendly name for the credential
            device_type: Optional device type
            
        Returns:
            Newly created WebAuthnCredential object
            
        Raises:
            HTTPException: If verification fails
        """
        # Get the stored challenge
        stored_challenge = cls._get_stored_challenge_for_user(db, user.id)
        if not stored_challenge:
            print(f"[WEBAUTHN_DEBUG] No stored challenge found for user {user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No challenge found for user. Please try again."
            )
        print(f"[WEBAUTHN_DEBUG] Found stored challenge for user {user.id}: {stored_challenge[:5]}...")
        
        try:
            # Parse the credential data
            print(f"[WEBAUTHN_DEBUG] Parsing credential data: {json.dumps(credential_data)[:100]}...")
            # Map and convert fields as needed for RegistrationCredential
            response_data = credential_data["response"]
            attestation_response = AuthenticatorAttestationResponse(
                client_data_json=base64url_to_bytes(response_data["clientDataJSON"]),
                attestation_object=base64url_to_bytes(response_data["attestationObject"]),
                transports=response_data.get("transports")
            )
            registration_credential = RegistrationCredential(
                id=credential_data["id"],
                raw_id=base64url_to_bytes(credential_data["rawId"]),
                response=attestation_response,
                type=credential_data.get("type", "public-key"),
                authenticator_attachment=credential_data.get("authenticatorAttachment")
            )
            print(f"[WEBAUTHN_DEBUG] Credential data parsed successfully.")
            
            # Verify the registration
            print(f"[WEBAUTHN_DEBUG] Verifying registration response...")
            print(f"[WEBAUTHN_DEBUG]   - expected_challenge: {stored_challenge[:5]}...")
            print(f"[WEBAUTHN_DEBUG]   - expected_rp_id: {cls.RP_ID}")
            print(f"[WEBAUTHN_DEBUG]   - expected_origin: {cls.RP_ORIGIN}")
            
            verification = verify_registration_response(
                credential=registration_credential,
                expected_challenge=stored_challenge.encode('utf-8'),
                expected_rp_id=cls.RP_ID,
                expected_origin=cls.RP_ORIGIN,
                require_user_verification=False # Set to True if you require user verification (e.g., PIN, biometric)
            )
            print(f"[WEBAUTHN_DEBUG] Registration verified successfully. Sign count: {verification.sign_count}")
            
            # Extract credential details
            credential_id = bytes_to_base64url(verification.credential_id)
            print(f"[WEBAUTHN_DEBUG] Credential ID extracted: {credential_id[:10]}...")
            
            # Check if credential already exists
            existing_credential = db.query(WebAuthnCredential).filter(
                WebAuthnCredential.credential_id == credential_id
            ).first()
            
            if existing_credential:
                print(f"[WEBAUTHN_DEBUG] Credential ID {credential_id[:10]}... already exists.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Credential already registered"
                )
                
            # Create new credential
            print(f"[WEBAUTHN_DEBUG] Creating new WebAuthnCredential record...")
            new_credential = WebAuthnCredential(
                user_id=user.id,
                credential_id=credential_id,
                public_key=verification.credential_public_key,
                sign_count=verification.sign_count,
                name=credential_name,
                device_type=device_type,
                created_at=datetime.now(),
                last_used_at=None
            )
            
            # Save to database
            db.add(new_credential)
            db.commit()
            db.refresh(new_credential)
            print(f"[WEBAUTHN_DEBUG] New credential saved with ID: {new_credential.id}")
            
            # Clear the challenge
            cls._clear_challenge_for_user(db, user.id)
            print(f"[WEBAUTHN_DEBUG] Cleared challenge for user {user.id}")
            
            # Update user mfa_enabled and preferred_mfa_method if this is their first WebAuthn credential
            user_credentials_count = db.query(WebAuthnCredential).filter(
                WebAuthnCredential.user_id == user.id
            ).count()
            
            if user_credentials_count == 1:
                from app.models.user import MFAMethod
                user.mfa_enabled = True
                user.preferred_mfa_method = MFAMethod.WEBAUTHN
                db.commit()
                print(f"[WEBAUTHN_DEBUG] Updated MFA settings for user {user.id}")
                
            return new_credential
            
        except InvalidRegistrationResponse as e:
            print(f"[WEBAUTHN_ERROR] InvalidRegistrationResponse: {str(e)}") # Log specific error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid registration response: {str(e)}"
            )
        except Exception as e:
            # Log the full exception for debugging
            import traceback
            print(f"[WEBAUTHN_ERROR] Unexpected exception during verification: {str(e)}")
            print(traceback.format_exc()) # Print the full traceback
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Verification failed: {str(e)}"
            )
        finally:
            # Always clear the challenge on completion (success or failure)
            # Check if user object exists before clearing challenge to avoid errors if user wasn't found
            if user:
                cls._clear_challenge_for_user(db, user.id)
                print(f"[WEBAUTHN_DEBUG] Ensured challenge is cleared for user {user.id} in finally block.")
    
    @classmethod
    def generate_authentication_options(
        cls, 
        db: Session, 
        user_id: Optional[int] = None,
        user_verification: str = "preferred"
    ) -> Dict:
        """
        Generate WebAuthn authentication options.
        
        Args:
            db: Database session
            user_id: Optional user ID (if known)
            user_verification: User verification requirement
            
        Returns:
            WebAuthn authentication options dictionary
        """
        print(f"[WEBAUTHN_MANAGER_DEBUG] generate_authentication_options called for user_id={user_id}") # Log entry
        # Generate a new challenge
        challenge = secrets.token_urlsafe(32)
        
        allow_credentials = None
        
        # If user_id is provided, get their credentials
        if user_id:
            # Store the challenge
            cls._store_challenge_for_user(db, user_id, challenge)
            print(f"[WEBAUTHN_MANAGER_DEBUG] Stored challenge for user_id={user_id}") # Log challenge stored
            
            # Get credentials for this user
            credentials = db.query(WebAuthnCredential).filter(
                WebAuthnCredential.user_id == user_id
            ).all()
            print(f"[WEBAUTHN_MANAGER_DEBUG] Found {len(credentials)} credentials for user_id={user_id}") # Log credential count
            
            if not credentials:
                print(f"[WEBAUTHN_MANAGER_ERROR] No credentials found for user_id={user_id}") # Log no credentials error
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No credentials found for user"
                )
            
            # Create allow_credentials list
            allow_credentials = [
                PublicKeyCredentialDescriptor(
                    type=PublicKeyCredentialType.PUBLIC_KEY,
                    id=base64url_to_bytes(cred.credential_id)
                )
                for cred in credentials
            ]
        else:
            # For discovery flow, store the challenge in the session
            # (For simplicity in this example, we're not implementing this - 
            # in a real app you'd store this in a session or temporary storage)
            pass
        
        # Generate authentication options
        if isinstance(user_verification, str):
            user_verification_enum = UserVerificationRequirement[user_verification.upper()]
        else:
            user_verification_enum = user_verification
        options = generate_authentication_options(
            rp_id=cls.RP_ID,
            challenge=challenge.encode('utf-8'),
            allow_credentials=allow_credentials,
            user_verification=user_verification_enum
        )
        
        # Return serializable dictionary
        options_json = options_to_json(options)
        return json.loads(options_json)
    
    @classmethod
    def verify_authentication_response(
        cls, 
        db: Session, 
        user_id: int,
        credential_data: Dict
    ) -> Tuple[bool, Optional[WebAuthnCredential]]:
        """
        Verify WebAuthn authentication response.
        
        Args:
            db: Database session
            user_id: User ID
            credential_data: WebAuthn credential data
            
        Returns:
            Tuple of (success, credential)
            
        Raises:
            HTTPException: If verification fails
        """
        # Get the stored challenge
        stored_challenge = cls._get_stored_challenge_for_user(db, user_id)
        if not stored_challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No challenge found. Please try again."
            )
            
        try:
            # Manually parse the credential data from the frontend
            print(f"[WEBAUTHN_MANAGER_DEBUG] Verifying authentication for user_id={user_id}")
            print(f"[WEBAUTHN_MANAGER_DEBUG] Raw credential_data received: {json.dumps(credential_data)}") # Log raw data
            
            # Check top-level keys
            if "response" not in credential_data or "id" not in credential_data or "rawId" not in credential_data:
                print("[WEBAUTHN_MANAGER_ERROR] Missing top-level keys in credential_data")
                raise ValueError("Invalid credential data structure: Missing top-level keys")
                
            response_data = credential_data["response"]
            print(f"[WEBAUTHN_MANAGER_DEBUG] response_data: {json.dumps(response_data)}")
            
            # Check required keys in response_data
            required_response_keys = ["clientDataJSON", "authenticatorData", "signature"]
            for key in required_response_keys:
                if key not in response_data:
                    print(f"[WEBAUTHN_MANAGER_ERROR] Missing key '{key}' in response_data")
                    raise ValueError(f"Invalid credential data structure: Missing key '{key}' in response")

            # Safely decode base64 fields
            try:
                client_data_json_bytes = base64url_to_bytes(response_data["clientDataJSON"])
                authenticator_data_bytes = base64url_to_bytes(response_data["authenticatorData"])
                signature_bytes = base64url_to_bytes(response_data["signature"])
                user_handle_bytes = base64url_to_bytes(response_data["userHandle"]) if response_data.get("userHandle") else None
                raw_id_bytes = base64url_to_bytes(credential_data["rawId"])
            except Exception as decode_error:
                print(f"[WEBAUTHN_MANAGER_ERROR] Base64 decoding failed: {str(decode_error)}")
                raise ValueError(f"Base64 decoding failed: {str(decode_error)}")

            assertion_response = AuthenticatorAssertionResponse(
                client_data_json=client_data_json_bytes,
                authenticator_data=authenticator_data_bytes,
                signature=signature_bytes,
                user_handle=user_handle_bytes
            )
            print("[WEBAUTHN_MANAGER_DEBUG] AuthenticatorAssertionResponse created successfully.")
            
            authentication_credential = AuthenticationCredential(
                id=credential_data["id"],
                raw_id=raw_id_bytes,
                response=assertion_response,
                type=PublicKeyCredentialType.PUBLIC_KEY, # Use enum directly
                authenticator_attachment=credential_data.get("authenticatorAttachment")
            )
            print(f"[WEBAUTHN_MANAGER_DEBUG] Authentication credential object created successfully.")
            
            # Find the credential in the database
            credential = db.query(WebAuthnCredential).filter(
                WebAuthnCredential.credential_id == credential_data["id"]
            ).first()
            
            if not credential:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unknown credential"
                )
                
            # Verify the credential belongs to the user
            if credential.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Credential doesn't belong to user"
                )
                
            # Verify the authentication
            verification = verify_authentication_response(
                credential=authentication_credential,
                expected_challenge=stored_challenge.encode('utf-8'),
                expected_rp_id=cls.RP_ID,
                expected_origin=cls.RP_ORIGIN,
                credential_public_key=credential.public_key,
                credential_current_sign_count=credential.sign_count,
                require_user_verification=False
            )
            
            # Update the credential's sign count and last used timestamp
            credential.sign_count = verification.new_sign_count
            credential.last_used_at = datetime.now()
            db.commit()
            
            # Clear the challenge
            cls._clear_challenge_for_user(db, user_id)
            
            return True, credential
            
        except InvalidAuthenticationResponse as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid authentication response: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Authentication failed: {str(e)}"
            )
        finally:
            # Always clear the challenge on completion
            cls._clear_challenge_for_user(db, user_id) 