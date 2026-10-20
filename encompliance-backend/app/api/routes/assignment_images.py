"""
Assignment Images API Routes
---------------------------
This module defines the assignment image management API endpoints for the EnCompliance system.
It provides:
- Multiple image upload with HEIC conversion
- Image metadata management (labels, descriptions)
- Image retrieval and display
- Image deletion and cleanup
- Before/after photo comparison

Educational Note: Implements comprehensive image management API with support for
Apple's HEIC format and unlimited file sizes. Includes proper error handling,
validation, and storage tracking for billing purposes.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.assignment_image import AssignmentImage
from app.models.task_assignment import TaskAssignment
from app.models.user import User
from app.services.assignment_image_service import AssignmentImageService
from app.auth.dependencies import get_current_user
from app.schemas.assignment_image import (
    AssignmentImageResponse, 
    AssignmentImageUpdate,
    ImageUploadResponse
)
import logging

router = APIRouter(tags=["assignment-images"])
logger = logging.getLogger(__name__)

@router.post("/assignments/{assignment_id}/images/upload", response_model=ImageUploadResponse)
async def upload_assignment_images(
    assignment_id: int,
    image_type: str = Form(..., description="Image type: before, after, or progress"),
    files: List[UploadFile] = File(..., description="Image files to upload"),
    labels: Optional[List[str]] = Form(None, description="Optional labels for each image"),
    descriptions: Optional[List[str]] = Form(None, description="Optional descriptions for each image"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload multiple images for an assignment with optional labels and descriptions.
    Supports all standard image formats including HEIC with automatic conversion.
    No file size limits - users pay for storage used.
    """
    try:
        logger.info(f"Image upload request for assignment {assignment_id} by user {current_user.id}")
        logger.info(f"Files: {[f.filename for f in files]}, Type: {image_type}")
        
        # Validate assignment access
        assignment = db.query(TaskAssignment).filter(TaskAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Check if user has permission to upload images for this assignment
        # (Either assigned staff member or facility admin)
        if (assignment.staff_member_id != current_user.staff_member_id and 
            not current_user.is_facility_admin):
            raise HTTPException(status_code=403, detail="Not authorized to upload images for this assignment")
        
        # Upload images
        uploaded_images = await AssignmentImageService.upload_multiple_images(
            assignment_id=assignment_id,
            image_type=image_type,
            files=files,
            current_user_id=current_user.id,
            db=db,
            labels=labels,
            descriptions=descriptions
        )
        
        logger.info(f"Successfully uploaded {len(uploaded_images)} images for assignment {assignment_id}")
        
        return ImageUploadResponse(
            message=f"Successfully uploaded {len(uploaded_images)} images",
            uploaded_count=len(uploaded_images),
            images=[AssignmentImageResponse.from_orm(img) for img in uploaded_images]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading images for assignment {assignment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload images"
        )

@router.get("/assignments/{assignment_id}/images", response_model=List[AssignmentImageResponse])
async def get_assignment_images(
    assignment_id: int,
    image_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all images for an assignment, optionally filtered by image type.
    Returns images ordered by display_order and creation date.
    """
    try:
        # Validate assignment access
        assignment = db.query(TaskAssignment).filter(TaskAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Check permissions
        if (assignment.staff_member_id != current_user.staff_member_id and 
            not current_user.is_facility_admin):
            raise HTTPException(status_code=403, detail="Not authorized to view images for this assignment")
        
        images = AssignmentImageService.get_assignment_images(
            assignment_id=assignment_id,
            db=db,
            image_type=image_type
        )
        
        return [AssignmentImageResponse.from_orm(img) for img in images]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving images for assignment {assignment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve images"
        )

@router.get("/assignments/{assignment_id}/images/{image_id}")
async def get_image_file(
    assignment_id: int,
    image_id: int,
    original: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download an image file. Set original=true to download the original HEIC file if available.
    """
    try:
        # Validate assignment access
        assignment = db.query(TaskAssignment).filter(TaskAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Check permissions
        if (assignment.staff_member_id != current_user.staff_member_id and 
            not current_user.is_facility_admin):
            raise HTTPException(status_code=403, detail="Not authorized to access images for this assignment")
        
        # Get image record
        image = db.query(AssignmentImage).filter(
            AssignmentImage.id == image_id,
            AssignmentImage.assignment_id == assignment_id
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Get file path
        file_path = AssignmentImageService.get_image_file_path(image, original=original)
        
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
        logger.error(f"Error serving image file {image_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to serve image file"
        )

@router.put("/assignments/{assignment_id}/images/{image_id}", response_model=AssignmentImageResponse)
async def update_image_metadata(
    assignment_id: int,
    image_id: int,
    update_data: AssignmentImageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update image metadata including label, description, and display order.
    """
    try:
        # Validate assignment access
        assignment = db.query(TaskAssignment).filter(TaskAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Check permissions
        if (assignment.staff_member_id != current_user.staff_member_id and 
            not current_user.is_facility_admin):
            raise HTTPException(status_code=403, detail="Not authorized to modify images for this assignment")
        
        # Update image
        updated_image = AssignmentImageService.update_image_metadata(
            assignment_id=assignment_id,
            image_id=image_id,
            updates=update_data.dict(exclude_unset=True),
            db=db
        )
        
        return AssignmentImageResponse.from_orm(updated_image)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating image metadata {image_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update image metadata"
        )

@router.delete("/assignments/{assignment_id}/images/{image_id}")
async def delete_assignment_image(
    assignment_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an assignment image and its associated files.
    """
    try:
        # Validate assignment access
        assignment = db.query(TaskAssignment).filter(TaskAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Check permissions
        if (assignment.staff_member_id != current_user.staff_member_id and 
            not current_user.is_facility_admin):
            raise HTTPException(status_code=403, detail="Not authorized to delete images for this assignment")
        
        # Delete image
        success = AssignmentImageService.delete_assignment_image(
            assignment_id=assignment_id,
            image_id=image_id,
            db=db
        )
        
        if success:
            return {"message": "Image deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete image")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image {image_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image"
        )

@router.post("/assignments/{assignment_id}/images/reorder")
async def reorder_assignment_images(
    assignment_id: int,
    reorder_data: Dict[str, List[Dict[str, int]]] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update display order for multiple images.
    Expected format: {"images": [{"id": 1, "display_order": 0}, {"id": 2, "display_order": 1}]}
    """
    try:
        # Validate assignment access
        assignment = db.query(TaskAssignment).filter(TaskAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Check permissions
        if (assignment.staff_member_id != current_user.staff_member_id and 
            not current_user.is_facility_admin):
            raise HTTPException(status_code=403, detail="Not authorized to reorder images for this assignment")
        
        if "images" not in reorder_data:
            raise HTTPException(status_code=400, detail="Missing 'images' field in request body")
        
        # Update display orders
        updated_count = 0
        for image_update in reorder_data["images"]:
            if "id" not in image_update or "display_order" not in image_update:
                continue
                
            try:
                AssignmentImageService.update_image_metadata(
                    assignment_id=assignment_id,
                    image_id=image_update["id"],
                    updates={"display_order": image_update["display_order"]},
                    db=db
                )
                updated_count += 1
            except Exception as e:
                logger.warning(f"Failed to update display order for image {image_update['id']}: {str(e)}")
                continue
        
        return {"message": f"Updated display order for {updated_count} images"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering images for assignment {assignment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder images"
        ) 