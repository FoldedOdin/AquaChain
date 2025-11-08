"""
Shared error classes for AquaChain Lambda functions.

This module provides a standardized error hierarchy for consistent
error handling across all Lambda functions.
"""

from typing import Dict, Optional, Any


class AquaChainError(Exception):
    """
    Base exception for AquaChain system.
    
    All custom exceptions should inherit from this class to ensure
    consistent error handling and logging.
    
    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code for client handling
        details: Additional context about the error
    """
    
    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize AquaChainError.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary format for API responses.
        
        Returns:
            Dictionary containing error information
        """
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }


class ValidationError(AquaChainError):
    """
    Raised when input validation fails.
    
    Use this exception when user-provided data doesn't meet
    validation requirements (e.g., invalid format, missing fields,
    out of range values).
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = 'VALIDATION_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ValidationError.
        
        Args:
            message: Description of the validation failure
            error_code: Specific validation error code (defaults to VALIDATION_ERROR)
            details: Additional context (e.g., field name, expected format)
        """
        super().__init__(message, error_code, details)


class AuthenticationError(AquaChainError):
    """
    Raised when authentication fails.
    
    Use this exception when a user cannot be authenticated
    (e.g., invalid credentials, expired token, missing auth header).
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = 'AUTHENTICATION_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize AuthenticationError.
        
        Args:
            message: Description of the authentication failure
            error_code: Specific auth error code (defaults to AUTHENTICATION_ERROR)
            details: Additional context (avoid including sensitive data)
        """
        super().__init__(message, error_code, details)


class AuthorizationError(AquaChainError):
    """
    Raised when authorization fails.
    
    Use this exception when an authenticated user lacks the required
    permissions to perform an action.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = 'AUTHORIZATION_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize AuthorizationError.
        
        Args:
            message: Description of the authorization failure
            error_code: Specific authorization error code
            details: Additional context (e.g., required role, resource)
        """
        super().__init__(message, error_code, details)


class ResourceNotFoundError(AquaChainError):
    """
    Raised when a requested resource doesn't exist.
    
    Use this exception when a database query or resource lookup
    fails to find the requested item.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = 'RESOURCE_NOT_FOUND',
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ResourceNotFoundError.
        
        Args:
            message: Description of what resource was not found
            error_code: Specific not found error code
            details: Additional context (e.g., resource type, ID)
        """
        super().__init__(message, error_code, details)


class DatabaseError(AquaChainError):
    """
    Raised when database operations fail.
    
    Use this exception when DynamoDB or other database operations
    encounter errors (e.g., connection issues, capacity exceeded,
    conditional check failures).
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = 'DATABASE_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize DatabaseError.
        
        Args:
            message: Description of the database error
            error_code: Specific database error code
            details: Additional context (avoid exposing internal details to clients)
        """
        super().__init__(message, error_code, details)


class CacheError(AquaChainError):
    """
    Raised when cache operations fail.
    
    Use this exception when Redis/ElastiCache operations encounter
    errors. These are typically non-fatal and should allow fallback
    to database queries.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = 'CACHE_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize CacheError.
        
        Args:
            message: Description of the cache error
            error_code: Specific cache error code
            details: Additional context
        """
        super().__init__(message, error_code, details)


class RateLimitError(AquaChainError):
    """
    Raised when rate limits are exceeded.
    
    Use this exception when a user or client exceeds allowed
    request rates or quotas.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = 'RATE_LIMIT_EXCEEDED',
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize RateLimitError.
        
        Args:
            message: Description of the rate limit violation
            error_code: Specific rate limit error code
            details: Additional context (e.g., retry_after, limit, current_usage)
        """
        super().__init__(message, error_code, details)


class DeviceError(AquaChainError):
    """
    Raised when IoT device operations fail.
    
    Use this exception for device-specific errors (e.g., device
    offline, invalid device state, provisioning failures).
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = 'DEVICE_ERROR',
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize DeviceError.
        
        Args:
            message: Description of the device error
            error_code: Specific device error code
            details: Additional context (e.g., device_id, device_status)
        """
        super().__init__(message, error_code, details)


class GDPRError(AquaChainError):
    """
    Raised when GDPR operations fail.
    
    Use this exception for GDPR-related errors (e.g., export failures,
    deletion failures, consent management issues).
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = 'GDPR_REQUEST_FAILED',
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize GDPRError.
        
        Args:
            message: Description of the GDPR operation failure
            error_code: Specific GDPR error code
            details: Additional context
        """
        super().__init__(message, error_code, details)
