"""
Settings Management Routes
------------------------
This module defines the settings management API endpoints for the EnCompliance system.
It provides:
- System settings configuration
- User preferences management
- Application configuration
- Feature flags
- Environment settings
- System parameters
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.database import get_db
from app.auth.dependencies import get_current_user
from fastapi.responses import JSONResponse
import logging
import json
import os
from pydantic import BaseModel

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings"])

# Define the settings model
class ModelSettings(BaseModel):
    # New unified fields
    api_key: Optional[str] = None
    provider: Optional[str] = "auto"  # 'auto', 'openai', 'anthropic', 'google', 'other'
    other_api_url: Optional[str] = None  # URL for custom API provider
    
    # Legacy fields (kept for backward compatibility)
    local_model_url: Optional[str] = "http://127.0.0.1:1234"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    custom_model_url: Optional[str] = None
    custom_api_key: Optional[str] = None

# Add OPTIONS handler for CORS preflight requests
@router.options("/settings/model")
async def options_settings():
    """
    Handle OPTIONS requests for settings endpoints.
    """
    headers = {
        "Access-Control-Allow-Origin": "http://localhost:5174",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, x-token",
        "Access-Control-Max-Age": "600",
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(content={}, headers=headers)

@router.get("/settings/model")
async def get_model_settings(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get model settings for the current user.
    """
    try:
        # Create settings directory if it doesn't exist
        settings_dir = os.path.join(os.getcwd(), "user_settings")
        os.makedirs(settings_dir, exist_ok=True)
        
        # Path to user's settings file
        settings_file = os.path.join(settings_dir, f"user_{current_user.id}_model_settings.json")
        
        # Check if settings file exists
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                settings = json.load(f)
                
            # Mask API keys for security
            if "api_key" in settings and settings["api_key"]:
                settings["api_key"] = "********"
            if "openai_api_key" in settings and settings["openai_api_key"]:
                settings["openai_api_key"] = "********"
            if "anthropic_api_key" in settings and settings["anthropic_api_key"]:
                settings["anthropic_api_key"] = "********"
            if "custom_api_key" in settings and settings["custom_api_key"]:
                settings["custom_api_key"] = "********"
                
            return settings
        else:
            # Return default settings
            return {
                "api_key": "",
                "provider": "auto",
                "local_model_url": "http://127.0.0.1:1234",
                "openai_api_key": "",
                "anthropic_api_key": "",
                "custom_model_url": "",
                "custom_api_key": ""
            }
    except Exception as e:
        logger.error(f"Error getting model settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get model settings"
        )

@router.post("/settings/model")
async def save_model_settings(
    settings: ModelSettings,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Save model settings for the current user.
    """
    try:
        # Create settings directory if it doesn't exist
        settings_dir = os.path.join(os.getcwd(), "user_settings")
        os.makedirs(settings_dir, exist_ok=True)
        
        # Path to user's settings file
        settings_file = os.path.join(settings_dir, f"user_{current_user.id}_model_settings.json")
        
        # Save settings to file
        with open(settings_file, "w") as f:
            json.dump(settings.dict(), f)
            
        # Update environment variables for the current session
        # Handle the unified API key based on provider
        if settings.api_key:
            from app.services.llm_service import detect_provider
            provider = settings.provider if settings.provider != "auto" else None
            detected_provider = detect_provider(settings.api_key, provider)
            
            # Clear existing API keys first
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]
            if "GOOGLE_API_KEY" in os.environ:
                del os.environ["GOOGLE_API_KEY"]
            if "OTHER_API_KEY" in os.environ:
                del os.environ["OTHER_API_KEY"]
            
            # Set the appropriate environment variable based on the detected provider
            if detected_provider == "openai":
                os.environ["OPENAI_API_KEY"] = settings.api_key
                print(f"Set OpenAI API key for user {current_user.id}")
            elif detected_provider == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = settings.api_key
                print(f"Set Anthropic API key for user {current_user.id}")
            elif detected_provider == "google":
                os.environ["GOOGLE_API_KEY"] = settings.api_key
                print(f"Set Google API key for user {current_user.id}")
            elif detected_provider == "other":
                os.environ["OTHER_API_KEY"] = settings.api_key
                print(f"Set Other API key for user {current_user.id}")
                
                # Set the custom API URL if provided
                if settings.other_api_url:
                    os.environ["OTHER_API_URL"] = settings.other_api_url
                    print(f"Set Other API URL to {settings.other_api_url}")
            else:
                print(f"Unknown provider detected for API key: {detected_provider}")
        
        # Also handle legacy fields for backward compatibility
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        if settings.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
            
        # Update local model URL if provided
        if settings.local_model_url:
            os.environ["LOCAL_MODEL_URL"] = settings.local_model_url
            print(f"Set local model URL to {settings.local_model_url}")
            
        return {"message": "Settings saved successfully"}
    except Exception as e:
        logger.error(f"Error saving model settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save model settings"
        ) 