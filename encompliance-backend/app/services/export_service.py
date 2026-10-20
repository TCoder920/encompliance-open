"""
Export Service Module

This module provides the main export functionality for the EnCompliance application.
It handles export request processing, size estimation, fee calculation, and file generation.

Key functionalities:
- Export size estimation and fee calculation
- Export request initiation and processing
- File generation in multiple formats (CSV, PDF, JSON)
- Download link management and expiration
- Integration with quota and subscription services

Dependencies:
- sqlalchemy: For database operations
- datetime: For timestamp handling
- app.models: For database models
- app.services: For quota and subscription validation
"""

from sqlalchemy.orm import Session
from app.models.export_request import ExportRequest, ExportStatus, ExportFormat
from app.models.user import User
from app.services.export_quota_service import ExportQuotaService
from app.services.data_extraction_service import DataExtractionService
from app.services.export_processing_service import ExportProcessingService
from app.utils.access_control import can_access_feature
from app.utils.tiers import get_tier_from_subscription_status
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
import json
import uuid
import logging

logger = logging.getLogger(__name__)

class ExportService:
    """Service for managing data exports."""
    
    # Size thresholds in bytes
    FEE_THRESHOLD = 1024 * 1024 * 1024  # 1GB
    FEE_PER_GB = 5.00  # $5 per GB over 1GB
    
    @staticmethod
    def estimate_export_size(db: Session, user_id: int, data_types: List[str]) -> int:
        """Estimate export size in bytes based on actual user data."""
        try:
            # Extract real user data for size estimation
            extracted_data = DataExtractionService.extract_all_user_data(db, user_id, data_types)
            
            if "error" in extracted_data:
                logger.warning(f"Error extracting data for size estimation: {extracted_data['error']}")
                # Fallback to estimates if extraction fails
                return ExportService._fallback_size_estimate(data_types)
            
            # Calculate actual size
            actual_size = DataExtractionService.calculate_data_size(extracted_data)
            
            # Add 30% overhead for formatting and metadata
            estimated_size = int(actual_size * 1.3)
            
            logger.info(f"Estimated export size for user {user_id}: {estimated_size} bytes")
            return estimated_size
            
        except Exception as e:
            logger.error(f"Error estimating export size for user {user_id}: {str(e)}")
            # Fallback to conservative estimates
            return ExportService._fallback_size_estimate(data_types)
    
    @staticmethod
    def _fallback_size_estimate(data_types: List[str]) -> int:
        """Fallback size estimation when real data extraction fails."""
        size_estimates = {
            # Original data types
            "user_profile": 1024,  # 1KB
            "documents": 50 * 1024 * 1024,  # 50MB average
            "policy_records": 5 * 1024 * 1024,  # 5MB
            "training_history": 2 * 1024 * 1024,  # 2MB
            "calendar_entries": 1024 * 1024,  # 1MB
            "chat_logs": 10 * 1024 * 1024,  # 10MB
            "audit_trail": 3 * 1024 * 1024,  # 3MB
            # New data types
            "facility_management": 5 * 1024 * 1024,  # 5MB
            "training_programs": 2 * 1024 * 1024,  # 2MB
            "policy_management": 3 * 1024 * 1024,  # 3MB
            "translation_data": 10 * 1024 * 1024,  # 10MB
            "calendar_connections": 1024 * 1024,  # 1MB
            "push_subscriptions": 512 * 1024,  # 512KB
            "export_history": 5 * 1024 * 1024,  # 5MB
            "notes": 1024 * 1024,  # 1MB
        }
        
        total_size = 0
        for data_type in data_types:
            total_size += size_estimates.get(data_type, 0)
        
        # Add 20% overhead for formatting
        return int(total_size * 1.2)
    
    @staticmethod
    def calculate_fee(estimated_size: int) -> float:
        """Calculate fee for exports over 1GB."""
        if estimated_size <= ExportService.FEE_THRESHOLD:
            return 0.0
        
        excess_bytes = estimated_size - ExportService.FEE_THRESHOLD
        excess_gb = excess_bytes / (1024 * 1024 * 1024)
        return round(excess_gb * ExportService.FEE_PER_GB, 2)
    
    @staticmethod
    def validate_export_request(db: Session, user_id: int, format: str, data_types: List[str]) -> Dict:
        """Validate export request and return validation result."""
        # Ensure the user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "valid": False,
                "error": "user_not_found",
                "message": "User not found"
            }

        # Prevent overlapping exports that could create runaway loops
        if ExportService._has_active_export(db, user_id):
            return {
                "valid": False,
                "error": "export_in_progress",
                "message": "An export is already running. Please wait for it to finish before starting another."
            }
        
        # Validate format
        if format not in [ExportFormat.CSV, ExportFormat.PDF, ExportFormat.JSON]:
            return {
                "valid": False,
                "error": "invalid_format",
                "message": "Invalid export format"
            }
        
        if not data_types:
            return {
                "valid": False,
                "error": "no_data_types",
                "message": "Select at least one data type to export"
            }

        # Validate data types
        valid_data_types = [
            "user_profile", "documents", "policy_records", 
            "training_history", "calendar_entries", "chat_logs", "audit_trail",
            "facility_management", "training_programs", "policy_management",
            "translation_data", "calendar_connections", "push_subscriptions",
            "export_history", "notes"
        ]
        invalid_types = [dt for dt in data_types if dt not in valid_data_types]
        if invalid_types:
            return {
                "valid": False,
                "error": "invalid_data_types",
                "message": f"Invalid data types: {', '.join(invalid_types)}"
            }
        
        return {"valid": True}
    
    @staticmethod
    def initiate_export(db: Session, user_id: int, format: str, data_types: List[str]) -> Dict:
        """Initiate export request and start background processing."""
        # Validate request
        validation = ExportService.validate_export_request(db, user_id, format, data_types)
        if not validation["valid"]:
            return validation
        
        # Estimate size and calculate fee
        estimated_size = ExportService.estimate_export_size(db, user_id, data_types)
        fee_amount = ExportService.calculate_fee(estimated_size)
        requires_fee = fee_amount > 0
        
        # Create export request with 72-hour expiration
        export_request = ExportRequest(
            user_id=user_id,
            status=ExportStatus.PENDING,
            format=format,
            data_types=data_types,
            estimated_size=estimated_size,
            requires_fee=requires_fee,
            fee_amount=fee_amount if requires_fee else None,
            download_expires_at=datetime.now() + timedelta(hours=72)  # Extended to 72 hours
        )
        
        db.add(export_request)
        db.commit()
        db.refresh(export_request)
        
        # Start background processing immediately
        processing_started = ExportProcessingService.start_export_processing(export_request.id)
        if not processing_started:
            logger.error(f"Failed to start background processing for export {export_request.id}")
            # Update status to failed
            export_request.status = ExportStatus.FAILED
            export_request.error_message = "Failed to start background processing"
            db.commit()
            
            return {
                "valid": False,
                "error": "processing_failed",
                "message": "Failed to start export processing"
            }
        
        logger.info(f"Initiated export {export_request.id} for user {user_id} with background processing")
        
        return {
            "valid": True,
            "export_id": export_request.id,
            "estimated_size": estimated_size,
            "requires_fee": requires_fee,
            "fee_amount": fee_amount,
            "status": export_request.status
        }
    
    @staticmethod
    def get_export_status(db: Session, export_id: str, user_id: int) -> Optional[Dict]:
        """Get export request status."""
        export_request = db.query(ExportRequest).filter(
            ExportRequest.id == export_id,
            ExportRequest.user_id == user_id
        ).first()
        
        if not export_request:
            return None
        
        return {
            "id": export_request.id,
            "status": export_request.status,
            "format": export_request.format,
            "data_types": export_request.data_types,
            "estimated_size": export_request.estimated_size,
            "actual_size": export_request.actual_size,
            "requires_fee": export_request.requires_fee,
            "fee_amount": export_request.fee_amount,
            "progress_percentage": export_request.progress_percentage,
            "download_expires_at": export_request.download_expires_at,
            "error_message": export_request.error_message,
            "created_at": export_request.created_at,
            "updated_at": export_request.updated_at
        }
    
    @staticmethod
    def get_user_export_history(db: Session, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's export history."""
        exports = db.query(ExportRequest).filter(
            ExportRequest.user_id == user_id
        ).order_by(ExportRequest.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": export.id,
                "status": export.status,
                "format": export.format,
                "data_types": export.data_types,
                "actual_size": export.actual_size or export.estimated_size,
                "created_at": export.created_at,
                "download_expires_at": export.download_expires_at
            }
            for export in exports
        ]
    
    @staticmethod
    def cleanup_expired_exports(db: Session) -> int:
        """Clean up expired export files and update database. Returns count of cleaned exports."""
        expired_exports = db.query(ExportRequest).filter(
            ExportRequest.download_expires_at < datetime.now(),
            ExportRequest.file_path.isnot(None)
        ).all()
        
        cleaned_count = 0
        for export in expired_exports:
            # Remove file if it exists
            if export.file_path and os.path.exists(export.file_path):
                try:
                    os.remove(export.file_path)
                except OSError:
                    pass  # File already removed or permission issue
            
            # Clear file path in database
            export.file_path = None
            export.status = ExportStatus.CANCELLED
            cleaned_count += 1
        
        db.commit()
        return cleaned_count 

    @staticmethod
    def _has_active_export(db: Session, user_id: int) -> bool:
        """Check if the user already has an export running to avoid runaway loops."""
        active_statuses = [ExportStatus.PENDING, ExportStatus.PROCESSING]
        return db.query(ExportRequest).filter(
            ExportRequest.user_id == user_id,
            ExportRequest.status.in_(active_statuses)
        ).count() > 0