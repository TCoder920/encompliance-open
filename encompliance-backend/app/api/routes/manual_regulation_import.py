"""
Manual Regulation Import Routes

This module provides endpoints for manually importing regulations
for testing and administrative purposes.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.regulation import Regulation
from app.models.facility_type import FacilityType
from app.core.config import get_settings
from typing import Optional, List
import logging
import os
import shutil
from datetime import datetime

router = APIRouter(prefix="/manual-import", tags=["manual-import"])
logger = logging.getLogger(__name__)
settings = get_settings()

@router.post("/regulation")
async def manual_import_regulation(
    title: str = Form(...),
    state_territory: str = Form(...),
    facility_type: str = Form(...),
    document_type: str = Form("Regulation"),
    last_updated: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually import a regulation document
    
    This endpoint allows administrators to manually upload regulation
    documents for testing or when automated extraction is not available.
    """
    
    # Check if user has admin permissions
    if current_user.user_role not in ["FACILITY_ADMIN", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can import regulations"
        )
    
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Create state directory if it doesn't exist
        state_dir = os.path.join(settings.PDF_STORAGE_PATH, "regulations_by_state", state_territory)
        os.makedirs(state_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{state_territory}_{timestamp}_{file.filename}"
        filepath = os.path.join(state_dir, filename)
        
        # Save file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse last_updated date
        last_updated_date = None
        if last_updated:
            try:
                last_updated_date = datetime.strptime(last_updated, '%m/%d/%Y').date()
            except ValueError:
                try:
                    last_updated_date = datetime.strptime(last_updated, '%Y-%m-%d').date()
                except ValueError:
                    logger.warning(f"Could not parse last_updated date: {last_updated}")
        
        # Create regulation record
        regulation = Regulation(
            state_territory=state_territory,
            document_title=title,
            document_type=document_type,
            file_name=filename,
            last_updated=last_updated_date
        )
        
        db.add(regulation)
        db.flush()  # Get ID without committing
        
        # Associate with facility type
        if facility_type:
            facility_type_obj = db.query(FacilityType).filter(
                FacilityType.name == facility_type
            ).first()
            
            if not facility_type_obj:
                # Create new facility type if it doesn't exist
                facility_type_obj = FacilityType(name=facility_type)
                db.add(facility_type_obj)
                db.flush()
                logger.info(f"Created new facility type: {facility_type}")
            
            regulation.facility_types.append(facility_type_obj)
        
        db.commit()
        
        logger.info(f"Successfully imported regulation: {filename}")
        
        return {
            "message": "Regulation imported successfully",
            "regulation_id": regulation.id,
            "filename": filename,
            "title": title,
            "state_territory": state_territory,
            "facility_type": facility_type
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing regulation: {str(e)}")
        
        # Clean up file if it was created
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import regulation: {str(e)}"
        )

@router.get("/test-maryland-structure")
async def test_maryland_structure(
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint to verify Maryland directory structure and create sample data
    """
    
    # Check if user has admin permissions
    if current_user.user_role not in ["FACILITY_ADMIN", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access test endpoints"
        )
    
    try:
        maryland_dir = os.path.join(settings.PDF_STORAGE_PATH, "regulations_by_state", "Maryland")
        
        # Create directory if it doesn't exist
        os.makedirs(maryland_dir, exist_ok=True)
        
        # Check directory contents
        contents = []
        if os.path.exists(maryland_dir):
            contents = os.listdir(maryland_dir)
        
        return {
            "maryland_directory": maryland_dir,
            "directory_exists": os.path.exists(maryland_dir),
            "contents": contents,
            "expected_files": [
                "MD_COMAR_13A15_Family_Child_Care.pdf",
                "MD_COMAR_13A16_Child_Care_Centers.pdf", 
                "MD_COMAR_13A17_Letters_of_Compliance.pdf",
                "MD_COMAR_13A18_Large_Family_Child_Care_Homes.pdf"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error testing Maryland structure: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test Maryland structure: {str(e)}"
        ) 