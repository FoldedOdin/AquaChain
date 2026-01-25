"""
AquaChain Error Handling Module - Dashboard Overhaul
Comprehensive error handling with meaningful messages, proper HTTP status codes,
correlation IDs, and security-aware error responses.

Requirements: 5.8, 8.6, 10.4, 10.5
"""

import json
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import logging

# Initialize logger
logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standard error codes for consistent error handling"""
    
    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    REQUEST_TOO_LARGE = "REQUEST_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    
    # Business logic errors
    INSUFFICIENT_BUDGET = "INSUFFICIENT_BUDGET"
    WORKFLOW_ERROR = "WORKFLOW_ERROR"
    CONCURRENCY_CONFLICT = "CONCURRENCY_CONFLICT"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    
    # Security errors
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    ACCESS_DENIED = "ACCESS_DENIED"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AquaChainError(Exception):
    """Base exception class for AquaChain errors"""
    
    def __init__(self, message: str, code: ErrorCode, status_code: int = 500,
                 details: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc).isoformat()
        super().__init__(message)


class ValidationError(AquaChainError):
    """Validation error with field-specific details"""
    
    def __init__(self, message: str, field_errors: Optional[List[Dict]] = None, 
                 correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details={'field_errors': field_errors or []},
            correlation_id=correlation_id
        )


class AuthenticationError(AquaChainError):
    """Authentication failure error"""
    
    def __init__(self, message: str = "Authentication failed", 
                 correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code=ErrorCode.AUTHENTICATION_FAILED,
            status_code=401,
            correlation_id=correlation_id
        )


class AuthorizationError(AquaChainError):
    """Authorization failure error"""
    
    def __init__(self, message: str = "Access denied", resource: Optional[str] = None,
                 action: Optional[str] = None, correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code=ErrorCode.AUTHORIZATION_FAILED,
            status_code=403,
            details={'resource': resource, 'action': action},
            correlation_id=correlation_id
        )


class ResourceNotFoundError(AquaChainError):
    """Resource not found error"""
    
    def __init__(self, resource_type: str, resource_id: str, 
                 correlation_id: Optional[str] = None):
        super().__init__(
            message=f"{resource_type} not found",
            code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
            details={'resource_type': resource_type, 'resource_id': resource_id},
            correlation_id=correlation_id
        )


class ConflictError(AquaChainError):
    """Resource conflict error"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None,
                 correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code=ErrorCode.CONFLICT,
            status_code=409,
            details={'resource_type': resource_type},
            correlation_id=correlation_id
        )


class SecurityViolationError(AquaChainError):
    """Security violation error"""
    
    def __init__(self, message: str, violation_type: Optional[str] = None,
                 correlation_id: Optional[str] = None):
        super().__init__(
            message="Security violation detected",  # Don't expose details
            code=ErrorCode.SECURITY_VIOLATION,
            status_code=400,
            details={'violation_type': violation_type},
            correlation_id=correlation_id
        )


class BusinessRuleViolationError(AquaChainError):
    """Business rule violation error"""
    
    def __init__(self, message: str, rule: Optional[str] = None,
                 correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            code=ErrorCode.BUSINESS_RULE_VIOLATION,
            status_code=422,
            details={'rule': rule},
            correlation_id=correlation_id
        )


