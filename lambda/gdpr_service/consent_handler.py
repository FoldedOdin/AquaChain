"""
Lambda handler for consent management operations
"""

import json
import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from gdpr_service.consent_service import ConsentService
from shared.error_handler import handle_errors
from shared.errors import ValidationError, AquaChainError
from shared.structured_logger import StructuredLogger

# Initialize logger and service
logger = StructuredLogger(__name__)
consent_service = ConsentService()


def extract_metadata(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract request metadata from Lambda event."""
    request_context = event.get('requestContext', {})
    identity = request_context.get('identity', {})
    
    return {
        'ip_address': identity.get('sourceIp', 'unknown'),
        'user_agent': identity.get('userAgent', 'unknown'),
        'request_id': request_context.get('requestId', 'unknown')
    }


def extract_user_id(event: Dict[str, Any]) -> str:
    """Extract user ID from Lambda event."""
    # Try to get from authorizer context
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    
    user_id = authorizer.get('claims', {}).get('sub')
    if not user_id:
        user_id = authorizer.get('principalId')
    
    if not user_id:
        raise ValidationError(
            "User ID not found in request",
            "MISSING_USER_ID"
        )
    
    return user_id


@handle_errors
def update_consent_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle consent update requests.
    
    Expected body:
    {
        "consent_type": "data_processing",
        "granted": true
    }
    """
    logger.log('info', 'Processing consent update request',
               service='consent_service',
               request_id=context.request_id)
    
    # Extract user ID
    user_id = extract_user_id(event)
    
    # Parse request body
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        raise ValidationError(
            "Invalid JSON in request body",
            "INVALID_JSON"
        )
    
    # Validate required fields
    consent_type = body.get('consent_type')
    if not consent_type:
        raise ValidationError(
            "consent_type is required",
            "MISSING_CONSENT_TYPE"
        )
    
    if 'granted' not in body:
        raise ValidationError(
            "granted field is required",
            "MISSING_GRANTED_FIELD"
        )
    
    granted = body.get('granted')
    if not isinstance(granted, bool):
        raise ValidationError(
            "granted must be a boolean",
            "INVALID_GRANTED_TYPE"
        )
    
    # Extract metadata
    metadata = extract_metadata(event)
    
    # Update consent
    try:
        result = consent_service.update_consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            metadata=metadata
        )
        
        logger.log('info', 'Consent updated successfully',
                   service='consent_service',
                   user_id=user_id,
                   consent_type=consent_type,
                   granted=granted)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Consent updated successfully',
                'consent': result.get('consents', {}).get(consent_type, {})
            })
        }
        
    except ValueError as e:
        raise ValidationError(str(e), "INVALID_CONSENT_TYPE")


@handle_errors
def get_consents_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle requests to get all user consents.
    """
    logger.log('info', 'Processing get consents request',
               service='consent_service',
               request_id=context.request_id)
    
    # Extract user ID
    user_id = extract_user_id(event)
    
    # Get all consents
    result = consent_service.get_all_consents(user_id)
    
    logger.log('info', 'Retrieved consents successfully',
               service='consent_service',
               user_id=user_id)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(result)
    }


@handle_errors
def check_consent_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle requests to check a specific consent.
    
    Query parameters:
    - consent_type: Type of consent to check
    """
    logger.log('info', 'Processing check consent request',
               service='consent_service',
               request_id=context.request_id)
    
    # Extract user ID
    user_id = extract_user_id(event)
    
    # Get consent type from query parameters
    query_params = event.get('queryStringParameters', {}) or {}
    consent_type = query_params.get('consent_type')
    
    if not consent_type:
        raise ValidationError(
            "consent_type query parameter is required",
            "MISSING_CONSENT_TYPE"
        )
    
    # Check consent
    try:
        granted = consent_service.check_consent(user_id, consent_type)
        
        logger.log('info', 'Checked consent successfully',
                   service='consent_service',
                   user_id=user_id,
                   consent_type=consent_type,
                   granted=granted)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'consent_type': consent_type,
                'granted': granted
            })
        }
        
    except ValueError as e:
        raise ValidationError(str(e), "INVALID_CONSENT_TYPE")


@handle_errors
def get_consent_history_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle requests to get consent history.
    
    Query parameters:
    - consent_type: Optional filter for specific consent type
    """
    logger.log('info', 'Processing get consent history request',
               service='consent_service',
               request_id=context.request_id)
    
    # Extract user ID
    user_id = extract_user_id(event)
    
    # Get optional consent type filter
    query_params = event.get('queryStringParameters', {}) or {}
    consent_type = query_params.get('consent_type')
    
    # Get history
    history = consent_service.get_consent_history(user_id, consent_type)
    
    logger.log('info', 'Retrieved consent history successfully',
               service='consent_service',
               user_id=user_id,
               history_count=len(history))
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'history': history,
            'count': len(history)
        })
    }


@handle_errors
def bulk_update_consents_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle bulk consent update requests.
    
    Expected body:
    {
        "consents": {
            "data_processing": true,
            "marketing": false,
            "analytics": true,
            "third_party_sharing": false
        }
    }
    """
    logger.log('info', 'Processing bulk consent update request',
               service='consent_service',
               request_id=context.request_id)
    
    # Extract user ID
    user_id = extract_user_id(event)
    
    # Parse request body
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        raise ValidationError(
            "Invalid JSON in request body",
            "INVALID_JSON"
        )
    
    # Validate required fields
    consent_updates = body.get('consents')
    if not consent_updates:
        raise ValidationError(
            "consents field is required",
            "MISSING_CONSENTS"
        )
    
    if not isinstance(consent_updates, dict):
        raise ValidationError(
            "consents must be a dictionary",
            "INVALID_CONSENTS_TYPE"
        )
    
    # Extract metadata
    metadata = extract_metadata(event)
    
    # Update consents
    try:
        result = consent_service.bulk_update_consents(
            user_id=user_id,
            consent_updates=consent_updates,
            metadata=metadata
        )
        
        logger.log('info', 'Bulk consent update successful',
                   service='consent_service',
                   user_id=user_id,
                   updated_count=len(consent_updates))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Consents updated successfully',
                'consents': result.get('consents', {})
            })
        }
        
    except ValueError as e:
        raise ValidationError(str(e), "INVALID_CONSENT_TYPE")
