"""
Error handler decorator for Lambda functions.

This module provides a decorator that standardizes error handling
across all Lambda functions, ensuring consistent error responses
and proper logging.
"""

import json
import logging
import traceback
from functools import wraps
from typing import Callable, Dict, Any

from errors import (
    AquaChainError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    DatabaseError,
    CacheError,
    RateLimitError,
    DeviceError,
    GDPRError,
    AuditServiceError
)

# Import structured logging
from structured_logger import get_logger

# Configure structured logger
logger = get_logger(__name__, service='error-handler')


def handle_errors(func: Callable) -> Callable:
    """
    Decorator for Lambda functions to handle errors consistently.
    
    This decorator:
    - Catches all exceptions and maps them to appropriate HTTP status codes
    - Logs errors with appropriate severity levels
    - Ensures sensitive error details are not exposed to clients
    - Returns standardized error response format
    
    Usage:
        @handle_errors
        def lambda_handler(event, context):
            # Your Lambda function code
            pass
    
    Args:
        func: The Lambda handler function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    
    @wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Wrapper function that handles errors.
        
        Args:
            event: Lambda event object
            context: Lambda context object
            
        Returns:
            Lambda response with statusCode and body
        """
        request_id = context.request_id if hasattr(context, 'request_id') else 'unknown'
        
        try:
            # Execute the Lambda function
            result = func(event, context)
            
            # If result is already a proper Lambda response, return it
            if isinstance(result, dict) and 'statusCode' in result:
                return result
            
            # Otherwise, wrap it in a success response
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True
                },
                'body': json.dumps(result) if not isinstance(result, str) else result
            }
            
        except ValidationError as e:
            logger.warning(
                f"Validation error: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                }
            )
            return _create_error_response(400, e, request_id)
            
        except AuthenticationError as e:
            logger.warning(
                f"Authentication error: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'request_id': request_id
                }
            )
            return _create_error_response(401, e, request_id)
            
        except AuthorizationError as e:
            logger.warning(
                f"Authorization error: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                }
            )
            return _create_error_response(403, e, request_id)
            
        except ResourceNotFoundError as e:
            logger.info(
                f"Resource not found: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                }
            )
            return _create_error_response(404, e, request_id)
            
        except RateLimitError as e:
            logger.warning(
                f"Rate limit exceeded: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                }
            )
            return _create_error_response(429, e, request_id)
            
        except (DatabaseError, CacheError, DeviceError, GDPRError) as e:
            # Log full error details for internal errors
            logger.error(
                f"Service error: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                },
                exc_info=True
            )
            # Return sanitized error to client
            sanitized_error = AquaChainError(
                message='An internal error occurred. Please try again later.',
                error_code='INTERNAL_ERROR',
                details={'request_id': request_id}
            )
            return _create_error_response(500, sanitized_error, request_id)
            
        except AquaChainError as e:
            # Catch any other custom errors
            logger.error(
                f"AquaChain error: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                },
                exc_info=True
            )
            sanitized_error = AquaChainError(
                message='An internal error occurred. Please try again later.',
                error_code='INTERNAL_ERROR',
                details={'request_id': request_id}
            )
            return _create_error_response(500, sanitized_error, request_id)
            
        except Exception as e:
            # Catch all unexpected errors
            logger.exception(
                f"Unexpected error: {str(e)}",
                extra={
                    'request_id': request_id,
                    'error_type': type(e).__name__
                }
            )
            # Never expose internal error details to clients
            sanitized_error = AquaChainError(
                message='An unexpected error occurred. Please try again later.',
                error_code='INTERNAL_ERROR',
                details={'request_id': request_id}
            )
            return _create_error_response(500, sanitized_error, request_id)
    
    return wrapper


