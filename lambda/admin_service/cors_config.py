"""
CORS Configuration for Admin Service Lambda
Implements environment-specific CORS policies (no wildcards in production)
"""

import os
import json
from typing import Dict, List


def get_allowed_origins() -> List[str]:
    """
    Get allowed origins from environment variable.
    Falls back to localhost for development if not set.
    
    Returns:
        List of allowed origin URLs
    """
    
    # Read from environment variable (set by CDK deployment)
    origins_env = os.environ.get("ALLOWED_ORIGINS", "")
    
    if origins_env:
        # Parse comma-separated list
        return [origin.strip() for origin in origins_env.split(",")]
    
    # Fallback for local development
    return ["http://localhost:3000"]


def get_cors_headers(origin: str = None) -> Dict[str, str]:
    """
    Get CORS headers for API response.
    Only returns Access-Control-Allow-Origin if origin is in allowed list.
    
    Args:
        origin: Origin header from request
    
    Returns:
        Dict with CORS headers
    """
    
    allowed_origins = get_allowed_origins()
    
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Max-Age": "3600",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block"
    }
    
    # Only add Access-Control-Allow-Origin if origin is allowed
    if origin and origin in allowed_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    elif len(allowed_origins) == 1:
        # If only one origin configured, use it
        headers["Access-Control-Allow-Origin"] = allowed_origins[0]
        headers["Access-Control-Allow-Credentials"] = "true"
    else:
        # Don't set origin header if not in allowed list (request will fail)
        pass
    
    return headers


def create_response(status_code: int, body: Dict, origin: str = None) -> Dict:
    """
    Create API Gateway response with proper CORS headers.
    
    Args:
        status_code: HTTP status code
        body: Response body dict
        origin: Origin header from request
    
    Returns:
        API Gateway response dict
    """
    
    return {
        "statusCode": status_code,
        "headers": get_cors_headers(origin),
        "body": json.dumps(body)
    }


def handle_options_request(origin: str = None) -> Dict:
    """
    Handle OPTIONS preflight request.
    
    Args:
        origin: Origin header from request
    
    Returns:
        API Gateway response for OPTIONS request
    """
    
    return {
        "statusCode": 200,
        "headers": get_cors_headers(origin),
        "body": ""
    }
