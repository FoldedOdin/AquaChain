"""
Consent Checker Utility
Provides functions to check user consent before processing data
"""

import os
import boto3
from typing import Optional
from functools import wraps
from shared.errors import AuthorizationError
from shared.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class ConsentChecker:
    """
    Utility class for checking user consent before data processing operations.
    """
    
    def __init__(self):
        """Initialize the consent checker with DynamoDB connection."""
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get(
            'USER_CONSENTS_TABLE',
            'aquachain-user-consents-dev'
        )
        self.table = self.dynamodb.Table(self.table_name)
    
    def check_consent(self, user_id: str, consent_type: str) -> bool:
        """
        Check if user has granted specific consent.
        
        Args:
            user_id: Unique identifier for the user
            consent_type: Type of consent to check
            
        Returns:
            True if consent is granted, False otherwise
        """
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                logger.log('warning', 'No consent record found for user',
                          user_id=user_id,
                          consent_type=consent_type)
                return False
            
            consents = response['Item'].get('consents', {})
            consent = consents.get(consent_type, {})
            granted = consent.get('granted', False)
            
            logger.log('info', 'Consent check completed',
                      user_id=user_id,
                      consent_type=consent_type,
                      granted=granted)
            
            return granted
            
        except Exception as e:
            logger.log('error', 'Error checking consent',
                      user_id=user_id,
                      consent_type=consent_type,
                      error=str(e))
            # On error, default to False (deny access)
            return False
    
    def require_consent(self, consent_type: str, error_message: Optional[str] = None):
        """
        Decorator to require specific consent before executing a function.
        
        Args:
            consent_type: Type of consent required
            error_message: Optional custom error message
            
        Usage:
            @consent_checker.require_consent('marketing')
            def send_marketing_email(user_id, message):
                # Function implementation
                pass
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Try to extract user_id from args or kwargs
                user_id = kwargs.get('user_id')
                if not user_id and len(args) > 0:
                    # Assume first argument is user_id
                    user_id = args[0]
                
                if not user_id:
                    raise ValueError("user_id is required for consent check")
                
                # Check consent
                if not self.check_consent(user_id, consent_type):
                    msg = error_message or f"User has not granted consent for {consent_type}"
                    logger.log('warning', 'Consent check failed',
                              user_id=user_id,
                              consent_type=consent_type)
                    raise AuthorizationError(msg, "CONSENT_NOT_GRANTED")
                
                # Execute the function
                return func(*args, **kwargs)
            
            return wrapper
        return decorator


# Global instance
consent_checker = ConsentChecker()


def check_data_processing_consent(user_id: str) -> bool:
    """
    Check if user has granted consent for essential data processing.
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        True if consent is granted, False otherwise
    """
    return consent_checker.check_consent(user_id, 'data_processing')


def check_marketing_consent(user_id: str) -> bool:
    """
    Check if user has granted consent for marketing communications.
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        True if consent is granted, False otherwise
    """
    return consent_checker.check_consent(user_id, 'marketing')


def check_analytics_consent(user_id: str) -> bool:
    """
    Check if user has granted consent for analytics.
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        True if consent is granted, False otherwise
    """
    return consent_checker.check_consent(user_id, 'analytics')


def check_third_party_consent(user_id: str) -> bool:
    """
    Check if user has granted consent for third-party data sharing.
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        True if consent is granted, False otherwise
    """
    return consent_checker.check_consent(user_id, 'third_party_sharing')


def require_data_processing_consent(func):
    """
    Decorator to require data processing consent.
    
    Usage:
        @require_data_processing_consent
        def process_user_data(user_id, data):
            # Function implementation
            pass
    """
    return consent_checker.require_consent('data_processing')(func)


def require_marketing_consent(func):
    """
    Decorator to require marketing consent.
    
    Usage:
        @require_marketing_consent
        def send_marketing_email(user_id, message):
            # Function implementation
            pass
    """
    return consent_checker.require_consent(
        'marketing',
        'User has not consented to marketing communications'
    )(func)


def require_analytics_consent(func):
    """
    Decorator to require analytics consent.
    
    Usage:
        @require_analytics_consent
        def track_user_behavior(user_id, event):
            # Function implementation
            pass
    """
    return consent_checker.require_consent(
        'analytics',
        'User has not consented to analytics tracking'
    )(func)


def require_third_party_consent(func):
    """
    Decorator to require third-party sharing consent.
    
    Usage:
        @require_third_party_consent
        def share_with_partner(user_id, data):
            # Function implementation
            pass
    """
    return consent_checker.require_consent(
        'third_party_sharing',
        'User has not consented to third-party data sharing'
    )(func)
