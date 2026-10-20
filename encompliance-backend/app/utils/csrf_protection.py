import secrets
import logging
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional, Set, List
import time

logger = logging.getLogger(__name__)

class CSRFProtection(BaseHTTPMiddleware):
    """
    Middleware for protecting against Cross-Site Request Forgery (CSRF) attacks.
    
    This middleware sets a CSRF token in a cookie and requires that same token
    to be present in the request headers for all unsafe HTTP methods (POST, PUT, DELETE, PATCH).
    
    CSRF attacks occur when a malicious website tricks a user's browser into making
    an unintended request to a site where the user is already authenticated, potentially
    performing actions without the user's consent.
    
    Attributes:
        cookie_name (str): Name of the cookie that stores the CSRF token
        header_name (str): Name of the header expected to contain the token
        cookie_secure (bool): Whether the cookie should only be sent over HTTPS
        cookie_httponly (bool): Whether the cookie should be accessible via JavaScript
        cookie_samesite (str): SameSite attribute for the cookie ('Lax', 'Strict', 'None')
        methods_to_protect (List[str]): HTTP methods that require CSRF protection
        exclude_paths (List[str]): URL paths that should be excluded from CSRF checks
        
    Example:
        ```python
        app.add_middleware(
            CSRFProtection,
            cookie_secure=True,
            exclude_paths=["/api/v1/login", "/api/v1/signup"]
        )
        ```
    """
    
    def __init__(
        self,
        app,
        cookie_name: str = "csrftoken",
        header_name: str = "X-CSRF-Token",
        cookie_secure: bool = True,
        cookie_httponly: bool = True,
        cookie_samesite: str = "Lax",
        methods_to_protect: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None
    ):
        """
        Initialize the CSRF protection middleware.
        
        Args:
            app: The FastAPI application
            cookie_name: Name of the cookie that stores the CSRF token
            header_name: Name of the header expected to contain the token
            cookie_secure: Whether the cookie should only be sent over HTTPS
            cookie_httponly: Whether the cookie should be accessible via JavaScript
            cookie_samesite: SameSite attribute for the cookie
            methods_to_protect: HTTP methods that require CSRF protection
            exclude_paths: URL paths that should be excluded from CSRF checks
        """
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.methods_to_protect = methods_to_protect or ["POST", "PUT", "DELETE", "PATCH"]
        self.exclude_paths = exclude_paths or []
        
    def _is_path_excluded(self, request_path: str) -> bool:
        """
        Check if the request path is in the excluded paths list.
        
        Args:
            request_path: The URL path of the request
            
        Returns:
            bool: True if the path should be excluded from CSRF protection
        """
        return any(request_path.startswith(path) for path in self.exclude_paths)
        
    def _generate_csrf_token(self) -> str:
        """
        Generate a secure CSRF token.
        
        Returns:
            str: A cryptographically secure random token
        """
        return secrets.token_hex(32)
        
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and enforce CSRF protection for unsafe methods.
        
        Args:
            request: The incoming request
            call_next: Function to process the request
            
        Returns:
            Response: The response from the application
            
        Raises:
            HTTPException: 403 Forbidden if CSRF validation fails
        """
        # Skip CSRF protection for excluded paths
        if self._is_path_excluded(request.url.path):
            return await call_next(request)
            
        # Get the existing token from cookies if available
        csrf_token = request.cookies.get(self.cookie_name)
        
        # For unsafe methods, verify the CSRF token
        if request.method in self.methods_to_protect:
            # Get token from the header
            header_token = request.headers.get(self.header_name)
            
            # If no token in cookie or header, or tokens don't match, block the request
            if not csrf_token or not header_token or csrf_token != header_token:
                logger.warning(f"CSRF token validation failed for {request.url.path}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token validation failed"
                )
        
        # Process the request
        response = await call_next(request)
        
        # If no CSRF token exists, generate one and set it in the cookie
        if not csrf_token:
            csrf_token = self._generate_csrf_token()
            
            # Set the CSRF token cookie with proper security settings
            response.set_cookie(
                key=self.cookie_name,
                value=csrf_token,
                httponly=self.cookie_httponly,
                secure=self.cookie_secure,
                samesite=self.cookie_samesite,
                max_age=86400 * 7  # 7 days
            )
            
        return response 