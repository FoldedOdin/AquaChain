"""
Audit Logger for Authentication Events
Logs security-relevant events for compliance and fraud detection
"""

import boto3
import json
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError


class AuditLogger:
    """Handles audit logging for authentication events"""
    
    def __init__(self, table_name: str = 'AquaChain-AuthEvents', region: str = 'ap-south-1'):
        """
        Initialize audit logger
        
        Args:
            table_name: DynamoDB table name for audit logs
            region: AWS region
        """
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
    
    def log_event(
        self,
        email: str,
        event_type: str,
        status: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log an authentication event
        
        Args:
            email: User email
            event_type: Type of event (OTP_REQUESTED, OTP_VERIFIED, etc.)
            status: Event status (SUCCESS, FAILURE, RATE_LIMITED, etc.)
            ip_address: Client IP address
            user_agent: Client User-Agent
            metadata: Additional event metadata
        
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            item = {
                'email': email,
                'timestamp': timestamp,
                'eventType': event_type,
                'status': status,
                'ipAddress': ip_address,
                'userAgent': user_agent,
                'ttl': int(datetime.utcnow().timestamp()) + (90 * 24 * 60 * 60)  # 90 days retention
            }
            
            if metadata:
                item['metadata'] = metadata
            
            self.table.put_item(Item=item)
            return True
            
        except ClientError as e:
            print(f"Failed to log audit event: {e}")
            return False
    
    def log_otp_request(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        reason: Optional[str] = None
    ) -> bool:
        """Log OTP request event"""
        return self.log_event(
            email=email,
            event_type='OTP_REQUESTED',
            status='SUCCESS' if success else 'FAILURE',
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={'reason': reason} if reason else None
        )
    
    def log_otp_verification(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        attempts: int,
        reason: Optional[str] = None
    ) -> bool:
        """Log OTP verification event"""
        return self.log_event(
            email=email,
            event_type='OTP_VERIFIED',
            status='SUCCESS' if success else 'FAILURE',
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'attempts': attempts,
                'reason': reason
            }
        )
    
    def log_registration(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        role: str,
        reason: Optional[str] = None
    ) -> bool:
        """Log user registration event"""
        return self.log_event(
            email=email,
            event_type='USER_REGISTERED',
            status='SUCCESS' if success else 'FAILURE',
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'role': role,
                'reason': reason
            }
        )
    
    def log_rate_limit(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        event_type: str,
        remaining_seconds: int
    ) -> bool:
        """Log rate limiting event"""
        return self.log_event(
            email=email,
            event_type=event_type,
            status='RATE_LIMITED',
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={'remainingSeconds': remaining_seconds}
        )
    
    def log_lockout(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        failed_attempts: int,
        lock_duration_minutes: int
    ) -> bool:
        """Log account lockout event"""
        return self.log_event(
            email=email,
            event_type='ACCOUNT_LOCKED',
            status='LOCKED',
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'failedAttempts': failed_attempts,
                'lockDurationMinutes': lock_duration_minutes
            }
        )
    
    def get_recent_events(
        self,
        email: str,
        limit: int = 10
    ) -> list:
        """
        Get recent events for a user
        
        Args:
            email: User email
            limit: Maximum number of events to return
        
        Returns:
            List of recent events
        """
        try:
            response = self.table.query(
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            return response.get('Items', [])
            
        except ClientError as e:
            print(f"Failed to query audit events: {e}")
            return []


# Create default instance for easy importing
audit_logger = AuditLogger()
