"""
Utility functions for user management operations.
"""

import boto3
import logging
from typing import Dict, List, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class UserUtils:
    """
    Utility class for common user management operations.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.users_table = self.dynamodb.Table('aquachain-users')
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user profile by email address.
        """
        try:
            # Scan table for user with matching email
            response = self.users_table.scan(
                FilterExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            
            items = response.get('Items', [])
            return items[0] if items else None
            
        except ClientError as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def get_users_by_role(self, role: str) -> List[Dict]:
        """
        Get all users with specified role.
        """
        try:
            response = self.users_table.scan(
                FilterExpression='#role = :role',
                ExpressionAttributeNames={'#role': 'role'},
                ExpressionAttributeValues={':role': role}
            )
            
            return response.get('Items', [])
            
        except ClientError as e:
            logger.error(f"Error getting users by role: {e}")
            return []
    
    def get_available_technicians(self) -> List[Dict]:
        """
        Get all available technicians.
        """
        try:
            response = self.users_table.scan(
                FilterExpression='#role = :role AND availabilityStatus = :status',
                ExpressionAttributeNames={'#role': 'role'},
                ExpressionAttributeValues={
                    ':role': 'technician',
                    ':status': 'available'
                }
            )
            
            return response.get('Items', [])
            
        except ClientError as e:
            logger.error(f"Error getting available technicians: {e}")
            return []
    
    def update_technician_performance(self, user_id: str, new_rating: float, 
                                    completion_time_ratio: float) -> bool:
        """
        Update technician performance score based on customer rating and completion time.
        Implements requirement 13.1 for performance tracking.
        """
        try:
            # Get current profile
            response = self.users_table.get_item(Key={'userId': user_id})
            user_profile = response.get('Item')
            
            if not user_profile or user_profile.get('role') != 'technician':
                return False
            
            # Calculate new performance score (70% rating, 30% completion time)
            current_score = user_profile.get('performanceScore', 100.0)
            
            # Weighted average with new data
            rating_component = new_rating * 20  # Convert 5-star to 100-point scale
            time_component = max(0, 100 - (completion_time_ratio - 1) * 50)  # Penalty for delays
            
            new_score = (rating_component * 0.7) + (time_component * 0.3)
            
            # Update with exponential moving average (alpha = 0.1)
            updated_score = (current_score * 0.9) + (new_score * 0.1)
            
            # Update in database
            self.users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET performanceScore = :score, updatedAt = :updated_at',
                ExpressionAttributeValues={
                    ':score': round(updated_score, 2),
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Updated performance score for technician {user_id}: {updated_score}")
            return True
            
        except ClientError as e:
            logger.error(f"Error updating technician performance: {e}")
            return False
    
    def get_user_devices(self, user_id: str) -> List[str]:
        """
        Get list of devices associated with user.
        """
        try:
            response = self.users_table.get_item(Key={'userId': user_id})
            user_profile = response.get('Item')
            
            if user_profile:
                return user_profile.get('deviceIds', [])
            
            return []
            
        except ClientError as e:
            logger.error(f"Error getting user devices: {e}")
            return []
    
    def is_device_owner(self, user_id: str, device_id: str) -> bool:
        """
        Check if user owns the specified device.
        """
        user_devices = self.get_user_devices(user_id)
        return device_id in user_devices
    
    def validate_user_access(self, user_id: str, target_user_id: str, 
                           user_role: str) -> bool:
        """
        Validate if user has access to target user's data.
        """
        # Administrators can access all users
        if user_role == 'administrators':
            return True
        
        # Users can access their own data
        if user_id == target_user_id:
            return True
        
        return False
    
    def get_technician_workload(self, user_id: str) -> Dict:
        """
        Get current workload information for a technician.
        """
        try:
            # This would typically query the service requests table
            # For now, return basic structure
            return {
                'activeRequests': 0,
                'completedToday': 0,
                'averageRating': 5.0,
                'availabilityStatus': 'available'
            }
            
        except Exception as e:
            logger.error(f"Error getting technician workload: {e}")
            return {}

# Global utility instance
user_utils = UserUtils()

from datetime import datetime