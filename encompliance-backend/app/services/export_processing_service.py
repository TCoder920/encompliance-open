"""
Export Processing Service Module

This module provides background processing for data exports using Python threading.
It manages the complete export workflow from initiation to completion.

Key functionalities:
- Background thread spawning for export processing
- Real-time progress tracking and status updates
- Export file generation and management
- Error handling and recovery
- Database status updates throughout processing
- Integration with data extraction and file generation services

Dependencies:
- threading: For background processing
- sqlalchemy: For database status updates
- pathlib: For file system operations

Educational Note: Implements background processing with proper thread management
Reference: Python Threading Documentation - https://docs.python.org/3/library/threading.html
"""

import threading
import asyncio
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path
import logging
import traceback
import uuid

from app.database import get_db
from app.models.export_request import ExportRequest, ExportStatus
from app.services.data_extraction_service import DataExtractionService
from app.services.export_file_service import ExportFileService
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationCreate
from app.models.notification import NotificationType, NotificationPriority

logger = logging.getLogger(__name__)

class ExportProcessingService:
    """Service for managing background export processing."""
    
    # Class-level tracking of active exports
    _active_exports = {}
    _lock = threading.Lock()
    
    @staticmethod
    def start_export_processing(export_id: str) -> bool:
        """Start background processing for an export request."""
        try:
            with ExportProcessingService._lock:
                if export_id in ExportProcessingService._active_exports:
                    logger.warning(f"Export {export_id} is already being processed")
                    return False
                
                # Mark as active
                ExportProcessingService._active_exports[export_id] = {
                    "started_at": datetime.utcnow(),
                    "thread_id": None
                }
            
            # Start background thread
            thread = threading.Thread(
                target=ExportProcessingService._process_export_background,
                args=(export_id,),
                daemon=True
            )
            thread.start()
            
            # Update thread info
            with ExportProcessingService._lock:
                ExportProcessingService._active_exports[export_id]["thread_id"] = thread.ident
            
            logger.info(f"Started background processing for export {export_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting export processing for {export_id}: {str(e)}")
            # Clean up tracking
            with ExportProcessingService._lock:
                ExportProcessingService._active_exports.pop(export_id, None)
            return False
    
    @staticmethod
    def _process_export_background(export_id: str):
        """Background thread function for processing exports."""
        db = None
        try:
            # Get database session
            db = next(get_db())
            
            # Get export request
            export_request = db.query(ExportRequest).filter(
                ExportRequest.id == export_id
            ).first()
            
            if not export_request:
                logger.error(f"Export request {export_id} not found")
                return
            
            # Update status to processing
            ExportProcessingService._update_export_status(
                db, export_request, ExportStatus.PROCESSING, 5
            )
            
            # Extract user data
            logger.info(f"Extracting data for export {export_id}")
            extracted_data = DataExtractionService.extract_all_user_data(
                db, export_request.user_id, export_request.data_types
            )
            
            if "error" in extracted_data:
                raise Exception(f"Data extraction failed: {extracted_data['error']}")
            
            # Update progress
            ExportProcessingService._update_export_status(
                db, export_request, ExportStatus.PROCESSING, 30
            )
            
            # Calculate actual data size
            actual_size = DataExtractionService.calculate_data_size(extracted_data)
            export_request.actual_size = actual_size
            db.commit()
            
            # Generate export file
            logger.info(f"Generating export file for export {export_id}")
            file_path = ExportFileService.generate_export_file(
                extracted_data, export_request.format, export_id
            )
            
            if not file_path:
                raise Exception("Failed to generate export file")
            
            # Update progress
            ExportProcessingService._update_export_status(
                db, export_request, ExportStatus.PROCESSING, 70
            )
            
            # Update export request with file path
            export_request.file_path = str(file_path)
            export_request.download_expires_at = datetime.utcnow() + timedelta(hours=72)
            db.commit()
            
            # Add to document library
            logger.info(f"Adding export to document library for export {export_id}")
            document_id = ExportFileService.add_to_document_library(
                db, export_request.user_id, file_path, export_request.format, export_id
            )
            
            if document_id:
                export_request.document_id = document_id
                db.commit()
            
            # Update progress
            ExportProcessingService._update_export_status(
                db, export_request, ExportStatus.PROCESSING, 90
            )
            
            # Mark as completed
            ExportProcessingService._update_export_status(
                db, export_request, ExportStatus.COMPLETED, 100
            )
            
            # Send completion notification
            ExportProcessingService._send_completion_notification(
                db, export_request.user_id, export_id, True
            )
            
            logger.info(f"Export {export_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing export {export_id}: {str(e)}")
            logger.error(traceback.format_exc())
            
            try:
                if db and export_request:
                    # Mark as failed
                    export_request.status = ExportStatus.FAILED
                    export_request.error_message = str(e)
                    export_request.updated_at = datetime.utcnow()
                    db.commit()
                    
                    # Send failure notification
                    ExportProcessingService._send_completion_notification(
                        db, export_request.user_id, export_id, False, str(e)
                    )
            except Exception as notif_error:
                logger.error(f"Error updating failed export status: {str(notif_error)}")
        
        finally:
            # Clean up database session
            if db:
                db.close()
            
            # Remove from active exports tracking
            with ExportProcessingService._lock:
                ExportProcessingService._active_exports.pop(export_id, None)
    
    @staticmethod
    def _update_export_status(
        db: Session, 
        export_request: ExportRequest, 
        status: str, 
        progress: int
    ):
        """Update export status and progress in database."""
        try:
            export_request.status = status
            export_request.progress_percentage = progress
            export_request.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(export_request)
            
            logger.info(f"Updated export {export_request.id} status to {status} ({progress}%)")
            
        except Exception as e:
            logger.error(f"Error updating export status: {str(e)}")
            db.rollback()
    
    @staticmethod
    def _send_completion_notification(
        db: Session, 
        user_id: int, 
        export_id: str, 
        success: bool, 
        error_message: str = None
    ):
        """Send notification when export completes or fails."""
        try:
            if success:
                title = "Data Export Completed"
                message = f"Your data export is ready for download. The download link will expire in 72 hours."
                action_url = f"/documents?export={export_id}"
            else:
                title = "Data Export Failed"
                message = f"Your data export failed to complete. Error: {error_message or 'Unknown error'}"
                action_url = f"/export"
            
            notification = NotificationCreate(
                title=title,
                message=message,
                type=NotificationType.SYSTEM,
                priority=NotificationPriority.HIGH if not success else NotificationPriority.MEDIUM,
                related_id=export_id,
                related_type="export",
                action_url=action_url
            )
            
            # Create notification using the service
            asyncio.create_task(
                NotificationService.create_notification(
                    db, notification, user_id, send_email=True, send_push=True
                )
            )
            
        except Exception as e:
            logger.error(f"Error sending export completion notification: {str(e)}")
    
    @staticmethod
    def get_active_exports() -> Dict[str, Any]:
        """Get information about currently active exports."""
        with ExportProcessingService._lock:
            return dict(ExportProcessingService._active_exports)
    
    @staticmethod
    def is_export_active(export_id: str) -> bool:
        """Check if an export is currently being processed."""
        with ExportProcessingService._lock:
            return export_id in ExportProcessingService._active_exports
    
    @staticmethod
    def cleanup_expired_exports(db: Session) -> int:
        """Clean up expired export files and database records."""
        try:
            # Find expired exports
            expired_exports = db.query(ExportRequest).filter(
                ExportRequest.status == ExportStatus.COMPLETED,
                ExportRequest.download_expires_at < datetime.utcnow()
            ).all()
            
            cleaned_count = 0
            for export in expired_exports:
                try:
                    # Delete physical file if it exists
                    if export.file_path and Path(export.file_path).exists():
                        Path(export.file_path).unlink()
                        logger.info(f"Deleted expired export file: {export.file_path}")
                    
                    # Update database record
                    export.status = "expired"
                    export.file_path = None
                    export.updated_at = datetime.utcnow()
                    
                    cleaned_count += 1
                    
                except Exception as e:
                    logger.error(f"Error cleaning up export {export.id}: {str(e)}")
            
            db.commit()
            logger.info(f"Cleaned up {cleaned_count} expired exports")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error in cleanup_expired_exports: {str(e)}")
            db.rollback()
            return 0 