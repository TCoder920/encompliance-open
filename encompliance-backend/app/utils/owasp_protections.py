import re
import html
import logging
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, validator
import secrets
import string

logger = logging.getLogger(__name__)

class InputSanitizer:
    """
    Utility class to sanitize user input to prevent common security vulnerabilities
    like SQL Injection, XSS, etc.
    """
    
    @staticmethod
    def sanitize_html(input_string: str) -> str:
        """
        Sanitize HTML input to prevent XSS attacks
        """
        if not input_string:
            return ""
        
        # Basic HTML escaping
        return html.escape(input_string)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format to prevent injection attacks
        """
        if not email:
            return False
            
        # Simple email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filenames to prevent path traversal attacks
        """
        if not filename:
            return ""
            
        # Remove any directory traversal patterns
        sanitized = re.sub(r'[/\\]', '', filename)
        # Remove any null bytes
        sanitized = re.sub(r'\x00', '', sanitized)
        # Limit to safe characters
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', sanitized)
        
        return sanitized
    
    @staticmethod
    def sanitize_sql_query(query: str) -> str:
        """
        Very basic SQL injection prevention - note that parameterized queries
        should be used instead of string interpolation
        """
        if not query:
            return ""
            
        # Replace common SQL injection patterns
        sanitized = re.sub(r'[\'";\-/*]', '_', query)
        return sanitized


class RateLimiter:
    """
    Basic in-memory rate limiter to prevent brute force attacks.
    For production, consider using Redis or another shared cache.
    """
    
    # Track request counts by IP
    request_counts: Dict[str, Dict[str, int]] = {}
    
    @classmethod
    def check_rate_limit(cls, ip_address: str, endpoint: str, max_requests: int = 100, 
                         window_seconds: int = 60) -> bool:
        """
        Check if a request from a specific IP to a specific endpoint is within rate limits
        
        Returns:
            bool: True if within limits, False if rate limited
        """
        # Initialize tracking for this IP if not exists
        if ip_address not in cls.request_counts:
            cls.request_counts[ip_address] = {}
        
        # Initialize tracking for this endpoint if not exists
        if endpoint not in cls.request_counts[ip_address]:
            cls.request_counts[ip_address][endpoint] = 0
            
        # Increment request count
        cls.request_counts[ip_address][endpoint] += 1
        
        # Check if over limit
        if cls.request_counts[ip_address][endpoint] > max_requests:
            logger.warning(f"Rate limit exceeded for IP {ip_address} on endpoint {endpoint}")
            return False
            
        return True


class PasswordPolicy:
    """
    Enforce strong password policies
    """
    
    @staticmethod
    def validate_password_strength(password: str, 
                                  min_length: int = 8,
                                  require_uppercase: bool = True,
                                  require_lowercase: bool = True,
                                  require_numbers: bool = True,
                                  require_special: bool = True) -> Dict[str, Any]:
        """
        Validate password strength against policy
        
        Returns:
            Dict containing 'valid' (bool) and 'message' (str)
        """
        if len(password) < min_length:
            return {
                "valid": False,
                "message": f"Password must be at least {min_length} characters long"
            }
            
        if require_uppercase and not any(c.isupper() for c in password):
            return {
                "valid": False,
                "message": "Password must contain at least one uppercase letter"
            }
            
        if require_lowercase and not any(c.islower() for c in password):
            return {
                "valid": False,
                "message": "Password must contain at least one lowercase letter" 
            }
            
        if require_numbers and not any(c.isdigit() for c in password):
            return {
                "valid": False,
                "message": "Password must contain at least one number"
            }
            
        if require_special and not any(c in string.punctuation for c in password):
            return {
                "valid": False,
                "message": "Password must contain at least one special character"
            }
            
        return {
            "valid": True,
            "message": "Password meets strength requirements"
        }
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """
        Generate a cryptographically secure random password
        """
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class SecurityHeaders:
    """
    Security headers to be added to responses
    """
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """
        Get a dictionary of recommended security headers
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        } 