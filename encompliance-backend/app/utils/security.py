from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

class CSPMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding Content Security Policy headers to the response.
    
    This middleware helps protect against XSS attacks by specifying which
    dynamic resources are allowed to load.
    
    Content Security Policy (CSP) is an added layer of security that helps to detect and
    mitigate certain types of attacks, including Cross-Site Scripting (XSS) and data injection
    attacks. These attacks are used for everything from data theft to site defacement to
    malware distribution.
    
    Attributes:
        policy (dict): Dictionary containing CSP directives and their sources
        report_only (bool): Whether to use report-only mode or enforcement mode
        
    Example:
        ```python
        app.add_middleware(
            CSPMiddleware,
            default_src=["'self'"],
            script_src=["'self'", "'unsafe-inline'"],
            style_src=["'self'", "'unsafe-inline'"],
            img_src=["'self'", "data:"],
            report_only=True  # Only report violations without blocking
        )
        ```
    """
    
    def __init__(
        self,
        app,
        default_src=None,
        script_src=None,
        style_src=None,
        img_src=None,
        font_src=None,
        connect_src=None,
        frame_src=None,
        report_uri=None,
        report_only=False
    ):
        """
        Initialize the CSP middleware with the specified directives.
        
        Args:
            app: The FastAPI application
            default_src: Default source list for resources (list or string)
            script_src: Allowed sources for JavaScript (list or string)
            style_src: Allowed sources for CSS (list or string)
            img_src: Allowed sources for images (list or string)
            font_src: Allowed sources for fonts (list or string)
            connect_src: Allowed targets for fetch/XHR/WebSocket (list or string)
            frame_src: Allowed sources for frames (list or string)
            report_uri: URI to report CSP violations to (string)
            report_only: Whether to use report-only mode (bool, default False)
        """
        super().__init__(app)
        
        # Default policy (restrictive but functional for most apps)
        self.policy = {
            "default-src": default_src or ["'self'"],
            "script-src": script_src or ["'self'"],
            "style-src": style_src or ["'self'"],
            "img-src": img_src or ["'self'", "data:"],
            "font-src": font_src or ["'self'"],
            "connect-src": connect_src or ["'self'"],
            "frame-src": frame_src or ["'none'"],
            "report-uri": report_uri,
        }
        
        self.report_only = report_only
        
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and add CSP headers to the response.
        
        Args:
            request: The incoming request
            call_next: Function to process the request
            
        Returns:
            Response with added security headers
        """
        response = await call_next(request)
        
        # Build the CSP policy string
        policy_parts = []
        for directive, sources in self.policy.items():
            if sources:
                if isinstance(sources, list):
                    policy_parts.append(f"{directive} {' '.join(sources)}")
                else:
                    policy_parts.append(f"{directive} {sources}")
        
        policy_string = "; ".join(policy_parts)
        
        # Add the CSP header to the response
        header_name = "Content-Security-Policy-Report-Only" if self.report_only else "Content-Security-Policy"
        response.headers[header_name] = policy_string
        
        # Add other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response 