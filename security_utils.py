#!/usr/bin/env python3
"""
Security utilities for safe data handling and error reporting
Prevents sensitive information exposure in logs and user-facing errors
"""

import re
import hashlib
import logging
from typing import Any, Dict, Optional
import streamlit as st

# Configure secure logger
logger = logging.getLogger(__name__)

class SecurityUtils:
    """Utilities for secure data handling"""
    
    # Patterns for detecting sensitive data
    SENSITIVE_PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{3}-\d{3}-\d{4}\b',  # Phone
        r'\b4\d{12}(?:\d{3})?\b',  # Credit card
        r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\']+)',  # API keys
        r'password["\']?\s*[:=]\s*["\']?([^"\']+)',  # Passwords
    ]
    
    @staticmethod
    def scrub_sensitive_data(text: str) -> str:
        """Remove sensitive data from text"""
        if not text:
            return text
            
        scrubbed = str(text)
        
        for pattern in SecurityUtils.SENSITIVE_PATTERNS:
            scrubbed = re.sub(pattern, '[REDACTED]', scrubbed, flags=re.IGNORECASE)
        
        return scrubbed
    
    @staticmethod
    def generate_error_id(error: Exception) -> str:
        """Generate a safe error ID for tracking"""
        error_str = f"{type(error).__name__}:{str(error)}"
        return hashlib.md5(error_str.encode()).hexdigest()[:8]
    
    @staticmethod
    def safe_error_message(error: Exception, context: str = "") -> str:
        """Generate a safe error message for users"""
        error_id = SecurityUtils.generate_error_id(error)
        if context:
            return f"{context} failed (Error: {error_id})"
        return f"Operation failed (Error: {error_id})"
    
    @staticmethod
    def secure_log_error(error: Exception, context: str = "", level: int = logging.ERROR):
        """Securely log an error without exposing sensitive data"""
        error_id = SecurityUtils.generate_error_id(error)
        safe_message = SecurityUtils.scrub_sensitive_data(str(error))
        logger.log(level, f"Error {error_id} in {context}: {type(error).__name__} - {safe_message[:200]}...")
    
    @staticmethod
    def safe_streamlit_error(error: Exception, context: str = "Operation"):
        """Display a safe error message in Streamlit"""
        safe_message = SecurityUtils.safe_error_message(error, context)
        SecurityUtils.secure_log_error(error, context)
        st.error(f"❌ {safe_message}")
    
    @staticmethod
    def sanitize_user_input(input_data: Any) -> str:
        """Sanitize user input to prevent XSS and injection attacks"""
        if input_data is None:
            return ""
        
        # Convert to string and strip
        clean_data = str(input_data).strip()
        
        # Basic HTML escaping
        clean_data = (clean_data
                     .replace("&", "&amp;")
                     .replace("<", "&lt;")
                     .replace(">", "&gt;")
                     .replace('"', "&quot;")
                     .replace("'", "&#x27;"))
        
        # Remove potentially dangerous characters
        clean_data = re.sub(r'[<>"\']', '', clean_data)
        
        return clean_data[:500]  # Limit length
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format"""
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, str(uuid_str).lower()))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, str(email)))
    
    @staticmethod
    def safe_dict_access(data: Dict, key: str, default: Any = None) -> Any:
        """Safely access dictionary values"""
        try:
            return data.get(key, default) if isinstance(data, dict) else default
        except Exception:
            return default

# Convenience functions for common operations
def safe_error(error: Exception, context: str = "Operation"):
    """Quick function for safe error handling"""
    SecurityUtils.safe_streamlit_error(error, context)

def sanitize_input(input_data: Any) -> str:
    """Quick function for input sanitization"""
    return SecurityUtils.sanitize_user_input(input_data)

def validate_uuid(uuid_str: str) -> bool:
    """Quick UUID validation"""
    return SecurityUtils.validate_uuid(uuid_str)

# Example usage:
"""
try:
    # Some operation that might fail
    result = risky_operation(user_data)
except Exception as e:
    # Instead of: st.error(f"Failed with {user_data}: {e}")
    safe_error(e, "User data processing")
"""