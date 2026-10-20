"""
Logging Routes
------------
This module defines the logging API endpoints for the EnCompliance system.
It provides:
- System log management
- Audit trail tracking
- Error logging
- Performance monitoring
- Log analysis
- Log retention policies
"""

import logging
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, Optional

# Set up router
router = APIRouter()

# Set up logger for client logs
client_logger = logging.getLogger("client")
client_logger.setLevel(logging.INFO)

# Create a file handler that logs to a separate file
file_handler = logging.FileHandler("client_logs.log")
file_handler.setLevel(logging.INFO)

# Create a console handler that logs to the terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handlers
formatter = logging.Formatter('[CLIENT][%(asctime)s][%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
client_logger.addHandler(file_handler)
client_logger.addHandler(console_handler)

# Define the log entry model
class LogEntry(BaseModel):
    level: str
    message: str
    timestamp: Optional[datetime] = None

@router.post("/logs", status_code=200)
async def log_client_message(log_entry: LogEntry, request: Request):
    """Endpoint for receiving logs from the client-side application"""
    # Get client IP for the log
    client_ip = request.client.host if request.client else "unknown"
    
    # Map log level to logging method
    log_methods = {
        'log': client_logger.info,
        'info': client_logger.info,
        'warn': client_logger.warning,
        'error': client_logger.error,
        'debug': client_logger.debug
    }
    
    # Use the appropriate logging method or default to info
    log_method = log_methods.get(log_entry.level, client_logger.info)
    
    # Log the message
    log_method(f"[{client_ip}] {log_entry.message}")
    
    return {"success": True} 