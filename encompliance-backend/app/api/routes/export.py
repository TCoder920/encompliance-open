"""
Export API Routes Module

This module defines the API endpoints for data export functionality.
It handles export requests, status tracking, and download management.

Key functionalities:
- Export quota status checking
- Export size estimation
- Export request initiation
- Export status tracking
- Export history retrieval
- Download management

Dependencies:
- fastapi: For API endpoint definition
- sqlalchemy: For database operations
- app.services: For export business logic
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user, require_facility_admin
from app.models.user import User
from app.models.export_request import ExportRequest
from app.services.export_service import ExportService
from app.services.export_quota_service import ExportQuotaService
from app.utils.access_control import can_access_feature
from app.utils.tiers import get_tier_from_subscription_status
from pydantic import BaseModel
from typing import List, Optional
import logging
from fastapi.responses import FileResponse
from pathlib import Path

# Educational Note: FastAPI router pattern for modular API organization
# Reference: FastAPI documentation - https://fastapi.tiangolo.com/tutorial/bigger-applications/

router = APIRouter(prefix="/api/v1/export", tags=["export"])
logger = logging.getLogger(__name__)

# Request/Response Models
class ExportEstimateRequest(BaseModel):
    data_types: List[str]

class ExportInitiateRequest(BaseModel):
    format: str
    data_types: List[str]

class ExportEstimateResponse(BaseModel):
    estimated_size: int
    estimated_size_mb: float
    requires_fee: bool
    fee_amount: Optional[float]

class ExportStatusResponse(BaseModel):
    id: str
    status: str
    format: str
    data_types: List[str]
    estimated_size: int
    actual_size: Optional[int]
    requires_fee: bool
    fee_amount: Optional[float]
    progress_percentage: int
    download_expires_at: Optional[str]
    error_message: Optional[str]
    created_at: str
    updated_at: str

@router.get("/quota-status")
async def get_quota_status(
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """
    Get user's current export quota status (facility admins only).
    
    Returns quota information including usage, availability, and next reset date.
    Team members cannot access data export functionality.
    """
    try:
        quota_status = ExportQuotaService.get_quota_status(db, current_user.id)
        quota_status.update({
            "exports_limit": None,
            "available": True,
            "unlimited": True,
            "message": "Exports are now unlimited for all facility administrators."
        })
        
        return {
            "quota": quota_status,
            "subscription": {
                "tier": current_user.subscription_status or "free",
                "is_active": current_user.is_active,
                "end_date": current_user.subscription_end_date
            },
            "has_access": True
        }
    except Exception as e:
        logger.error(f"Error getting quota status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota status"
        )

@router.post("/estimate-size", response_model=ExportEstimateResponse)
async def estimate_export_size(
    request: ExportEstimateRequest,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """
    Estimate export size and calculate fees for selected data types.
    
    Provides size estimation and fee calculation before initiating export.
    """
    try:
        estimated_size = ExportService.estimate_export_size(db, current_user.id, request.data_types)
        fee_amount = ExportService.calculate_fee(estimated_size)
        
        return ExportEstimateResponse(
            estimated_size=estimated_size,
            estimated_size_mb=round(estimated_size / (1024 * 1024), 2),
            requires_fee=fee_amount > 0,
            fee_amount=fee_amount if fee_amount > 0 else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating export size for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to estimate export size"
        )

@router.post("/initiate")
async def initiate_export(
    request: ExportInitiateRequest,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """
    Initiate a new export request.
    
    Creates export request and returns request ID for tracking.
    """
    try:
        result = ExportService.initiate_export(
            db, current_user.id, request.format, request.data_types
        )
        
        if not result["valid"]:
            error = result.get("error")
            status_code_map = {
                "export_in_progress": status.HTTP_409_CONFLICT,
            }
            status_code = status_code_map.get(error, status.HTTP_400_BAD_REQUEST)
            raise HTTPException(
                status_code=status_code,
                detail=result
            )
        
        return {
            "export_id": result["export_id"],
            "estimated_size": result["estimated_size"],
            "requires_fee": result["requires_fee"],
            "fee_amount": result["fee_amount"],
            "status": result["status"],
            "message": "Export request initiated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating export for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate export"
        )

@router.get("/status/{export_id}", response_model=ExportStatusResponse)
async def get_export_status(
    export_id: str,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """
    Get export request status and progress.
    
    Returns current status, progress, and download information.
    """
    try:
        export_status = ExportService.get_export_status(db, export_id, current_user.id)
        
        if not export_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export request not found"
            )
        
        return ExportStatusResponse(
            id=export_status["id"],
            status=export_status["status"],
            format=export_status["format"],
            data_types=export_status["data_types"],
            estimated_size=export_status["estimated_size"],
            actual_size=export_status["actual_size"],
            requires_fee=export_status["requires_fee"],
            fee_amount=export_status["fee_amount"],
            progress_percentage=export_status["progress_percentage"],
            download_expires_at=export_status["download_expires_at"].isoformat() if export_status["download_expires_at"] else None,
            error_message=export_status["error_message"],
            created_at=export_status["created_at"].isoformat(),
            updated_at=export_status["updated_at"].isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export status for user {current_user.id}, export {export_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve export status"
        )

@router.get("/history")
async def get_export_history(
    limit: int = 10,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """
    Get user's export history.
    
    Returns list of previous export requests with basic information.
    """
    try:
        history = ExportService.get_user_export_history(db, current_user.id, limit)
        
        # Format dates for JSON serialization
        for export in history:
            export["created_at"] = export["created_at"].isoformat()
            if export["download_expires_at"]:
                export["download_expires_at"] = export["download_expires_at"].isoformat()
        
        return {
            "exports": history,
            "total": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting export history for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve export history"
        )

@router.get("/download/{export_id}")
async def download_export(
    export_id: str,
    current_user: User = Depends(require_facility_admin),
    db: Session = Depends(get_db)
):
    """
    Download completed export file with secure streaming.
    
    Returns actual file content with proper headers and 72-hour expiration validation.
    """
    try:
        export_status = ExportService.get_export_status(db, export_id, current_user.id)
        
        if not export_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export request not found"
            )
        
        if export_status["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Export is not ready for download"
            )
        
        # Check if download has expired (72-hour window)
        from datetime import datetime
        if export_status["download_expires_at"]:
            expiry_time = export_status["download_expires_at"]
            if isinstance(expiry_time, str):
                expiry_time = datetime.fromisoformat(expiry_time.replace('Z', '+00:00'))
            
            if expiry_time < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="Download link has expired (72-hour limit)"
                )
        
        # Get file path from export request
        export_request = db.query(ExportRequest).filter(
            ExportRequest.id == export_id,
            ExportRequest.user_id == current_user.id
        ).first()
        
        if not export_request or not export_request.file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found"
            )
        
        # Verify file exists
        file_path = Path(export_request.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file no longer available"
            )
        
        # Determine MIME type based on format
        mime_types = {
            "json": "application/json",
            "csv": "application/zip",
            "pdf": "application/pdf"
        }
        
        media_type = mime_types.get(export_request.format.lower(), "application/octet-stream")
        filename = f"data_export_{export_id}.{export_request.format.lower()}"
        
        # Return file with proper headers for streaming
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export for user {current_user.id}, export {export_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process download request"
        )

@router.post("/request-additional")
async def request_additional_export(
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request additional export beyond quarterly limit.
    
    Creates support ticket for manual review and approval.
    """
    return {
        "support_ticket_id": None,
        "message": "Exports are now unlimited—no additional approval is required.",
        "reason": reason,
        "unlimited": True
    }