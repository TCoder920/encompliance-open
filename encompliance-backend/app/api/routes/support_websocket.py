"""
WebSocket Routes for Support Portal
-----------------------------------
Real-time WebSocket endpoints for ticket notifications.
"""

import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_support_portal_db
from app.models.support_portal_account import SupportPortalAccount
from app.auth.support_portal_auth_utils import get_current_support_account
from app.services.websocket_manager import manager
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


async def verify_websocket_token(websocket: WebSocket, token: str) -> SupportPortalAccount:
    """Verify WebSocket connection token. Connection must be accepted before calling this."""
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
        raise ValueError("Token required")
    
    # Get database session
    db = next(get_support_portal_db())
    try:
        # Verify token and get account
        from app.auth.support_portal_auth_utils import verify_token
        account_id = verify_token(token)
        
        if not account_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            raise ValueError("Invalid token")
        
        account = db.query(SupportPortalAccount).filter(SupportPortalAccount.id == account_id).first()
        if not account:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Account not found")
            raise ValueError("Account not found")
        
        return account
    finally:
        db.close()


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time ticket notifications.
    
    Connect with: ws://host:port/api/v1/support/ws/notifications?token=<jwt_token>
    """
    account = None
    try:
        # Accept the WebSocket connection first (required before any operations)
        await websocket.accept()
        
        # Get token from query parameter
        if not token:
            # Try to get from query string
            query_params = dict(websocket.query_params)
            token = query_params.get("token")
        
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
            return
        
        # Verify token and get account (connection is already accepted)
        account = await verify_websocket_token(websocket, token)
        
        # Connect to manager (this will send welcome message)
        await manager.connect(websocket, account.id)
        
        # Keep connection alive and handle incoming messages
        try:
            while True:
                # Wait for messages from the client to keep the socket alive
                data = await websocket.receive_text()
                # Optional: handle incoming messages or keep-alive pings
        except WebSocketDisconnect:
            logger.info("Client disconnected")
            pass
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
    finally:
        if account:
            await manager.disconnect(websocket)

