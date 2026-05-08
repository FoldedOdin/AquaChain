"""
Maintenance Mode Middleware
Checks DynamoDB system config and blocks non-allowed roles when maintenance is active.

Usage in any Lambda handler:
    from maintenance_middleware import check_maintenance_mode

    # In lambda_handler, after auth but before routing:
    maintenance_block = check_maintenance_mode(event, user_role)
    if maintenance_block:
        return maintenance_block
"""

import json
import os
import logging
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

CONFIG_TABLE = os.environ.get('CONFIG_TABLE', 'AquaChain-SystemConfig')

# In-memory cache: avoids a DynamoDB read on every single request.
# TTL is intentionally short (30s) so changes propagate quickly.
_cache: Dict[str, Any] = {}
_cache_ttl_seconds = 30

import time


def _get_maintenance_config() -> Dict[str, Any]:
    """
    Read maintenance_mode block from DynamoDB system config.
    Returns a dict with at minimum: enabled (bool), message (str), allowedRoles (list).
    Uses a 30-second in-memory cache to reduce DynamoDB reads.
    """
    now = time.monotonic()
    if _cache.get('expires_at', 0) > now:
        return _cache.get('data', {})

    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(CONFIG_TABLE)
        response = table.get_item(Key={'configKey': 'system_config'})
        item = response.get('Item', {})
        config = item.get('maintenanceMode', {})
    except ClientError as e:
        logger.error(f"maintenance_middleware: DynamoDB read failed: {e}")
        # Fail open — don't block users if we can't read config
        config = {}

    _cache['data'] = config
    _cache['expires_at'] = now + _cache_ttl_seconds
    return config


def invalidate_cache() -> None:
    """Force cache expiry so the next request re-reads from DynamoDB."""
    _cache['expires_at'] = 0


def get_maintenance_status() -> Dict[str, Any]:
    """
    Public helper — returns the current maintenance config dict.
    Used by the public /api/system/maintenance endpoint.
    """
    config = _get_maintenance_config()
    return {
        'enabled': bool(config.get('enabled', False)),
        'message': config.get('message', 'System is under maintenance. Please try again later.'),
        'allowedRoles': config.get('allowedRoles', ['admin', 'administrator']),
    }


def check_maintenance_mode(event: Dict[str, Any], user_role: str) -> Optional[Dict[str, Any]]:
    """
    Call this after authentication, before routing.

    Returns a 503 response dict if the user is blocked, or None if they may proceed.

    Args:
        event:     The raw Lambda event (used only for logging context).
        user_role: The authenticated user's role string (e.g. 'consumer', 'technician', 'admin').
    """
    config = _get_maintenance_config()

    if not config.get('enabled', False):
        return None  # Maintenance mode is off — proceed normally

    allowed_roles = config.get('allowedRoles', ['admin', 'administrator'])

    # Normalise role comparison (backend uses 'administrators' group, frontend uses 'admin')
    normalised_role = user_role.lower().rstrip('s')  # 'administrators' → 'administrator'
    normalised_allowed = [r.lower().rstrip('s') for r in allowed_roles]

    if normalised_role in normalised_allowed:
        return None  # This role is allowed through

    message = config.get('message', 'System is under maintenance. Please try again later.')
    path = event.get('path', '')
    logger.info(f"maintenance_middleware: blocked role='{user_role}' on path='{path}'")

    return {
        'statusCode': 503,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Retry-After': '3600',
        },
        'body': json.dumps({
            'error': 'Service Unavailable',
            'code': 'MAINTENANCE_MODE',
            'message': message,
        }),
    }