class ErrorHandler:
    """
    Comprehensive error handler with security-aware responses and audit logging.
    
    Features:
    - Standardized error response format
    - Security-aware error message filtering
    - Correlation ID tracking
    - Audit logging for security events
    - Rate limiting for error responses
    - Proper HTTP status code mapping
    """
    
    def __init__(self, service_name: str, enable_debug: bool = False):
        """
        Initialize error handler
        
        Args:
            service_name: Name of the service for logging
            enable_debug: Whether to include debug information in responses
        """
        self.service_name = service_name
        self.enable_debug = enable_debug
        self.security_keywords = [
            'password', 'secret', 'key', 'token', 'credential',
            'database', 'connection', 'internal', 'system',
            'stack trace', 'exception', 'error', 'debug'
        ]
    
    def handle_error(self, error: Exception, correlation_id: Optional[str] = None,
                    user_id: Optional[str] = None, request_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Handle error and return standardized response
        
        Args:
            error: Exception to handle
            correlation_id: Optional correlation ID
            user_id: Optional user ID for audit logging
            request_context: Optional request context
            
        Returns:
            Standardized error response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # Handle known AquaChain errors
        if isinstance(error, AquaChainError):
            return self._handle_aquachain_error(error, correlation_id, user_id, request_context)
        
        # Handle unknown errors
        return self._handle_unknown_error(error, correlation_id, user_id, request_context)
    
    def _handle_aquachain_error(self, error: AquaChainError, correlation_id: str,
                               user_id: Optional[str], request_context: Optional[Dict]) -> Dict[str, Any]:
        """Handle known AquaChain errors"""
        
        # Log error based on severity
        severity = self._get_error_severity(error.code)
        
        log_data = {
            'service': self.service_name,
            'error_code': error.code.value,
            'message': error.message,
            'status_code': error.status_code,
            'correlation_id': correlation_id,
            'user_id': user_id,
            'timestamp': error.timestamp
        }
        
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error("High severity error occurred", extra=log_data)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error occurred", extra=log_data)
        else:
            logger.info("Low severity error occurred", extra=log_data)
        
        # Security audit logging for security-related errors
        if error.code in [ErrorCode.SECURITY_VIOLATION, ErrorCode.SUSPICIOUS_ACTIVITY, 
                         ErrorCode.AUTHENTICATION_FAILED, ErrorCode.AUTHORIZATION_FAILED]:
            self._log_security_event(error, correlation_id, user_id, request_context)
        
        # Create response
        response = {
            'error': True,
            'code': error.code.value,
            'message': self._sanitize_error_message(error.message),
            'correlation_id': correlation_id,
            'timestamp': error.timestamp
        }
        
        # Add details for non-security errors
        if error.code not in [ErrorCode.SECURITY_VIOLATION, ErrorCode.SUSPICIOUS_ACTIVITY]:
            if error.details:
                response['details'] = self._sanitize_error_details(error.details)
        
        # Add debug information if enabled
        if self.enable_debug and error.code not in [ErrorCode.SECURITY_VIOLATION]:
            response['debug'] = {
                'service': self.service_name,
                'error_type': type(error).__name__
            }
        
        return {
            'statusCode': error.status_code,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': correlation_id,
                'X-Error-Code': error.code.value
            },
            'body': json.dumps(response)
        }
    
    def _handle_unknown_error(self, error: Exception, correlation_id: str,
                             user_id: Optional[str], request_context: Optional[Dict]) -> Dict[str, Any]:
        """Handle unknown/unexpected errors"""
        
        # Log full error details for debugging
        logger.error(
            "Unexpected error occurred",
            service=self.service_name,
            error_type=type(error).__name__,
            error_message=str(error),
            correlation_id=correlation_id,
            user_id=user_id,
            stack_trace=traceback.format_exc() if self.enable_debug else None
        )
        
        # Create generic response (don't expose internal details)
        response = {
            'error': True,
            'code': ErrorCode.INTERNAL_ERROR.value,
            'message': 'An internal error occurred. Please try again later.',
            'correlation_id': correlation_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Add debug information if enabled (be careful not to expose sensitive data)
        if self.enable_debug:
            response['debug'] = {
                'service': self.service_name,
                'error_type': type(error).__name__
            }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': correlation_id,
                'X-Error-Code': ErrorCode.INTERNAL_ERROR.value
            },
            'body': json.dumps(response)
        }
    
    def _get_error_severity(self, error_code: ErrorCode) -> ErrorSeverity:
        """Determine error severity based on error code"""
        
        critical_errors = [
            ErrorCode.SECURITY_VIOLATION,
            ErrorCode.SUSPICIOUS_ACTIVITY,
            ErrorCode.DATABASE_ERROR
        ]
        
        high_errors = [
            ErrorCode.AUTHENTICATION_FAILED,
            ErrorCode.AUTHORIZATION_FAILED,
            ErrorCode.INTERNAL_ERROR,
            ErrorCode.SERVICE_UNAVAILABLE
        ]
        
        medium_errors = [
            ErrorCode.BUSINESS_RULE_VIOLATION,
            ErrorCode.CONCURRENCY_CONFLICT,
            ErrorCode.TIMEOUT,
            ErrorCode.EXTERNAL_SERVICE_ERROR
        ]
        
        if error_code in critical_errors:
            return ErrorSeverity.CRITICAL
        elif error_code in high_errors:
            return ErrorSeverity.HIGH
        elif error_code in medium_errors:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _sanitize_error_message(self, message: str) -> str:
        """Sanitize error message to prevent information disclosure"""
        
        # Convert to lowercase for checking
        message_lower = message.lower()
        
        # Check for security-sensitive keywords
        for keyword in self.security_keywords:
            if keyword in message_lower:
                return "An error occurred. Please contact support with the correlation ID."
        
        # Remove potential file paths
        import re
        message = re.sub(r'[A-Za-z]:\\[^\\]+\\[^\\]+', '[PATH]', message)
        message = re.sub(r'/[^/]+/[^/]+/[^/]+', '[PATH]', message)
        
        # Remove potential IP addresses
        message = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', message)
        
        # Remove potential UUIDs (except correlation IDs which are safe)
        message = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '[ID]', message)
        
        return message
    
    def _sanitize_error_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize error details to prevent information disclosure"""
        
        sanitized = {}
        
        for key, value in details.items():
            # Skip sensitive keys
            if any(keyword in key.lower() for keyword in self.security_keywords):
                continue
            
            # Sanitize string values
            if isinstance(value, str):
                sanitized[key] = self._sanitize_error_message(value)
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list):
                # Only include non-sensitive list items
                sanitized[key] = [item for item in value if isinstance(item, (str, int, float, bool))]
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self._sanitize_error_details(value)
        
        return sanitized
    
    def _log_security_event(self, error: AquaChainError, correlation_id: str,
                           user_id: Optional[str], request_context: Optional[Dict]) -> None:
        """Log security events for audit purposes"""
        
        security_event = {
            'event_type': 'SECURITY_ERROR',
            'service': self.service_name,
            'error_code': error.code.value,
            'correlation_id': correlation_id,
            'user_id': user_id,
            'timestamp': error.timestamp,
            'ip_address': request_context.get('sourceIp') if request_context else None,
            'user_agent': request_context.get('userAgent') if request_context else None,
            'severity': self._get_error_severity(error.code).value
        }
        
        # Log to security audit log
        logger.warning(
            "Security event detected",
            extra={'security_audit': security_event}
        )


def create_lambda_error_response(error: Exception, correlation_id: Optional[str] = None,
                                service_name: str = 'unknown', enable_debug: bool = False) -> Dict[str, Any]:
    """
    Convenience function to create Lambda error response
    
    Args:
        error: Exception to handle
        correlation_id: Optional correlation ID
        service_name: Name of the service
        enable_debug: Whether to include debug information
        
    Returns:
        Lambda-compatible error response
    """
    handler = ErrorHandler(service_name, enable_debug)
    return handler.handle_error(error, correlation_id)


def validate_and_handle_input(validator_func: callable, input_data: Dict[str, Any],
                             correlation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate input and handle validation errors
    
    Args:
        validator_func: Function to validate input
        input_data: Input data to validate
        correlation_id: Optional correlation ID
        
    Returns:
        Validated input data
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        return validator_func(input_data)
    except Exception as e:
        if hasattr(e, 'field_errors'):
            raise ValidationError(
                message="Input validation failed",
                field_errors=e.field_errors,
                correlation_id=correlation_id
            )
        else:
            raise ValidationError(
                message=str(e),
                correlation_id=correlation_id
            )


# Global error handler instance
default_error_handler = ErrorHandler('aquachain-service')