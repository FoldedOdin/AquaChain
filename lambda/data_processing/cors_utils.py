"""
CORS utility for Lambda functions
Provides consistent CORS headers across all API responses
"""

import json
from typing import Any, Dict, Optional

# CORS configuration
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',  # Allow all origins for development
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-Requested-With',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    'Access-Control-Allow-Credentials': 'false',  # Must be false when using wildcard origin
    'Content-Type': 'application/json'
}

def cors_response(status_code: int, body: Any, additional_headers: Optional[Dict[str, str]] = None) -> Dict:
    """
    Create a Lambda response with CORS headers
    
    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized if not a string)
        additional_headers: Optional additional headers to include
    
    Returns:
        Dict: Lambda response object with CORS headers
    """
    headers = CORS_HEADERS.copy()
    
    if additional_headers:
        headers.update(additional_headers)
    
    # Serialize body if it's not already a string
    if not isinstance(body, str):
        body = json.dumps(body)
    
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': body
    }

def handle_options() -> Dict:
    """
    Handle OPTIONS preflight requests
    
    Returns:
        Dict: Lambda response for OPTIONS with CORS headers
    """
    return {
        'statusCode': 204,
        'headers': CORS_HEADERS,
        'body': ''
    }

def success_response(body: Any, status_code: int = 200) -> Dict:
    """
    Create a successful response with CORS headers
    
    Args:
        body: Response body
        status_code: HTTP status code (default: 200)
    
    Returns:
        Dict: Lambda response object
    """
    return cors_response(status_code, body)

def error_response(message: str, status_code: int = 500, details: Optional[Dict] = None) -> Dict:
    """
    Create an error response with CORS headers
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 500)
        details: Optional error details
    
    Returns:
        Dict: Lambda response object
    """
    error_body = {
        'error': message,
        'statusCode': status_code
    }
    
    if details:
        error_body['details'] = details
    
    return cors_response(status_code, error_body)

def created_response(body: Any) -> Dict:
    """
    Create a 201 Created response with CORS headers
    
    Args:
        body: Response body
    
    Returns:
        Dict: Lambda response object
    """
    return cors_response(201, body)

def no_content_response() -> Dict:
    """
    Create a 204 No Content response with CORS headers
    
    Returns:
        Dict: Lambda response object
    """
    return cors_response(204, '')
