"""
CloudWatch Metrics Publisher for OTP System
Provides observability for security monitoring and alerting
"""

import boto3
from datetime import datetime
from typing import Optional
from botocore.exceptions import ClientError


class OTPMetrics:
    """Publishes custom CloudWatch metrics for OTP operations"""
    
    def __init__(self, namespace: str = 'AquaChain/Auth', region: str = 'ap-south-1'):
        """
        Initialize metrics publisher
        
        Args:
            namespace: CloudWatch namespace
            region: AWS region
        """
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.namespace = namespace
    
    def _publish_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = 'Count',
        dimensions: Optional[list] = None
    ) -> bool:
        """
        Publish a metric to CloudWatch
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit (Count, Seconds, etc.)
            dimensions: List of dimension dicts
        
        Returns:
            True if published successfully
        """
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
            
            if dimensions:
                metric_data['Dimensions'] = dimensions
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
            
            return True
            
        except ClientError as e:
            print(f"Failed to publish metric {metric_name}: {e}")
            return False
    
    def otp_generated(self, success: bool = True) -> bool:
        """
        Track OTP generation
        
        Args:
            success: Whether generation was successful
        """
        return self._publish_metric(
            metric_name='OTPGenerated',
            value=1.0,
            dimensions=[
                {'Name': 'Status', 'Value': 'Success' if success else 'Failure'}
            ]
        )
    
    def otp_verification_attempt(self, success: bool, attempts: int = 1) -> bool:
        """
        Track OTP verification attempts
        
        Args:
            success: Whether verification succeeded
            attempts: Number of attempts made
        """
        # Track overall verification
        self._publish_metric(
            metric_name='OTPVerification',
            value=1.0,
            dimensions=[
                {'Name': 'Status', 'Value': 'Success' if success else 'Failure'}
            ]
        )
        
        # Track attempt count
        return self._publish_metric(
            metric_name='OTPVerificationAttempts',
            value=float(attempts),
            unit='Count'
        )
    
    def otp_rate_limited(self, reason: str = 'email') -> bool:
        """
        Track rate limiting events
        
        Args:
            reason: Reason for rate limit (email, ip, global)
        """
        return self._publish_metric(
            metric_name='OTPRateLimited',
            value=1.0,
            dimensions=[
                {'Name': 'Reason', 'Value': reason}
            ]
        )
    
    def otp_expired(self) -> bool:
        """Track expired OTP attempts"""
        return self._publish_metric(
            metric_name='OTPExpired',
            value=1.0
        )
    
    def account_locked(self, failed_attempts: int) -> bool:
        """
        Track account lockout events
        
        Args:
            failed_attempts: Number of failed attempts that triggered lockout
        """
        self._publish_metric(
            metric_name='AccountLocked',
            value=1.0
        )
        
        return self._publish_metric(
            metric_name='FailedAttemptsBeforeLockout',
            value=float(failed_attempts),
            unit='Count'
        )
    
    def registration_attempt(self, success: bool, role: str = 'consumer') -> bool:
        """
        Track registration attempts
        
        Args:
            success: Whether registration succeeded
            role: User role
        """
        return self._publish_metric(
            metric_name='UserRegistration',
            value=1.0,
            dimensions=[
                {'Name': 'Status', 'Value': 'Success' if success else 'Failure'},
                {'Name': 'Role', 'Value': role}
            ]
        )
    
    def email_delivery(self, success: bool, email_type: str = 'otp') -> bool:
        """
        Track email delivery
        
        Args:
            success: Whether email was sent successfully
            email_type: Type of email (otp, welcome, etc.)
        """
        return self._publish_metric(
            metric_name='EmailDelivery',
            value=1.0,
            dimensions=[
                {'Name': 'Status', 'Value': 'Success' if success else 'Failure'},
                {'Name': 'Type', 'Value': email_type}
            ]
        )
    
    def suspicious_activity(self, activity_type: str, ip_address: str) -> bool:
        """
        Track suspicious activity for security monitoring
        
        Args:
            activity_type: Type of suspicious activity
            ip_address: Source IP (hashed for privacy)
        """
        import hashlib
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:8]
        
        return self._publish_metric(
            metric_name='SuspiciousActivity',
            value=1.0,
            dimensions=[
                {'Name': 'Type', 'Value': activity_type},
                {'Name': 'IPHash', 'Value': ip_hash}
            ]
        )
