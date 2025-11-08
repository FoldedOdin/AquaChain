"""
Structured logging module for AquaChain Lambda functions.

This module provides JSON-formatted logging with standard fields for
consistent log aggregation and analysis across all Lambda functions.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted logs with standard fields.
    
    Standard fields included in every log entry:
    - timestamp: ISO 8601 formatted UTC timestamp
    - level: Log level (INFO, WARNING, ERROR, etc.)
    - message: Human-readable log message
    - service: Name of the service/Lambda function
    - request_id: AWS request ID for tracing
    - user_id: User identifier (if available)
    
    Additional custom fields can be passed via kwargs.
    """
    
    def __init__(self, name: str, service: str = "unknown"):
        """
        Initialize the structured logger.
        
        Args:
            name: Logger name (typically __name__)
            service: Service/Lambda function name
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.service = service
        
        # Remove existing handlers to avoid duplicate logs
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
    
    def _format_log_entry(
        self,
        level: str,
        message: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Format a log entry as JSON with standard fields.
        
        Args:
            level: Log level
            message: Log message
            request_id: AWS request ID
            user_id: User identifier
            **kwargs: Additional custom fields
            
        Returns:
            JSON-formatted log string
        """
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level.upper(),
            'message': message,
            'service': self.service,
        }
        
        # Add optional standard fields
        if request_id:
            log_entry['request_id'] = request_id
        if user_id:
            log_entry['user_id'] = user_id
        
        # Add custom fields
        for key, value in kwargs.items():
            if key not in log_entry:
                log_entry[key] = value
        
        return json.dumps(log_entry)
    
    def log(
        self,
        level: str,
        message: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log a message with the specified level.
        
        Args:
            level: Log level (info, warning, error, debug, critical)
            message: Log message
            request_id: AWS request ID
            user_id: User identifier
            **kwargs: Additional custom fields (e.g., device_id, duration_ms, error_code)
        """
        log_entry = self._format_log_entry(level, message, request_id, user_id, **kwargs)
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, log_entry)
    
    def info(
        self,
        message: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log an info-level message.
        
        Args:
            message: Log message
            request_id: AWS request ID
            user_id: User identifier
            **kwargs: Additional custom fields
        """
        self.log('info', message, request_id, user_id, **kwargs)
    
    def warning(
        self,
        message: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log a warning-level message.
        
        Args:
            message: Log message
            request_id: AWS request ID
            user_id: User identifier
            **kwargs: Additional custom fields
        """
        self.log('warning', message, request_id, user_id, **kwargs)
    
    def error(
        self,
        message: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log an error-level message.
        
        Args:
            message: Log message
            request_id: AWS request ID
            user_id: User identifier
            **kwargs: Additional custom fields (e.g., error_code, stack_trace)
        """
        self.log('error', message, request_id, user_id, **kwargs)
    
    def debug(
        self,
        message: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log a debug-level message.
        
        Args:
            message: Log message
            request_id: AWS request ID
            user_id: User identifier
            **kwargs: Additional custom fields
        """
        self.log('debug', message, request_id, user_id, **kwargs)
    
    def critical(
        self,
        message: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log a critical-level message.
        
        Args:
            message: Log message
            request_id: AWS request ID
            user_id: User identifier
            **kwargs: Additional custom fields
        """
        self.log('critical', message, request_id, user_id, **kwargs)


def get_logger(name: str, service: str = "unknown") -> StructuredLogger:
    """
    Factory function to create a StructuredLogger instance.
    
    Args:
        name: Logger name (typically __name__)
        service: Service/Lambda function name
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, service)
