"""
Task Reference Image Service Module

This module provides services for handling task reference image management including
HEIC format conversion, multiple file uploads, and storage tracking.

Key functionalities:
- Multiple reference image upload with unlimited file sizes
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
from app.models.task_reference_image import TaskReferenceImage, ConversionStatus
from app.models.operational_task import OperationalTask
from app.services.document_service import get_storage_path
from app.services.storage_meter_service import StorageMeterService
import logging

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

logger = logging.getLogger(__name__)

class TaskReferenceImageService:
    
    ALLOWED_MIME_TYPES = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 
        'image/gif', 'image/heic', 'image/heif'
    ]
    
    HEIC_MIME_TYPES = ['image/heic', 'image/heif']
    
    @staticmethod
    def validate_image_file(file: UploadFile) -> Dict[str, Any]:
        """Validate image file without size restrictions."""
        if file.content_type not in TaskReferenceImageService.ALLOWED_MIME_TYPES:
            return {
                "valid": False, 
                "error": f"Invalid file type. Allowed types: {', '.join(TaskReferenceImageService.ALLOWED_MIME_TYPES)}"
            }
        
        return {"valid": True}
    
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
        operational_task_id: int,
        files: List[UploadFile],
        current_user_id: int,
        db: Session,
        labels: Optional[List[str]] = None,
        descriptions: Optional[List[str]] = None
    ) -> List[TaskReferenceImage]:
        """Upload multiple reference images with labels and descriptions."""
        
        # Validate task exists
        task = db.query(OperationalTask).filter(OperationalTask.id == operational_task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Operational task not found")
        facility_id = task.facility_id
        
        uploaded_images = []
        storage_path = get_storage_path()
        task_dir = os.path.join(storage_path, "task-reference-images", str(operational_task_id))
        originals_dir = os.path.join(task_dir, "originals")
        web_dir = os.path.join(task_dir, "web")
        
        # Create directories
        os.makedirs(originals_dir, exist_ok=True)
        os.makedirs(web_dir, exist_ok=True)
        
        for i, file in enumerate(files):
            try:
                # Validate file
                validation = TaskReferenceImageService.validate_image_file(file)
                if not validation["valid"]:
                    logger.error(f"File validation failed for {file.filename}: {validation['error']}")
                    continue
                
                # Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                file_extension = os.path.splitext(file.filename)[1].lower()
                base_filename = f"{timestamp}_{current_user_id}_{i}"
                
                # Determine if HEIC conversion is needed
                is_heic = file.content_type in TaskReferenceImageService.HEIC_MIME_TYPES
                
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
                    
                    conversion_result = TaskReferenceImageService.convert_heic_to_jpeg(
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
                    db_original_path = os.path.join("task-reference-images", str(operational_task_id), "originals", original_filename)
                    db_web_path = os.path.join("task-reference-images", str(operational_task_id), "web", web_filename)
                    
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
                    db_web_path = os.path.join("task-reference-images", str(operational_task_id), "web", web_filename)
                
                # Create database record
                image_record = TaskReferenceImage(
                    operational_task_id=operational_task_id,
                    image_type="reference",
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
            try:
                db.commit()
                
                # Refresh all records
                for image in uploaded_images:
                    db.refresh(image)
                    
            except Exception as e:
                db.rollback()
                logger.error(f"Database commit failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to save image records")

            for image in uploaded_images:
                try:
                    StorageMeterService.log_consumption(
                        db,
                        facility_id=facility_id,
                        delta_bytes=image.total_storage_bytes,
                        resource_type="task_reference_image",
                        resource_id=image.id,
                        user_id=current_user_id,
                        metadata={
                            "operationalTaskId": operational_task_id,
                            "label": image.label,
                        },
                    )
                except Exception as meter_error:
                    logger.error(f"Failed to log storage usage for task reference image {image.id}: {meter_error}")
        
        return uploaded_images
    
    @staticmethod
    def get_task_reference_images(
        operational_task_id: int,
        db: Session
    ) -> List[TaskReferenceImage]:
        """Get reference images for a task."""
        return db.query(TaskReferenceImage).filter(
            TaskReferenceImage.operational_task_id == operational_task_id
        ).order_by(TaskReferenceImage.display_order, TaskReferenceImage.created_at).all()
    
    @staticmethod
    def update_image_metadata(
        operational_task_id: int,
        image_id: int,
        updates: Dict[str, Any],
        db: Session
    ) -> TaskReferenceImage:
        """Update image metadata (label, description, display_order)."""
        image = db.query(TaskReferenceImage).filter(
            TaskReferenceImage.id == image_id,
            TaskReferenceImage.operational_task_id == operational_task_id
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
    def delete_task_reference_image(
        operational_task_id: int,
        image_id: int,
        db: Session
    ) -> bool:
        """Delete a task reference image and its files."""
        image = db.query(TaskReferenceImage).filter(
            TaskReferenceImage.id == image_id,
            TaskReferenceImage.operational_task_id == operational_task_id
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
            
            facility_id = None
            try:
                if image.operational_task:
                    facility_id = image.operational_task.facility_id
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
                    resource_type="task_reference_image",
                    resource_id=image.id,
                    user_id=image.uploaded_by,
                    metadata={"action": "delete"},
                )
            except Exception as meter_error:
                logger.error(f"Failed to roll back storage usage for task reference image {image.id}: {meter_error}")
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete image: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete image")
    
    @staticmethod
    def get_image_file_path(image: TaskReferenceImage, original: bool = False) -> str:
        """Get full file system path for an image."""
        storage_path = get_storage_path()
        
        if original and image.original_file_path:
            return os.path.join(storage_path, image.original_file_path)
        else:
            return os.path.join(storage_path, image.file_path)
    
    @staticmethod
    def reorder_images(
        operational_task_id: int,
        image_orders: List[Dict[str, int]],
        db: Session
    ) -> bool:
        """Reorder task reference images by updating display_order."""
        try:
            for order_data in image_orders:
                image_id = order_data["id"]
                display_order = order_data["display_order"]
                
                image = db.query(TaskReferenceImage).filter(
                    TaskReferenceImage.id == image_id,
                    TaskReferenceImage.operational_task_id == operational_task_id
                ).first()
                
                if image:
                    image.display_order = display_order
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to reorder images: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to reorder images") 