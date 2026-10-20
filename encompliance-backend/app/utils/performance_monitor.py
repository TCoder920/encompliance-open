import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Set up logger
logger = logging.getLogger(__name__)

class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor and log response times for all API requests."""
    
    def __init__(self, app: ASGIApp, log_threshold_ms: int = 500):
        """
        Initialize the response time middleware.
        
        Args:
            app: The ASGI application
            log_threshold_ms: Response time threshold in milliseconds to log warnings
        """
        super().__init__(app)
        self.log_threshold_ms = log_threshold_ms
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Get request path and method for logging
        path = request.url.path
        method = request.method
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)
            
            # Add X-Process-Time header to response
            response.headers["X-Process-Time"] = str(process_time_ms)
            
            # Log response time
            if process_time_ms > self.log_threshold_ms:
                logger.warning(
                    f"SLOW RESPONSE: {method} {path} took {process_time_ms}ms (status: {response.status_code})"
                )
            else:
                logger.info(
                    f"RESPONSE TIME: {method} {path} took {process_time_ms}ms (status: {response.status_code})"
                )
                
            return response
            
        except Exception as e:
            # Log any exceptions
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)
            
            logger.error(
                f"ERROR RESPONSE: {method} {path} took {process_time_ms}ms - Exception: {str(e)}"
            )
            raise 