def _create_error_response(
    status_code: int,
    error: AquaChainError,
    request_id: str
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        error: AquaChainError instance
        request_id: Request ID for tracking
        
    Returns:
        Lambda response dictionary
    """
    error_body = error.to_dict()
    error_body['request_id'] = request_id
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True
        },
        'body': json.dumps(error_body)
    }


def handle_errors_async(func: Callable) -> Callable:
    """
    Decorator for async Lambda functions to handle errors consistently.
    
    This is the async version of handle_errors decorator for use with
    async Lambda handlers.
    
    Usage:
        @handle_errors_async
        async def lambda_handler(event, context):
            # Your async Lambda function code
            pass
    
    Args:
        func: The async Lambda handler function to wrap
        
    Returns:
        Wrapped async function with error handling
    """
    
    @wraps(func)
    async def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Async wrapper function that handles errors.
        
        Args:
            event: Lambda event object
            context: Lambda context object
            
        Returns:
            Lambda response with statusCode and body
        """
        request_id = context.request_id if hasattr(context, 'request_id') else 'unknown'
        
        try:
            # Execute the async Lambda function
            result = await func(event, context)
            
            # If result is already a proper Lambda response, return it
            if isinstance(result, dict) and 'statusCode' in result:
                return result
            
            # Otherwise, wrap it in a success response
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True
                },
                'body': json.dumps(result) if not isinstance(result, str) else result
            }
            
        except ValidationError as e:
            logger.warning(
                f"Validation error: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                }
            )
            return _create_error_response(400, e, request_id)
            
        except AuthenticationError as e:
            logger.warning(
                f"Authentication error: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'request_id': request_id
                }
            )
            return _create_error_response(401, e, request_id)
            
        except AuthorizationError as e:
            logger.warning(
                f"Authorization error: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                }
            )
            return _create_error_response(403, e, request_id)
            
        except ResourceNotFoundError as e:
            logger.info(
                f"Resource not found: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                }
            )
            return _create_error_response(404, e, request_id)
            
        except RateLimitError as e:
            logger.warning(
                f"Rate limit exceeded: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                }
            )
            return _create_error_response(429, e, request_id)
            
        except (DatabaseError, CacheError, DeviceError, GDPRError) as e:
            # Log full error details for internal errors
            logger.error(
                f"Service error: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                },
                exc_info=True
            )
            # Return sanitized error to client
            sanitized_error = AquaChainError(
                message='An internal error occurred. Please try again later.',
                error_code='INTERNAL_ERROR',
                details={'request_id': request_id}
            )
            return _create_error_response(500, sanitized_error, request_id)
            
        except AquaChainError as e:
            # Catch any other custom errors
            logger.error(
                f"AquaChain error: {e.message}",
                extra={
                    'error_code': e.error_code,
                    'details': e.details,
                    'request_id': request_id
                },
                exc_info=True
            )
            sanitized_error = AquaChainError(
                message='An internal error occurred. Please try again later.',
                error_code='INTERNAL_ERROR',
                details={'request_id': request_id}
            )
            return _create_error_response(500, sanitized_error, request_id)
            
        except Exception as e:
            # Catch all unexpected errors
            logger.exception(
                f"Unexpected error: {str(e)}",
                extra={
                    'request_id': request_id,
                    'error_type': type(e).__name__
                }
            )
            # Never expose internal error details to clients
            sanitized_error = AquaChainError(
                message='An unexpected error occurred. Please try again later.',
                error_code='INTERNAL_ERROR',
                details={'request_id': request_id}
            )
            return _create_error_response(500, sanitized_error, request_id)
    
    return wrapper


def handle_lambda_error(error: Exception, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle Lambda errors and return standardized error response
    
    Args:
        error: The exception that occurred
        event: Lambda event object
        context: Lambda context object
    
    Returns:
        Standardized error response
    """
    request_id = getattr(context, 'aws_request_id', 'unknown')
    
    if isinstance(error, AuditServiceError):
        logger.error(
            f"Audit service error: {error.message}",
            request_id=request_id,
            error_code=error.error_code
        )
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error.error_code,
                'message': error.message,
                'requestId': request_id
            })
        }
    elif isinstance(error, ValidationError):
        logger.warning(
            f"Validation error: {error.message}",
            request_id=request_id,
            error_code=error.error_code
        )
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': error.error_code,
                'message': error.message,
                'requestId': request_id
            })
        }
    else:
        logger.error(
            f"Unexpected error: {str(error)}",
            request_id=request_id,
            error_type=type(error).__name__
        )
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred',
                'requestId': request_id
            })
        }