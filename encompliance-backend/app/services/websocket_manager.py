"""
WebSocket Manager for Support Portal
------------------------------------
Manages WebSocket connections for real-time ticket notifications.
"""

import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for support portal."""
    
    def __init__(self):
        # Map of account_id -> Set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Map of WebSocket -> account_id for quick lookup
        self.connection_accounts: Dict[WebSocket, int] = {}
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, account_id: int):
        """Register a WebSocket connection (connection should already be accepted)."""
        # Note: websocket.accept() should be called before this method
        
        async with self.lock:
            if account_id not in self.active_connections:
                self.active_connections[account_id] = set()
            self.active_connections[account_id].add(websocket)
            self.connection_accounts[websocket] = account_id
        
        logger.info(f"WebSocket connected for account {account_id}. Total connections: {len(self.connection_accounts)}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to real-time notifications"
        }, websocket)
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self.lock:
            account_id = self.connection_accounts.pop(websocket, None)
            if account_id and account_id in self.active_connections:
                self.active_connections[account_id].discard(websocket)
                if not self.active_connections[account_id]:
                    del self.active_connections[account_id]
        
        logger.info(f"WebSocket disconnected for account {account_id}. Total connections: {len(self.connection_accounts)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            await self.disconnect(websocket)
    
    async def send_to_account(self, account_id: int, message: dict):
        """Send a message to all connections for a specific account."""
        if account_id not in self.active_connections:
            return
        
        disconnected = []
        async with self.lock:
            connections = list(self.active_connections[account_id])
        
        for connection in connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to account {account_id}: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection)
    
    async def broadcast(self, message: dict, exclude_accounts: Set[int] = None):
        """Broadcast a message to all connected accounts."""
        exclude_accounts = exclude_accounts or set()
        
        disconnected = []
        async with self.lock:
            all_connections = []
            for account_id, connections in self.active_connections.items():
                if account_id not in exclude_accounts:
                    all_connections.extend(connections)
        
        for connection in all_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.connection_accounts)
    
    def get_account_connection_count(self, account_id: int) -> int:
        """Get number of connections for a specific account."""
        return len(self.active_connections.get(account_id, set()))


# Global connection manager instance
manager = ConnectionManager()


async def broadcast_ticket_event(event_type: str, ticket_data: dict, target_account_id: int = None):
    """
    Broadcast a ticket event to relevant WebSocket connections.
    
    Args:
        event_type: Type of event (ticket_created, ticket_updated, ticket_assigned, etc.)
        ticket_data: Ticket data to include in the event
        target_account_id: Specific account to notify (None for broadcast to all)
    """
    message = {
        "type": event_type,
        "data": ticket_data,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if target_account_id:
        # Send to specific account
        await manager.send_to_account(target_account_id, message)
    else:
        # Broadcast to all connected support agents
        await manager.broadcast(message)

