"""
Configuration Module

This module manages the application's configuration settings and environment variables.
It provides a centralized configuration system using Pydantic for type-safe settings management.

Key functionalities:
- Environment variable loading and validation
- Application-wide settings management
- Security configuration (JWT, API keys)
- Database connection settings
- Email service configuration
- File storage paths
- OpenAI API integration settings
- CORS and frontend URL configuration

Dependencies:
- pydantic: For settings management and validation
- python-dotenv: For environment variable loading
- os: For path and environment operations
"""

import os
from typing import Optional
# Updated import for Pydantic v2.x
try:
    # Try to import from pydantic-settings (Pydantic v2.x)
    from pydantic_settings import BaseSettings
    PYDANTIC_V2 = True
except ImportError:
    # Fallback for Pydantic v1.x
    from pydantic import BaseSettings
    PYDANTIC_V2 = False
from functools import lru_cache
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import EmailStr, Field

# Determine the paths to potential .env files
# Backend root directory (where main.py typically runs from or where .env is stored)
backend_root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
backend_env_path = os.path.join(backend_root_path, ".env")

# Project root directory (one level up from backend)
project_root_path = os.path.dirname(backend_root_path)
project_env_path = os.path.join(project_root_path, ".env")

# Load environment variables at module level to ensure they are available
# when Pydantic Settings are initialized (especially for default factory/os.getenv calls)
if os.path.exists(backend_env_path):
    load_dotenv(backend_env_path, override=False)
elif os.path.exists(project_env_path):
    load_dotenv(project_env_path, override=False)


