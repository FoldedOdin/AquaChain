"""
Third-Party Integration with Consent Checks
Handles data sharing with third-party services with proper consent verification
"""

import os
import boto3
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from shared.consent_checker import check_third_party_consent, require_third_party_consent
from shared.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class ThirdPartyIntegration:
    """
    Service for sharing data with third-party partners.
    Only shares data for users who have granted consent.
    """
    
    def __init__(self):
        """Initialize the third-party integration service."""
        self.dynamodb = boto3.resource('dynamodb')
        self.s3_client = boto3.client('s3')
        self.sharing_log_table_name = os.environ.get(
            'DATA_SHARING_LOG_TABLE',
            'aquachain-data-sharing-log-dev'
        )
        self.sharing_log_table = self.dynamodb.Table(self.sharing_log_table_name)
    
    def share_anonymized_data(
        self,
        user_id: str,
        partner_id: str,
        data: Dict[str, Any],
        purpose: str
    ) -> bool:
        """
        Share anonymized user data with a third-party partner if consent is granted.
        
        Args:
            user_id: Unique identifier for the user
            partner_id: Identifier for the third-party partner
            data: Data to be shared (should be anonymized)
            purpose: Purpose of data sharing (research, analytics, etc.)
            
        Returns:
            True if data was shared, False if consent not granted
        """
        # Check third-party sharing consent
        if not check_third_party_consent(user_id):
            logger.log('info', 'Third-party data sharing skipped - no consent',
                      user_id=user_id,
                      partner_id=partner_id,
                      purpose=purpose)
            return False
        
        try:
            # Anonymize user ID
            anonymized_user_id = self._anonymize_user_id(user_id)
            
            # Prepare anonymized data
            anonymized_data = {
                'anonymized_user_id': anonymized_user_id,
                'data': data,
                'shared_at': datetime.utcnow().isoformat(),
                'purpose': purpose
            }
            
            # Share data with partner (implementation depends on partner API)
            self._send_to_partner(partner_id, anonymized_data)
            
            # Log the sharing event
            self._log_sharing_event(
                user_id=user_id,
                partner_id=partner_id,
                purpose=purpose,
                data_size=len(json.dumps(data))
            )
            
            logger.log('info', 'Data shared with third party',
                      user_id=user_id,
                      partner_id=partner_id,
                      purpose=purpose)
            
            return True
            
        except Exception as e:
            logger.log('error', 'Failed to share data with third party',
                      user_id=user_id,
                      partner_id=partner_id,
                      error=str(e))
            return False
    
    @require_third_party_consent
    def share_aggregated_insights(
        self,
        user_id: str,
        partner_id: str,
        insights: Dict[str, Any]
    ) -> None:
        """
        Share aggregated insights with a partner (requires consent).
        
        Args:
            user_id: Unique identifier for the user
            partner_id: Identifier for the third-party partner
            insights: Aggregated insights to share
        """
        self.share_anonymized_data(
            user_id=user_id,
            partner_id=partner_id,
            data=insights,
            purpose='aggregated_insights'
        )
    
    def _anonymize_user_id(self, user_id: str) -> str:
        """
        Create an anonymized version of the user ID.
        
        Args:
            user_id: Original user ID
            
        Returns:
            Anonymized user ID
        """
        import hashlib
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def _send_to_partner(self, partner_id: str, data: Dict[str, Any]) -> None:
        """
        Send data to partner (placeholder - implement based on partner API).
        
        Args:
            partner_id: Identifier for the third-party partner
            data: Data to send
        """
        # This is a placeholder. In production, this would:
        # 1. Look up partner API endpoint
        # 2. Authenticate with partner
        # 3. Send data via partner's API
        # 4. Handle response and errors
        
        logger.log('info', 'Sending data to partner',
                  partner_id=partner_id,
                  data_size=len(json.dumps(data)))
    
    def _log_sharing_event(
        self,
        user_id: str,
        partner_id: str,
        purpose: str,
        data_size: int
    ) -> None:
        """
        Log a data sharing event for audit purposes.
        
        Args:
            user_id: Unique identifier for the user
            partner_id: Identifier for the third-party partner
            purpose: Purpose of data sharing
            data_size: Size of shared data in bytes
        """
        try:
            log_entry = {
                'log_id': f"{user_id}:{partner_id}:{datetime.utcnow().timestamp()}",
                'user_id': user_id,
                'partner_id': partner_id,
                'purpose': purpose,
                'data_size': data_size,
                'timestamp': datetime.utcnow().isoformat(),
                'consent_verified': True
            }
            
            self.sharing_log_table.put_item(Item=log_entry)
            
        except Exception as e:
            logger.log('error', 'Failed to log sharing event',
                      user_id=user_id,
                      partner_id=partner_id,
                      error=str(e))
    
    def get_sharing_history(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get data sharing history for a user.
        
        Args:
            user_id: Unique identifier for the user
            limit: Maximum number of records to return
            
        Returns:
            List of sharing events
        """
        try:
            response = self.sharing_log_table.query(
                IndexName='user_id-timestamp-index',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id},
                Limit=limit,
                ScanIndexForward=False  # Newest first
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.log('error', 'Failed to get sharing history',
                      user_id=user_id,
                      error=str(e))
            return []


# Global instance
third_party_integration = ThirdPartyIntegration()


def share_with_partner(
    user_id: str,
    partner_id: str,
    data: Dict[str, Any],
    purpose: str
) -> bool:
    """
    Convenience function to share data with a partner with consent check.
    
    Args:
        user_id: Unique identifier for the user
        partner_id: Identifier for the third-party partner
        data: Data to share
        purpose: Purpose of sharing
        
    Returns:
        True if data was shared, False otherwise
    """
    return third_party_integration.share_anonymized_data(
        user_id=user_id,
        partner_id=partner_id,
        data=data,
        purpose=purpose
    )
