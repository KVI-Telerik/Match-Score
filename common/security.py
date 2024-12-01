from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBearer
from itsdangerous import URLSafeTimedSerializer
import secrets
from typing import Optional, Dict, Any
from html import escape
import re
import os
from dotenv import load_dotenv
import logging

load_dotenv()
SECURITY_KEY = os.getenv("SECURITY_KEY")

# Configure logging for security events
logging.basicConfig(level=logging.INFO)
security_logger = logging.getLogger("security")

class SecurityUtils:
    """Utility class for common security operations"""
    
    @staticmethod
    def validate_content_type(content_type: str) -> bool:
        """Validates that the content type is safe"""
        safe_types = ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data']
        return content_type in safe_types
    
    @staticmethod
    def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """Removes potentially dangerous headers"""
        dangerous_headers = ['X-Forwarded-Host', 'X-Forwarded-Protocol']
        return {k: v for k, v in headers.items() if k not in dangerous_headers}

class InputSanitizer:
    """Handles input sanitization with different strategies"""
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitizes a string input"""
        # Remove any HTML tags
        value = escape(value)
        # Remove any SQL injection basic patterns
        value = re.sub(r'([;]|(--)|(\/\*))', '', value)
        # Remove potential command injection characters
        value = re.sub(r'[&|;`$]', '', value)
        # Normalize whitespace
        value = ' '.join(value.split())
        return value
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Specifically sanitizes email inputs"""
        email = InputSanitizer.sanitize_string(email)
        # Additional email-specific sanitization
        email = re.sub(r'[<>]', '', email)
        return email
    
    @staticmethod
    async def sanitize_form_data(request: Request) -> Dict[str, Any]:
        """Sanitizes form data while preserving sensitive fields"""
        form_data = await request.form()
        sanitized_data = {}
        
        for key, value in form_data.items():
            if isinstance(value, str):
                if key == 'email':
                    sanitized_data[key] = InputSanitizer.sanitize_email(value)
                elif key == 'password':
                    # Don't sanitize passwords
                    sanitized_data[key] = value
                else:
                    sanitized_data[key] = InputSanitizer.sanitize_string(value)
            else:
                sanitized_data[key] = value
        
        return sanitized_data

class CSRFProtection:
    """Handles CSRF token generation and validation"""
    
    def __init__(self, secret_key: str):
        if not secret_key:
            raise ValueError("CSRF secret key must be provided")
        self.secret_key = secret_key
        self.serializer = URLSafeTimedSerializer(secret_key)
    
    def generate_token(self) -> str:
        """Generates a new CSRF token"""
        token = secrets.token_urlsafe(32)
        security_logger.info("Generated new CSRF token")
        return self.serializer.dumps(token)
    
    def validate_token(self, token: str) -> bool:
        """Validates a CSRF token"""
        try:
            self.serializer.loads(token, max_age=3600)  # 1 hour expiry
            return True
        except Exception as e:
            security_logger.warning(f"CSRF token validation failed: {str(e)}")
            return False

# class SecurityHeaders:
#     """Defines security headers for responses"""
    
#     @staticmethod
#     def get_security_headers() -> Dict[str, str]:
#         """Returns a dictionary of security headers"""
#         return {
#             "X-Frame-Options": "DENY",
#             "X-Content-Type-Options": "nosniff",
#             "X-XSS-Protection": "1; mode=block",
#             "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
#             "Content-Security-Policy": "default-src 'self'",
#             "Referrer-Policy": "strict-origin-when-cross-origin"
#         }

# Initialize the CSRF protection
csrf = CSRFProtection(SECURITY_KEY)

# Create convenience function for middleware
def verify_csrf_token(request: Request) -> bool:
    """Verifies CSRF token from request"""
    try:
        form_data = request.form()
        csrf_token = form_data.get("csrf_token")
        return csrf.validate_token(csrf_token) if csrf_token else False
    except:
        return False