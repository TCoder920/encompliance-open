"""
Maryland COMAR Integration Routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.services.maryland_comar_service import MarylandCOMARService
from app.services.maryland_regulation_processor import MarylandRegulationProcessor
from app.core.config import get_settings
from app.models.regulation import Regulation
from app.models.user import User
import logging

router = APIRouter(prefix="/maryland", tags=["maryland-comar"])
logger = logging.getLogger(__name__)
settings = get_settings()

@router.post("/sync-comar-regulations")
async def sync_comar_regulations(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sync Maryland COMAR childcare regulations
    
    This endpoint extracts the latest childcare regulations from Maryland's
    COMAR system and integrates them into the application.
    """
    
    # Check if user has admin permissions
    if current_user.user_role not in ["FACILITY_ADMIN", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can sync regulations"
        )
    
    try:
        # Start background task for regulation sync
        background_tasks.add_task(
            _sync_comar_regulations_background,
            settings.PDF_STORAGE_PATH
        )
        
        return {
            "message": "Maryland COMAR regulation sync started",
            "status": "processing",
            "expected_regulations": 4
        }
        
    except Exception as e:
        logger.error(f"Error starting COMAR sync: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start regulation sync"
        )

@router.post("/sync-comar-regulations-immediate")
async def sync_comar_regulations_immediate(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Immediately sync Maryland COMAR childcare regulations (for testing)
    """
    
    # Check if user has admin permissions
    if current_user.user_role not in ["FACILITY_ADMIN", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can sync regulations"
        )
    
    try:
        logger.info("Starting immediate Maryland COMAR regulation sync")
        
        # Extract regulations from COMAR
        comar_service = MarylandCOMARService()
        regulations = comar_service.extract_regulations_sync()
        
        logger.info(f"Extracted {len(regulations)} regulations from COMAR")
        
        # Process regulations and create PDFs
        processor = MarylandRegulationProcessor(settings.PDF_STORAGE_PATH)
        processed_regs = processor.process_regulations(regulations, db)
        
        logger.info(f"Successfully processed {len(processed_regs)} Maryland regulations")
        
        return {
            "message": "Maryland COMAR regulation sync completed",
            "status": "completed",
            "regulations_processed": len(processed_regs),
            "regulations": processed_regs
        }
        
    except Exception as e:
        logger.error(f"Error in immediate COMAR sync: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync regulations: {str(e)}"
        )

async def _sync_comar_regulations_background(storage_path: str):
    """Background task to sync COMAR regulations"""
    
    try:
        logger.info("Starting Maryland COMAR regulation sync")
        
        # Get database session
        from app.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Extract regulations from COMAR
            comar_service = MarylandCOMARService()
            regulations = await comar_service.extract_childcare_regulations()
            
            logger.info(f"Extracted {len(regulations)} regulations from COMAR")
            
            # Process regulations and create PDFs
            processor = MarylandRegulationProcessor(storage_path)
            processed_regs = processor.process_regulations(regulations, db)
            
            logger.info(f"Successfully processed {len(processed_regs)} Maryland regulations")
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error in background COMAR sync: {str(e)}")

@router.get("/comar-status")
async def get_comar_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of Maryland COMAR integration"""
    
    # Count Maryland regulations
    maryland_count = db.query(Regulation).filter(
        Regulation.state_territory == "Maryland"
    ).count()
    
    # Get list of Maryland regulations
    maryland_regs = db.query(Regulation).filter(
        Regulation.state_territory == "Maryland"
    ).all()
    
    regulation_details = []
    for reg in maryland_regs:
        regulation_details.append({
            "id": reg.id,
            "title": reg.document_title,
            "filename": reg.file_name,
            "last_updated": reg.last_updated.isoformat() if reg.last_updated else None,
            "facility_types": [ft.name for ft in reg.facility_types]
        })
    
    return {
        "maryland_regulations_count": maryland_count,
        "regulations": regulation_details,
        "available_subtitles": [
            "Family Child Care (13A.15)",
            "Child Care Centers (13A.16)", 
            "Child Care - Letters of Compliance (13A.17)",
            "Large Family Child Care Homes (13A.18)"
        ],
        "expected_facility_types": [
            "Family Child Care Home",
            "Child Care Center",
            "Other Facility Type", 
            "Group/Large Child Care Home"
        ]
    }

@router.delete("/clear-maryland-regulations")
async def clear_maryland_regulations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all Maryland regulations (for testing purposes)"""
    
    # Check if user has admin permissions
    if current_user.user_role not in ["FACILITY_ADMIN", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can clear regulations"
        )
    
    try:
        # Delete Maryland regulations from database
        deleted_count = db.query(Regulation).filter(
            Regulation.state_territory == "Maryland"
        ).delete()
        
        db.commit()
        
        # Also delete PDF files
        import os
        maryland_dir = os.path.join(settings.PDF_STORAGE_PATH, "regulations_by_state", "Maryland")
        if os.path.exists(maryland_dir):
            for filename in os.listdir(maryland_dir):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(maryland_dir, filename)
                    os.remove(file_path)
                    logger.info(f"Deleted PDF file: {filename}")
        
        return {
            "message": f"Cleared {deleted_count} Maryland regulations",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing Maryland regulations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear regulations: {str(e)}"
        ) 