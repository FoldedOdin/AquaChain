"""
WebSocket Connect Handler
Handles new WebSocket connections, validates JWT auth token, and stores
connection info in DynamoDB.
"""

import json
import boto3
import os
import logging
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
connections_table_name = os.environ.get('CONNECTIONS_TABLE', 'AquaChain-WebSocketConnections-dev')
connections_table = dynamodb.Table(connections_table_name)

COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID', 'ap-south-1_QUDl7hG8u')

# Module-level JWKS cache — avoids repeated HTTP calls across warm invocations
_jwks_cache: Dict[str, Any] = {}


def _get_cognito_public_keys() -> Dict[str, Any]:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    try:
        region = COGNITO_USER_POOL_ID.split('_')[0]
        url = f'https://cognito-idp.{region}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json'
        with urllib.request.urlopen(url, timeout=5) as resp:
            jwks = json.loads(resp.read().decode())
        try:
            import jwt
            from jwt.algorithms import RSAAlgorithm
            keys = {}
            for key_data in jwks.get('keys', []):
                keys[key_data['kid']] = RSAAlgorithm.from_jwk(json.dumps(key_data))
            _jwks_cache = keys
            return keys
        except ImportError:
            # PyJWT not available — fall back to unverified decode
            logger.warning("PyJWT not available, skipping signature verification")
            return {}
    except Exception as e:
        logger.error(f"Failed to fetch Cognito JWKS: {e}")
        return {}


def _validate_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a Cognito access token and return its claims, or None if invalid.
    Falls back to unverified decode if JWKS is unavailable (logs a warning).
    """
    try:
        import jwt

        # Fast-path: check token_use without verifying signature
        unverified = jwt.decode(token, options={"verify_signature": False})
        if unverified.get('token_use') != 'access':
            logger.warning("Token rejected: token_use is not 'access'")
            return None

        public_keys = _get_cognito_public_keys()
        if not public_keys:
            # JWKS unavailable — accept the token but log a warning
            logger.warning("JWKS unavailable, accepting token without signature verification")
            if unverified.get('exp', 0) < datetime.utcnow().timestamp():
                logger.warning("Token expired (unverified path)")
                return None
            return unverified

        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        if kid not in public_keys:
            logger.warning(f"Unknown key ID: {kid}")
            return None

        decoded = jwt.decode(
            token,
            public_keys[kid],
            algorithms=['RS256'],
            options={"verify_aud": False}  # Cognito access tokens have no 'aud'
        )

        if decoded.get('exp', 0) < datetime.utcnow().timestamp():
            logger.warning("Token expired")
            return None

        return decoded

    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        return None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket $connect route.
    Validates authToken query param and stores connection in DynamoDB.
    Returns 401 if token is missing or invalid.
    """
    try:
        connection_id = event['requestContext']['connectionId']
        domain_name = event['requestContext']['domainName']
        stage = event['requestContext']['stage']

        query_params = event.get('queryStringParameters') or {}
        auth_token = query_params.get('authToken') or query_params.get('token')
        topic = query_params.get('topic', 'consumer-updates')
        connection_type = query_params.get('type', 'dashboard')

        logger.info(f"$connect: connectionId={connection_id} topic={topic} hasToken={bool(auth_token)}")

        # Reject connections without a token
        if not auth_token:
            logger.warning(f"Connection {connection_id} rejected: no auth token provided")
            return {'statusCode': 401}

        # Validate the token
        claims = _validate_token(auth_token)
        if not claims:
            logger.warning(f"Connection {connection_id} rejected: invalid or expired token")
            return {'statusCode': 401}

        user_id = claims.get('sub', 'unknown')

        # Normalise Cognito group → role
        user_groups = claims.get('cognito:groups', ['consumers'])
        raw_role = user_groups[0] if user_groups else 'consumers'
        role_map = {
            'consumers': 'consumer', 'consumer': 'consumer',
            'technicians': 'technician', 'technician': 'technician',
            'administrators': 'administrator', 'administrator': 'administrator',
            'admins': 'administrator', 'admin': 'administrator',
        }
        user_role = role_map.get(raw_role.lower(), 'consumer')

        logger.info(f"$connect authenticated: connectionId={connection_id} userId={user_id} role={user_role} topic={topic}")

        ttl = int((datetime.utcnow() + timedelta(hours=24)).timestamp())

        try:
            connections_table.put_item(
                Item={
                    'connectionId': connection_id,
                    'userId': user_id,
                    'userRole': user_role,
                    'connectionType': connection_type,
                    'topic': topic,
                    'domainName': domain_name,
                    'stage': stage,
                    'connectedAt': datetime.utcnow().isoformat(),
                    'lastPing': datetime.utcnow().isoformat(),
                    'subscriptions': [
                        {
                            'type': topic,
                            'filters': {},
                            'subscribedAt': datetime.utcnow().isoformat()
                        }
                    ],
                    'ttl': ttl
                }
            )
            logger.info(f"Connection {connection_id} stored successfully for user {user_id}")
        except Exception as db_err:
            logger.error(f"DynamoDB write failed for {connection_id}: {db_err}")
            # Don't reject — client is authenticated, storage failure is non-fatal

        return {'statusCode': 200}

    except Exception as e:
        logger.error(f"Unexpected error in $connect handler: {e}", exc_info=True)
        return {'statusCode': 500}
