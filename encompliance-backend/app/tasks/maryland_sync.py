"""
Maryland COMAR Sync Background Tasks

This module provides background task functionality for automatically
synchronizing Maryland COMAR regulations on a scheduled basis.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.maryland_comar_service import MarylandCOMARService
from app.services.maryland_regulation_processor import MarylandRegulationProcessor
from app.core.config import get_settings
from app.models.regulation import Regulation

logger = logging.getLogger(__name__)

class MarylandSyncTask:
    """Background task manager for Maryland COMAR regulation synchronization"""
    
    def __init__(self):
        self.settings = get_settings()
        self.is_running = False
        self.last_sync = None
        
    async def run_sync_task(self) -> dict:
        """
        Execute Maryland COMAR regulation sync task
        
        Returns:
            Dictionary with sync results and status
        """
        if self.is_running:
            logger.warning("Maryland sync task already running, skipping...")
            return {
                "status": "skipped",
                "message": "Sync task already in progress"
            }
        
        self.is_running = True
        sync_start = datetime.now()
        
        try:
            logger.info("Starting Maryland COMAR regulation sync task")
            
            # Get database session
            db = SessionLocal()
            
            try:
                # Extract regulations from COMAR
                comar_service = MarylandCOMARService()
                regulations = await comar_service.extract_childcare_regulations()
                
                logger.info(f"Extracted {len(regulations)} regulations from COMAR")
                
                # Process regulations and create PDFs
                processor = MarylandRegulationProcessor(self.settings.PDF_STORAGE_PATH)
                processed_regs = processor.process_regulations(regulations, db)
                
                sync_duration = datetime.now() - sync_start
                self.last_sync = sync_start
                
                logger.info(f"Successfully processed {len(processed_regs)} Maryland regulations in {sync_duration}")
                
                return {
                    "status": "completed",
                    "regulations_processed": len(processed_regs),
                    "sync_duration_seconds": sync_duration.total_seconds(),
                    "sync_timestamp": sync_start.isoformat(),
                    "regulations": processed_regs
                }
                
            finally:
                db.close()
                
        except Exception as e:
            sync_duration = datetime.now() - sync_start
            logger.error(f"Error in Maryland sync task: {str(e)}")
            
            return {
                "status": "failed",
                "error": str(e),
                "sync_duration_seconds": sync_duration.total_seconds(),
                "sync_timestamp": sync_start.isoformat()
            }
            
        finally:
            self.is_running = False
    
    def should_sync(self, force: bool = False) -> bool:
        """
        Determine if sync should run based on schedule
        
        Args:
            force: Force sync regardless of schedule
            
        Returns:
            True if sync should run
        """
        if force:
            return True
            
        if not self.last_sync:
            return True
            
        # Sync daily
        time_since_last = datetime.now() - self.last_sync
        return time_since_last >= timedelta(days=1)
    
    async def scheduled_sync(self, force: bool = False) -> Optional[dict]:
        """
        Run sync if scheduled time has arrived
        
        Args:
            force: Force sync regardless of schedule
            
        Returns:
            Sync results if sync was executed, None if skipped
        """
        if self.should_sync(force):
            return await self.run_sync_task()
        else:
            logger.info("Maryland sync not due yet, skipping...")
            return None
    
    def get_sync_status(self) -> dict:
        """Get current sync status information"""
        
        # Get database session to check current regulation count
        db = SessionLocal()
        try:
            maryland_count = db.query(Regulation).filter(
                Regulation.state_territory == "Maryland"
            ).count()
        finally:
            db.close()
        
        return {
            "is_running": self.is_running,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "maryland_regulations_count": maryland_count,
            "next_scheduled_sync": self._get_next_sync_time(),
            "sync_interval_hours": 24
        }
    
    def _get_next_sync_time(self) -> Optional[str]:
        """Calculate next scheduled sync time"""
        if not self.last_sync:
            return "immediately"
        
        next_sync = self.last_sync + timedelta(days=1)
        if next_sync <= datetime.now():
            return "immediately"
        
        return next_sync.isoformat()

# Global instance
maryland_sync_task = MarylandSyncTask()

async def run_maryland_sync(force: bool = False) -> dict:
    """
    Convenience function to run Maryland sync
    
    Args:
        force: Force sync regardless of schedule
        
    Returns:
        Sync results
    """
    return await maryland_sync_task.scheduled_sync(force)

def get_maryland_sync_status() -> dict:
    """Get Maryland sync status"""
    return maryland_sync_task.get_sync_status() 