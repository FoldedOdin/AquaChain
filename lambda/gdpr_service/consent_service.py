"""
Consent Management Service
Handles user consent preferences for GDPR compliance
"""

import os
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any
from boto3.dynamodb.conditions import Key
import json


class ConsentService:
    """
    Service for managing user consent preferences.
    Tracks consent history with IP and user agent for audit purposes.
    """
    
    # Valid consent types
    CONSENT_TYPES = [
        'data_processing',
        'marketing',
        'analytics',
        'third_party_sharing'
    ]
    
    def __init__(self):
        """Initialize the consent service with DynamoDB connection."""
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get(
            'USER_CONSENTS_TABLE',
            'aquachain-user-consents-dev'
        )
        self.table = self.dynamodb.Table(self.table_name)
    
    def update_consent(
        self,
        user_id: str,
        consent_type: str,
        granted: bool,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user consent preference.
        
        Args:
            user_id: Unique identifier for the user
            consent_type: Type of consent (data_processing, marketing, analytics, third_party_sharing)
            granted: Whether consent is granted (True) or revoked (False)
            metadata: Additional context including ip_address, user_agent, request_id
            
        Returns:
            Updated consent record
            
        Raises:
            ValueError: If consent_type is invalid
        """
        if consent_type not in self.CONSENT_TYPES:
            raise ValueError(
                f"Invalid consent type: {consent_type}. "
                f"Must be one of: {', '.join(self.CONSENT_TYPES)}"
            )
        
        timestamp = datetime.utcnow().isoformat()
        
        # Create history entry
        history_entry = {
            'consent_type': consent_type,
            'action': 'granted' if granted else 'revoked',
            'timestamp': timestamp,
            'ip_address': metadata.get('ip_address', 'unknown'),
            'user_agent': metadata.get('user_agent', 'unknown'),
            'request_id': metadata.get('request_id', 'unknown')
        }
        
        # Update consent in DynamoDB
        try:
            response = self.table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='''
                    SET consents.#type = :consent,
                        updated_at = :timestamp,
                        consent_history = list_append(
                            if_not_exists(consent_history, :empty_list),
                            :history_entry
                        )
                ''',
                ExpressionAttributeNames={
                    '#type': consent_type
                },
                ExpressionAttributeValues={
                    ':consent': {
                        'granted': granted,
                        'timestamp': timestamp,
                        'version': '1.0'
                    },
                    ':timestamp': timestamp,
                    ':history_entry': [history_entry],
                    ':empty_list': []
                },
                ReturnValues='ALL_NEW'
            )
            
            return response['Attributes']
            
        except Exception as e:
            raise Exception(f"Failed to update consent: {str(e)}")
    
    def check_consent(self, user_id: str, consent_type: str) -> bool:
        """
        Check if user has granted specific consent.
        
        Args:
            user_id: Unique identifier for the user
            consent_type: Type of consent to check
            
        Returns:
            True if consent is granted, False otherwise
            
        Raises:
            ValueError: If consent_type is invalid
        """
        if consent_type not in self.CONSENT_TYPES:
            raise ValueError(
                f"Invalid consent type: {consent_type}. "
                f"Must be one of: {', '.join(self.CONSENT_TYPES)}"
            )
        
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                # No consent record exists - default to False
                return False
            
            consents = response['Item'].get('consents', {})
            consent = consents.get(consent_type, {})
            
            return consent.get('granted', False)
            
        except Exception as e:
            # On error, default to False (deny access)
            print(f"Error checking consent: {str(e)}")
            return False
    
    def get_all_consents(self, user_id: str) -> Dict[str, Any]:
        """
        Get all consent preferences for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dictionary containing all consent preferences and history
        """
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                # Return default consents (all False)
                return {
                    'user_id': user_id,
                    'consents': {
                        consent_type: {
                            'granted': False,
                            'timestamp': None,
                            'version': '1.0'
                        }
                        for consent_type in self.CONSENT_TYPES
                    },
                    'consent_history': [],
                    'updated_at': None
                }
            
            return response['Item']
            
        except Exception as e:
            raise Exception(f"Failed to get consents: {str(e)}")
    
    def get_consent_history(
        self,
        user_id: str,
        consent_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get consent history for a user.
        
        Args:
            user_id: Unique identifier for the user
            consent_type: Optional filter for specific consent type
            
        Returns:
            List of consent history entries
        """
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            
            if 'Item' not in response:
                return []
            
            history = response['Item'].get('consent_history', [])
            
            # Filter by consent type if specified
            if consent_type:
                history = [
                    entry for entry in history
                    if entry.get('consent_type') == consent_type
                ]
            
            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return history
            
        except Exception as e:
            raise Exception(f"Failed to get consent history: {str(e)}")
    
    def initialize_consents(
        self,
        user_id: str,
        default_consents: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Initialize consent record for a new user.
        
        Args:
            user_id: Unique identifier for the user
            default_consents: Optional dictionary of default consent values
            
        Returns:
            Created consent record
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Use provided defaults or set all to False
        consents = {}
        for consent_type in self.CONSENT_TYPES:
            granted = False
            if default_consents and consent_type in default_consents:
                granted = default_consents[consent_type]
            
            consents[consent_type] = {
                'granted': granted,
                'timestamp': timestamp,
                'version': '1.0'
            }
        
        # Create initial record
        item = {
            'user_id': user_id,
            'consents': consents,
            'consent_history': [],
            'updated_at': timestamp,
            'created_at': timestamp
        }
        
        try:
            self.table.put_item(Item=item)
            return item
            
        except Exception as e:
            raise Exception(f"Failed to initialize consents: {str(e)}")
    
    def bulk_update_consents(
        self,
        user_id: str,
        consent_updates: Dict[str, bool],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update multiple consent preferences at once.
        
        Args:
            user_id: Unique identifier for the user
            consent_updates: Dictionary mapping consent types to granted status
            metadata: Additional context including ip_address, user_agent
            
        Returns:
            Updated consent record
        """
        # Validate all consent types
        for consent_type in consent_updates.keys():
            if consent_type not in self.CONSENT_TYPES:
                raise ValueError(f"Invalid consent type: {consent_type}")
        
        # Update each consent individually to maintain proper history
        for consent_type, granted in consent_updates.items():
            self.update_consent(user_id, consent_type, granted, metadata)
        
        # Return the final state
        return self.get_all_consents(user_id)
