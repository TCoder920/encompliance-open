"""
Simple Training Router for Testing
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_simple_training():
    """Simple test endpoint."""
    return {"message": "Simple training router working!", "status": "success"}

@router.get("/health")
async def training_health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "training"} 