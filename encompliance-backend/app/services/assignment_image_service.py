"""
Assignment Image Service Module

This module provides services for handling assignment image management including
HEIC format conversion, multiple file uploads, and storage tracking.

Key functionalities:
- Multiple image upload with unlimited file sizes
- HEIC to JPEG conversion with quality preservation
- Image labeling and description management
- Storage usage tracking for billing
- File validation and error handling

Dependencies:
- PIL (Pillow): For image processing
- pillow-heif: For HEIC format support
- fastapi: For file upload handling
- sqlalchemy: For database operations

Educational Note: Implements comprehensive image processing pipeline with
support for Apple's HEIC format and automatic conversion to web-compatible
formats while maintaining original files for quality preservation.
"""

import os
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from PIL import Image
import pillow_heif
from app.models.assignment_image import AssignmentImage, ImageType, ConversionStatus
from app.models.task_assignment import TaskAssignment
from app.services.document_service import get_storage_path
from app.services.storage_meter_service import StorageMeterService
import logging

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

logger = logging.getLogger(__name__)

class AssignmentImageService:
    
    ALLOWED_MIME_TYPES = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 
        'image/gif', 'image/heic', 'image/heif'
    ]
    
    HEIC_MIME_TYPES = ['image/heic', 'image/heif']
    
    @staticmethod
    def validate_image_file(file: UploadFile) -> Dict[str, Any]:
        """Validate image file without size restrictions."""
        if file.content_type not in AssignmentImageService.ALLOWED_MIME_TYPES:
            return {
                "valid": False, 
                "error": f"Invalid file type. Allowed types: {', '.join(AssignmentImageService.ALLOWED_MIME_TYPES)}"
            }
        
        return {"valid": True}
    
    @staticmethod
    def validate_image_type(image_type: str) -> bool:
        """Validate image type enum value."""
        return image_type in [e.value for e in ImageType]
    
    @staticmethod
    def convert_heic_to_jpeg(heic_file_path: str, output_path: str, quality: int = 85) -> Dict[str, Any]:
        """Convert HEIC file to JPEG format."""
        try:
            # Open HEIC file using pillow-heif
            with Image.open(heic_file_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as JPEG
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                
                # Get converted file size
                converted_size = os.path.getsize(output_path)
                
                return {
                    "success": True,
                    "converted_path": output_path,
                    "converted_size": converted_size,
                    "original_format": img.format
                }
                
        except Exception as e:
            logger.error(f"HEIC conversion failed: {str(e)}")
            return {
                "success": False,
                "error": f"HEIC conversion failed: {str(e)}"
            }
    
    @staticmethod
    async def upload_multiple_images(
        assignment_id: int,
        image_type: str,
        files: List[UploadFile],
        current_user_id: int,
        db: Session,
        labels: Optional[List[str]] = None,
        descriptions: Optional[List[str]] = None
    ) -> List[AssignmentImage]:
        """Upload multiple images with labels and descriptions."""
        
        # Validate assignment exists
        assignment = db.query(TaskAssignment).filter(TaskAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        facility_id = None
        try:
            if assignment.operational_task:
                facility_id = assignment.operational_task.facility_id
        except Exception:
            facility_id = None
        
        # Validate image type
        if not AssignmentImageService.validate_image_type(image_type):
            raise HTTPException(status_code=400, detail="Invalid image type")
        
        uploaded_images = []
        storage_path = get_storage_path()
        assignment_dir = os.path.join(storage_path, "assignment-images", str(assignment_id), image_type)
        originals_dir = os.path.join(assignment_dir, "originals")
        web_dir = os.path.join(assignment_dir, "web")
        
        # Create directories
        os.makedirs(originals_dir, exist_ok=True)
        os.makedirs(web_dir, exist_ok=True)
        
        total_storage_added = 0
        
        for i, file in enumerate(files):
            try:
                # Validate file
                validation = AssignmentImageService.validate_image_file(file)
                if not validation["valid"]:
                    logger.error(f"File validation failed for {file.filename}: {validation['error']}")
                    continue
                
                # Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                file_extension = os.path.splitext(file.filename)[1].lower()
                base_filename = f"{timestamp}_{current_user_id}_{i}"
                
                # Determine if HEIC conversion is needed
                is_heic = file.content_type in AssignmentImageService.HEIC_MIME_TYPES
                
                if is_heic:
                    # Save original HEIC file
                    original_filename = f"{base_filename}{file_extension}"
                    original_path = os.path.join(originals_dir, original_filename)
                    
                    with open(original_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    
                    original_size = os.path.getsize(original_path)
                    
                    # Convert to JPEG for web
                    web_filename = f"{base_filename}.jpg"
                    web_path = os.path.join(web_dir, web_filename)
                    
                    conversion_result = AssignmentImageService.convert_heic_to_jpeg(
                        original_path, web_path, quality=85
                    )
                    
                    if not conversion_result["success"]:
                        logger.error(f"HEIC conversion failed for {file.filename}: {conversion_result['error']}")
                        # Clean up original file
                        if os.path.exists(original_path):
                            os.remove(original_path)
                        continue
                    
                    web_size = conversion_result["converted_size"]
                    conversion_status = ConversionStatus.COMPLETED.value
                    
                    # Database paths (relative to storage root)
                    db_original_path = os.path.join("assignment-images", str(assignment_id), image_type, "originals", original_filename)
                    db_web_path = os.path.join("assignment-images", str(assignment_id), image_type, "web", web_filename)
                    
                    total_storage_added += original_size + web_size
                    
                else:
                    # Non-HEIC file - save directly to web directory
                    web_filename = f"{base_filename}{file_extension}"
                    web_path = os.path.join(web_dir, web_filename)
                    
                    with open(web_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    
                    web_size = os.path.getsize(web_path)
                    original_size = None
                    conversion_status = ConversionStatus.NONE.value
                    
                    # Database paths
                    db_original_path = None
                    db_web_path = os.path.join("assignment-images", str(assignment_id), image_type, "web", web_filename)
                    
                    total_storage_added += web_size
                
                # Create database record
                image_record = AssignmentImage(
                    assignment_id=assignment_id,
                    image_type=image_type,
                    file_path=db_web_path,
                    original_file_path=db_original_path,
                    file_name=web_filename if not is_heic else web_filename,
                    original_file_name=file.filename,
                    file_size=web_size,
                    original_file_size=original_size,
                    mime_type='image/jpeg' if is_heic else file.content_type,
                    original_mime_type=file.content_type,
                    uploaded_by=current_user_id,
                    label=labels[i] if labels and i < len(labels) and labels[i].strip() else None,
                    description=descriptions[i] if descriptions and i < len(descriptions) and descriptions[i].strip() else None,
                    display_order=i,
                    conversion_status=conversion_status
                )
                
                db.add(image_record)
                uploaded_images.append(image_record)
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                continue
        
        if uploaded_images:
            # Update assignment storage tracking
            assignment.total_image_storage_bytes = (assignment.total_image_storage_bytes or 0) + total_storage_added
            
            try:
                db.commit()
                
                # Refresh all records
                for image in uploaded_images:
                    db.refresh(image)
                    
            except Exception as e:
                db.rollback()
                logger.error(f"Database commit failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to save image records")

            # Log storage usage per image for billing transparency
            for image in uploaded_images:
                try:
                    StorageMeterService.log_consumption(
                        db,
                        facility_id=facility_id,
                        delta_bytes=image.total_storage_bytes,
                        resource_type="assignment_image",
                        resource_id=image.id,
                        user_id=current_user_id,
                        metadata={
                            "assignmentId": assignment_id,
                            "imageType": image.image_type,
                        },
                    )
                except Exception as meter_error:
                    logger.error(f"Failed to log storage usage for assignment image {image.id}: {meter_error}")
        
        return uploaded_images
    
    @staticmethod
    def get_assignment_images(
        assignment_id: int,
        db: Session,
        image_type: Optional[str] = None
    ) -> List[AssignmentImage]:
        """Get images for an assignment, optionally filtered by type."""
        query = db.query(AssignmentImage).filter(AssignmentImage.assignment_id == assignment_id)
        
        if image_type:
            query = query.filter(AssignmentImage.image_type == image_type)
        
        return query.order_by(AssignmentImage.display_order, AssignmentImage.created_at).all()
    
    @staticmethod
    def update_image_metadata(
        assignment_id: int,
        image_id: int,
        updates: Dict[str, Any],
        db: Session
    ) -> AssignmentImage:
        """Update image metadata (label, description, display_order)."""
        image = db.query(AssignmentImage).filter(
            AssignmentImage.id == image_id,
            AssignmentImage.assignment_id == assignment_id
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Update allowed fields
        if "label" in updates:
            image.label = updates["label"][:255] if updates["label"] else None
        
        if "description" in updates:
            image.description = updates["description"]
        
        if "display_order" in updates:
            image.display_order = updates["display_order"]
        
        try:
            db.commit()
            db.refresh(image)
            return image
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update image metadata: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update image")
    
    @staticmethod
    def delete_assignment_image(
        assignment_id: int,
        image_id: int,
        db: Session
    ) -> bool:
        """Delete an assignment image and its files."""
        image = db.query(AssignmentImage).filter(
            AssignmentImage.id == image_id,
            AssignmentImage.assignment_id == assignment_id
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        storage_path = get_storage_path()
        
        try:
            # Delete physical files
            web_file_path = os.path.join(storage_path, image.file_path)
            if os.path.exists(web_file_path):
                os.remove(web_file_path)
            
            if image.original_file_path:
                original_file_path = os.path.join(storage_path, image.original_file_path)
                if os.path.exists(original_file_path):
                    os.remove(original_file_path)
            
            # Update assignment storage tracking
            assignment = db.query(TaskAssignment).filter(TaskAssignment.id == assignment_id).first()
            facility_id = None
            if assignment:
                storage_reduction = image.total_storage_bytes
                assignment.total_image_storage_bytes = max(0, (assignment.total_image_storage_bytes or 0) - storage_reduction)
                try:
                    if assignment.operational_task:
                        facility_id = assignment.operational_task.facility_id
                except Exception:
                    facility_id = None
            
            # Delete database record
            db.delete(image)
            db.commit()

            try:
                StorageMeterService.log_consumption(
                    db,
                    facility_id=facility_id,
                    delta_bytes=-image.total_storage_bytes,
                    resource_type="assignment_image",
                    resource_id=image.id,
                    user_id=image.uploaded_by,
                    metadata={"action": "delete"},
                )
            except Exception as meter_error:
                logger.error(f"Failed to roll back storage usage for assignment image {image.id}: {meter_error}")
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete image: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete image")
    
    @staticmethod
    def get_image_file_path(image: AssignmentImage, original: bool = False) -> str:
        """Get full file system path for an image."""
        storage_path = get_storage_path()
        
        if original and image.original_file_path:
            return os.path.join(storage_path, image.original_file_path)
        else:
            return os.path.join(storage_path, image.file_path) 