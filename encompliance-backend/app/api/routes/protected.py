"""
Protected Routes
--------------
This module defines the protected API endpoints for the EnCompliance system.
It provides:
- Authentication-required endpoints
- Role-based access control
- Permission validation
- Security middleware
- Access logging
- Security policies
"""

from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(tags=["Protected"])

@router.get("/me", response_model=dict)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get information about the currently authenticated user.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active
    }

@router.get("/protected-resource")
async def get_protected_resource(current_user: User = Depends(get_current_active_user)):
    """
    Example of a protected resource that requires authentication.
    """
    return {
        "message": f"Hello, {current_user.username}! This is a protected resource.",
        "data": "This data is only available to authenticated users."
    } 