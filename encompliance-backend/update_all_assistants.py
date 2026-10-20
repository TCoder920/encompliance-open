#!/usr/bin/env python3
"""
Update All AI Assistants Script

This script updates all existing AI assistants with the latest system prompt.
It can be run independently to ensure all users get the updated prompt immediately.

Usage:
    python update_all_assistants.py

Requirements:
    - OpenAI API key configured in environment
    - Database connection available
    - Run from the encompliance-backend directory
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from openai import AsyncOpenAI
from app.database import SessionLocal
from app.models.user import User
from app.core.config import get_settings
from app.core.openai_utils import get_or_create_user_assistant
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def update_all_assistants():
    """Update all existing AI assistants with the latest system prompt."""
    try:
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            logger.error("OpenAI API key not configured")
            return False
        
        openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Get all users who have OpenAI assistant IDs
            users_with_assistants = db.query(User).filter(
                User.openai_assistant_id.isnot(None)
            ).all()
            
            logger.info(f"Found {len(users_with_assistants)} users with existing assistants")
            
            updated_count = 0
            failed_count = 0
            
            for user in users_with_assistants:
                try:
                    # Determine the model based on user's subscription
                    model_name = "gpt-4.1-mini" if user.subscription_status == "pro" else "gpt-4.1-nano"
                    
                    logger.info(f"Updating assistant for user {user.id} (subscription: {user.subscription_status})")
                    
                    # This will check and update the assistant if needed
                    await get_or_create_user_assistant(
                        user_id=user.id,
                        db=db,
                        openai_client=openai_client,
                        model_name=model_name
                    )
                    
                    updated_count += 1
                    logger.info(f"✓ Successfully updated assistant for user {user.id}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"✗ Failed to update assistant for user {user.id}: {str(e)}")
            
            logger.info(f"\nUpdate Summary:")
            logger.info(f"Total users with assistants: {len(users_with_assistants)}")
            logger.info(f"Successfully updated: {updated_count}")
            logger.info(f"Failed updates: {failed_count}")
            
            return failed_count == 0
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error during assistant update process: {str(e)}")
        return False

def main():
    """Main function to run the assistant update process."""
    logger.info("Starting AI assistant update process...")
    
    # Run the async update function
    success = asyncio.run(update_all_assistants())
    
    if success:
        logger.info("✓ All assistants updated successfully!")
        sys.exit(0)
    else:
        logger.error("✗ Some assistants failed to update. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 