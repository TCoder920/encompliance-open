"""
Security Utilities Module

This module provides encryption and decryption utilities for sensitive application data.
It implements secure data handling using Fernet symmetric encryption.

Key functionalities:
- Secure encryption of sensitive settings and data
- Decryption of encrypted data with error handling
- Key derivation from application secret key
- Debug logging for encryption/decryption operations

Dependencies:
- cryptography: For Fernet encryption implementation
- json: For data serialization
- base64: For key encoding
"""

import os
import json
from cryptography.fernet import Fernet
from app.core.config import get_settings

settings = get_settings()

# Ensure a consistent encryption key is used. 
# It *should* be stored securely (e.g., env variable, secrets manager), not hardcoded.
# For demonstration, using a key derived from the app's SECRET_KEY.
# !! IMPORTANT: If SECRET_KEY changes, previously encrypted data will be unreadable !!
# A more robust solution would use a dedicated, unchanging encryption key.
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

salt = b'\x00' * 16 # Use a fixed salt for deriving key from SECRET_KEY, or better, store a separate ENC_KEY
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
)
encryption_key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))

fernet = Fernet(encryption_key)

def encrypt_settings(settings_dict: dict) -> bytes:
    """Encrypts a dictionary of settings into bytes."""
    print(f"ENCRYPT DEBUG - Settings being encrypted: {settings_dict}")
    # Important to check if api_key is in the settings
    if 'api_key' in settings_dict:
        print(f"ENCRYPT DEBUG - API Key present with length: {len(settings_dict['api_key'])}")
    else:
        print("ENCRYPT DEBUG - No API key in settings dictionary!")
        
    settings_json = json.dumps(settings_dict)
    encrypted_data = fernet.encrypt(settings_json.encode())
    print(f"ENCRYPT DEBUG - Encrypted data length: {len(encrypted_data)}")
    return encrypted_data

def decrypt_settings(encrypted_data: bytes) -> dict:
    """Decrypts bytes back into a dictionary of settings."""
    if not encrypted_data:
        print("DECRYPT DEBUG - No encrypted data provided!")
        return {}
    try:
        print(f"DECRYPT DEBUG - Trying to decrypt data of length: {len(encrypted_data)}")
        decrypted_json = fernet.decrypt(encrypted_data)
        settings_dict = json.loads(decrypted_json.decode())
        
        # Debug what we have after decryption
        print(f"DECRYPT DEBUG - Successfully decrypted settings: {settings_dict}")
        if 'api_key' in settings_dict:
            print(f"DECRYPT DEBUG - API Key found with length: {len(settings_dict['api_key'])}")
        else:
            print("DECRYPT DEBUG - No API key in decrypted settings!")
            
        return settings_dict
    except Exception as e:
        print(f"Error decrypting settings: {e}. Returning empty dict.")
        # Handle cases where decryption fails (e.g., key change, corrupted data)
        return {} 