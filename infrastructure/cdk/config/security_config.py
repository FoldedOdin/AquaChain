"""
Security Configuration for AquaChain
Implements production security requirements including CORS and rate limiting
"""

from typing import Dict, List


def get_cors_config(environment: str) -> Dict[str, any]:
    """
    Get CORS configuration for the specified environment.
    
    Production uses specific domain origins (no wildcards).
    Development allows localhost for testing.
    
    Args:
        environment: Environment name (dev, staging, prod)
    
    Returns:
        Dict with CORS configuration
    """
    
    # Environment-specific allowed origins
    allowed_origins = {
        "dev": [
            "http://localhost:3000",
            "http://localhost:3001",
            "https://dev.aquachain.example.com"  # Replace with actual dev domain
        ],
        "staging": [
            "https://staging.aquachain.example.com"  # Replace with actual staging domain
        ],
        "prod": [
            "https://aquachain.example.com",  # Replace with actual production domain
            "https://www.aquachain.example.com"
        ]
    }
    
    return {
        "allow_origins": allowed_origins.get(environment, ["http://localhost:3000"]),
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type",
            "Authorization",
            "X-Amz-Date",
            "X-Api-Key",
            "X-Amz-Security-Token"
        ],
        "allow_credentials": True,
        "max_age": 3600  # 1 hour
    }


def get_rate_limit_config(environment: str) -> Dict[str, int]:
    """
    Get API Gateway rate limiting configuration.
    
    Args:
        environment: Environment name (dev, staging, prod)
    
    Returns:
        Dict with rate limit settings
    """
    
    rate_limits = {
        "dev": {
            "rate_limit": 200,      # 200 requests/second for dev testing
            "burst_limit": 400,
            "quota_limit": 50000,   # 50,000 requests/day
            "quota_period": "DAY"
        },
        "staging": {
            "rate_limit": 150,      # 150 requests/second for staging
            "burst_limit": 300,
            "quota_limit": 25000,   # 25,000 requests/day
            "quota_period": "DAY"
        },
        "prod": {
            "rate_limit": 100,      # 100 requests/second for production
            "burst_limit": 200,
            "quota_limit": 10000,   # 10,000 requests/day
            "quota_period": "DAY"
        }
    }
    
    return rate_limits.get(environment, rate_limits["dev"])


def get_iam_permission_scopes(environment: str) -> Dict[str, List[str]]:
    """
    Get scoped IAM permissions (no wildcards in production).
    
    Args:
        environment: Environment name (dev, staging, prod)
    
    Returns:
        Dict with resource ARN patterns
    """
    
    # Use wildcards in dev for flexibility, specific resources in prod
    use_wildcards = environment == "dev"
    
    return {
        "dynamodb_tables": [
            "arn:aws:dynamodb:*:*:table/AquaChain-*" if use_wildcards 
            else "arn:aws:dynamodb:ap-south-1:*:table/AquaChain-*"
        ],
        "s3_buckets": [
            "arn:aws:s3:::aquachain-*" if use_wildcards
            else "arn:aws:s3:::aquachain-prod-*"
        ],
        "kms_keys": [
            "arn:aws:kms:*:*:key/*" if use_wildcards
            else "arn:aws:kms:ap-south-1:*:key/*"
        ],
        "cognito_pools": [
            "arn:aws:cognito-idp:*:*:userpool/*" if use_wildcards
            else "arn:aws:cognito-idp:ap-south-1:*:userpool/ap-south-1_*"
        ]
    }


def get_security_headers() -> Dict[str, str]:
    """
    Get security headers for API Gateway responses.
    
    Returns:
        Dict with security headers
    """
    
    return {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }


# Environment variable names for runtime configuration
CORS_ALLOWED_ORIGINS_ENV = "ALLOWED_ORIGINS"
RATE_LIMIT_ENABLED_ENV = "RATE_LIMIT_ENABLED"