class Settings(BaseSettings):
    """Application settings."""
    APP_NAME: str = "Encompliance.io API"
    API_V1_STR: str = "/api/v1"
    
    # Security settings
    SECRET_KEY: str = Field(..., min_length=32, validation_alias="SECRET_KEY")
    JWT_SECRET_KEY: str = Field(..., min_length=32, validation_alias="JWT_SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- Support portal security settings ---
    SUPPORT_PORTAL_SECRET_KEY: str = Field(..., min_length=32)
    SUPPORT_PORTAL_ALGORITHM: str = os.getenv(
        "SUPPORT_PORTAL_ALGORITHM", "HS256"
    )
    SUPPORT_PORTAL_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("SUPPORT_PORTAL_ACCESS_TOKEN_EXPIRE_MINUTES") or "60"
    )
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@localhost/encompliance"
    
    # CORS settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL") or "http://localhost:5174"
    
    # WebAuthn settings
    WEBAUTHN_RP_ID: str = os.getenv("WEBAUTHN_RP_ID", "localhost")
    WEBAUTHN_RP_NAME: str = os.getenv("WEBAUTHN_RP_NAME", "EnCompliance")
    WEBAUTHN_RP_ORIGIN: str = os.getenv("WEBAUTHN_RP_ORIGIN", "http://localhost:5174")
    WEBAUTHN_TIMEOUT: int = int(os.getenv("WEBAUTHN_TIMEOUT") or "60000")
    
    # Email settings
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    
    # Use environment variables directly to capture SMTP_USER if configured in .env
    # The default value logic here handles cases where one might be missing
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL: Optional[str] = os.getenv("SMTP_FROM_EMAIL") or os.getenv("EMAILS_FROM_EMAIL")
    SMTP_FROM_NAME: Optional[str] = os.getenv("SMTP_FROM_NAME") or os.getenv("EMAILS_FROM_NAME", "EnCompliance Support")
    
    # Legacy email settings for backward compatibility
    SMTP_TLS: bool = True
    SMTP_USER: Optional[EmailStr] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = "EnCompliance Support"
    SUPPORT_EMAIL: Optional[EmailStr] = os.getenv("SUPPORT_EMAIL")
    
    # Push notification settings
    VAPID_PRIVATE_KEY: Optional[str] = os.getenv("VAPID_PRIVATE_KEY")
    VAPID_PRIVATE_KEY_B64: Optional[str] = os.getenv("VAPID_PRIVATE_KEY_B64")
    VAPID_PRIVATE_KEY_B64URL: Optional[str] = os.getenv("VAPID_PRIVATE_KEY_B64URL")
    VAPID_PUBLIC_KEY: Optional[str] = os.getenv("VAPID_PUBLIC_KEY")
    VAPID_EMAIL: Optional[str] = os.getenv("VAPID_EMAIL")
    # Data export settings
    USER_DATA_EXPORT_PATH: str = os.getenv("USER_DATA_EXPORT_PATH", "storage/deleted-user-data")
    USER_DATA_EXPORT_RETENTION_DAYS: int = int(os.getenv("USER_DATA_EXPORT_RETENTION_DAYS") or "30")
    
    # PDF storage settings - HARDCODED to prevent any backend storage
    @property
    def PDF_STORAGE_PATH(self) -> str:
        """
        Returns the absolute path to the storage/regulations_by_state directory
        at the project root, regardless of any environment variable settings.
        """
        # Get the absolute path of the config.py file
        current_file = os.path.abspath(__file__)
        
        # Go up 3 levels to reach the backend root (app/core/config.py -> app/core -> app -> backend)
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        
        # Go up 1 more level to reach the project root
        project_root = os.path.dirname(backend_dir)
        
        # Hardcode the path to storage/regulations_by_state at the project root
        storage_path = os.path.join(project_root, "storage", "regulations_by_state")
        
        # Ensure the directory exists
        os.makedirs(storage_path, exist_ok=True)
        
        return storage_path
    
    # OpenAI API settings
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    BRAVE_API_KEY: str = os.getenv("BRAVE_API_KEY", "")
    OPENAI_ASSISTANT_ID: str = os.getenv("OPENAI_ASSISTANT_ID", "")
    
    # Google Calendar Configuration
    GOOGLE_CALENDAR_CLIENT_ID: str = Field("", env="GOOGLE_CALENDAR_CLIENT_ID")
    GOOGLE_CALENDAR_CLIENT_SECRET: str = Field("", env="GOOGLE_CALENDAR_CLIENT_SECRET")
    GOOGLE_CALENDAR_REDIRECT_URI: str = Field("", env="GOOGLE_CALENDAR_REDIRECT_URI")
    GOOGLE_OAUTH_CLIENT_ID: str = Field("", env="GOOGLE_OAUTH_CLIENT_ID")
    LIBRETRANSLATE_URL: str = Field("https://libretranslate.de", env="LIBRETRANSLATE_URL")
    
    # Apple Calendar Configuration
    CALDAV_DEFAULT_SERVER: str = Field("https://caldav.icloud.com", env="CALDAV_DEFAULT_SERVER")
    
    # Stripe Configuration
    STRIPE_SECRET_KEY: str = Field(..., env="STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: str = Field(..., env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field("", env="STRIPE_WEBHOOK_SECRET")
    STRIPE_PRO_BASE_PRICE_ID: str = Field("", env="STRIPE_PRO_BASE_PRICE_ID")  # Base $50 price
    STRIPE_USER_SEAT_PRICE_ID: str = Field("", env="STRIPE_USER_SEAT_PRICE_ID")  # $20 per additional user
    STRIPE_PRO_BASE_PRODUCT_ID: str = Field("", env="STRIPE_PRO_BASE_PRODUCT_ID")  # Base product ID
    STRIPE_USER_SEAT_PRODUCT_ID: str = Field("", env="STRIPE_USER_SEAT_PRODUCT_ID")  # Additional seat product ID
    STRIPE_ENVIRONMENT: str = Field("test", env="STRIPE_ENVIRONMENT")  # test or live
    
    # For debugging
    def print_settings(self):
        """Print settings for debugging"""
        settings_dict = {
            "APP_NAME": self.APP_NAME,
            "API_V1_STR": self.API_V1_STR,
            "FRONTEND_URL": self.FRONTEND_URL,
            "PDF_STORAGE_PATH": self.PDF_STORAGE_PATH,
            "OPENAI_API_KEY": "[Configured]" if self.OPENAI_API_KEY else "[Not Set]"
        }
        for key, value in settings_dict.items():
            print(f"{key}: {value}")
    
    # Pydantic configuration
    if PYDANTIC_V2:
        # Pydantic v2.x uses model_config instead of Config
        model_config = {
            "env_file": ".env",
            "case_sensitive": True,
            "extra": "ignore"  # Allow extra fields as a safety measure
        }
    else:
        # Pydantic v1.x uses Config class
        class Config:
            env_file = ".env"
            case_sensitive = True
            extra = "ignore"  # Allow extra fields as a safety measure

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings."""
    # Always try to load environment variables from .env file
    # Try loading from .env file in the backend directory first
    backend_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(backend_env_path):
        load_dotenv(backend_env_path, override=False)  # Don't override if already set
    else:
        # Try loading from .env file in the project root
        project_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env")
        if os.path.exists(project_env_path):
            load_dotenv(project_env_path, override=False)
    
    return Settings() 