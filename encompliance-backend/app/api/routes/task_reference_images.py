"""
Task Reference Images API Routes
-------------------------------
This module defines the task reference image management API endpoints for the EnCompliance system.
It provides:
- Multiple reference image upload with HEIC conversion
- Image metadata management (labels, descriptions)
- Image retrieval and display
- Image deletion and cleanup
- Image reordering

Educational Note: Implements comprehensive reference image management API with support for
Apple's HEIC format and unlimited file sizes. Includes proper error handling,
validation, and storage tracking for billing purposes.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.task_reference_image import TaskReferenceImage
from app.models.operational_task import OperationalTask
from app.models.user import User
from app.services.task_reference_image_service import TaskReferenceImageService
from app.auth.dependencies import get_current_user, require_facility_admin
from app.schemas.task_reference_image import (
    TaskReferenceImageResponse, 
    TaskReferenceImageUpdate,
    TaskReferenceImageUploadResponse,
    TaskReferenceImageReorderRequest
)
import logging

router = APIRouter(tags=["task-reference-images"])
logger = logging.getLogger(__name__)

@router.post("/operational-tasks/{task_id}/reference-images/upload", response_model=TaskReferenceImageUploadResponse)
async def upload_task_reference_images(
    task_id: int,
    files: List[UploadFile] = File(..., description="Reference image files to upload"),
    labels: Optional[List[str]] = Form(None, description="Optional labels for each image"),
    descriptions: Optional[List[str]] = Form(None, description="Optional descriptions for each image"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """
    Upload multiple reference images for an operational task with optional labels and descriptions.
    Supports all standard image formats including HEIC with automatic conversion.
    No file size limits - users pay for storage used.
    """
    try:
        logger.info(f"Reference image upload request for task {task_id} by user {current_user.id}")
        logger.info(f"Files: {[f.filename for f in files]}")
        
        # Validate task access
        task = db.query(OperationalTask).filter(OperationalTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Operational task not found")
        
        # Check if user has permission to upload images for this task
        # (Facility admin of the task's facility)
        if task.facility_id != current_user.administered_facility.id:
            raise HTTPException(status_code=403, detail="Not authorized to upload images for this task")
        
        # Upload images
        uploaded_images = await TaskReferenceImageService.upload_multiple_images(
            operational_task_id=task_id,
            files=files,
            current_user_id=current_user.id,
            db=db,
            labels=labels,
            descriptions=descriptions
        )
        
        logger.info(f"Successfully uploaded {len(uploaded_images)} reference images for task {task_id}")
        
        return TaskReferenceImageUploadResponse(
            message=f"Successfully uploaded {len(uploaded_images)} reference images",
            uploaded_count=len(uploaded_images),
            images=[TaskReferenceImageResponse.from_orm(img) for img in uploaded_images]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading reference images for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload reference images"
        )

@router.get("/operational-tasks/{task_id}/reference-images", response_model=List[TaskReferenceImageResponse])
async def get_task_reference_images(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """
    Get all reference images for an operational task.
    Returns images ordered by display_order and creation date.
    """
    try:
        # Validate task access
        task = db.query(OperationalTask).filter(OperationalTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Operational task not found")
        
        # Permission: facility admin OR staff member belonging to same facility
        user_facility_id = getattr(current_user, "facility_id", None)
        admin_facility_id = getattr(current_user, "administered_facility", None)
        admin_facility_id = admin_facility_id.id if admin_facility_id else None
        if task.facility_id not in (user_facility_id, admin_facility_id):
            raise HTTPException(status_code=403, detail="Not authorized to view images for this task")
        
        images = TaskReferenceImageService.get_task_reference_images(
            operational_task_id=task_id,
            db=db
        )
        
        return [TaskReferenceImageResponse.from_orm(img) for img in images]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving reference images for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reference images"
        )

@router.get("/operational-tasks/{task_id}/reference-images/{image_id}")
async def get_reference_image_file(
    task_id: int,
    image_id: int,
    original: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """
    Download a reference image file. Set original=true to download the original HEIC file if available.
    """
    try:
        # Validate task access
        task = db.query(OperationalTask).filter(OperationalTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Operational task not found")
        
        # Permission: facility admin or same-facility staff
        user_facility_id = getattr(current_user, "facility_id", None)
        admin_facility_id = getattr(current_user, "administered_facility", None)
        admin_facility_id = admin_facility_id.id if admin_facility_id else None
        if task.facility_id not in (user_facility_id, admin_facility_id):
            raise HTTPException(status_code=403, detail="Not authorized to access images for this task")
        
        # Get image record
        image = db.query(TaskReferenceImage).filter(
            TaskReferenceImage.id == image_id,
            TaskReferenceImage.operational_task_id == task_id
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Reference image not found")
        
        # Get file path
        file_path = TaskReferenceImageService.get_image_file_path(image, original=original)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # Determine filename and media type
        if original and image.original_file_path:
            filename = image.original_file_name
            media_type = image.original_mime_type
        else:
            filename = image.file_name
            media_type = image.mime_type
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving reference image file {image_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to serve image file"
        )

@router.put("/operational-tasks/{task_id}/reference-images/{image_id}", response_model=TaskReferenceImageResponse)
async def update_reference_image_metadata(
    task_id: int,
    image_id: int,
    update_data: TaskReferenceImageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """
    Update reference image metadata (label, description, display_order).
    """
    try:
        # Validate task access
        task = db.query(OperationalTask).filter(OperationalTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Operational task not found")
        
        # Check permissions
        if task.facility_id != current_user.administered_facility.id:
            raise HTTPException(status_code=403, detail="Not authorized to modify images for this task")
        
        # Update image metadata
        updated_image = TaskReferenceImageService.update_image_metadata(
            operational_task_id=task_id,
            image_id=image_id,
            updates=update_data.dict(exclude_unset=True),
            db=db
        )
        
        return TaskReferenceImageResponse.from_orm(updated_image)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reference image metadata {image_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update image metadata"
        )

@router.delete("/operational-tasks/{task_id}/reference-images/{image_id}")
async def delete_reference_image(
    task_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """
    Delete a reference image and its associated files.
    """
    try:
        # Validate task access
        task = db.query(OperationalTask).filter(OperationalTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Operational task not found")
        
        # Check permissions
        if task.facility_id != current_user.administered_facility.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete images for this task")
        
        # Delete image
        success = TaskReferenceImageService.delete_task_reference_image(
            operational_task_id=task_id,
            image_id=image_id,
            db=db
        )
        
        if success:
            return {"message": "Reference image deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete reference image")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reference image {image_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete reference image"
        )

@router.post("/operational-tasks/{task_id}/reference-images/reorder")
async def reorder_reference_images(
    task_id: int,
    reorder_data: TaskReferenceImageReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_facility_admin)
):
    """
    Reorder reference images by updating their display_order values.
    """
    try:
        # Validate task access
        task = db.query(OperationalTask).filter(OperationalTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Operational task not found")
        
        # Check permissions
        if task.facility_id != current_user.administered_facility.id:
            raise HTTPException(status_code=403, detail="Not authorized to reorder images for this task")
        
        # Reorder images
        success = TaskReferenceImageService.reorder_images(
            operational_task_id=task_id,
            image_orders=reorder_data.image_orders,
            db=db
        )
        
        if success:
            return {"message": "Reference images reordered successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reorder reference images")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering reference images for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder reference images"
        ) 