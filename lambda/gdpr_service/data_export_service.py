"""
Data Export Service for GDPR compliance.

This module provides functionality to export all user data in JSON format
for GDPR data portability requirements.
"""

import boto3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from boto3.dynamodb.conditions import Key

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from errors import GDPRError, DatabaseError
from structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class DataExportService:
    """
    Service for exporting user data in compliance with GDPR Article 20
    (Right to data portability).
    """
    
    def __init__(self):
        """Initialize the DataExportService with AWS clients."""
        self.dynamodb = boto3.resource('dynamodb')
        self.s3 = boto3.client('s3')
        self.sns = boto3.client('sns')
        
        # Table names from environment variables
        self.users_table_name = os.environ.get('USERS_TABLE', 'aquachain-users')
        self.devices_table_name = os.environ.get('DEVICES_TABLE', 'aquachain-devices')
        self.readings_table_name = os.environ.get('READINGS_TABLE', 'aquachain-readings')
        self.alerts_table_name = os.environ.get('ALERTS_TABLE', 'aquachain-alerts')
        self.audit_logs_table_name = os.environ.get('AUDIT_LOGS_TABLE', 'aquachain-audit-logs')
        self.service_requests_table_name = os.environ.get('SERVICE_REQUESTS_TABLE', 'aquachain-service-requests')
        
        # S3 bucket for exports
        self.export_bucket = os.environ.get('EXPORT_BUCKET')
        
        # SNS topic for notifications
        self.notification_topic = os.environ.get('NOTIFICATION_TOPIC_ARN')
    
    def export_user_data(
        self,
        user_id: str,
        request_id: str,
        user_email: Optional[str] = None
    ) -> str:
        """
        Export all user data in JSON format.
        
        Args:
            user_id: The unique identifier of the user
            request_id: The GDPR request ID for tracking
            user_email: Optional email address for notification
            
        Returns:
            S3 URL of the export file (presigned URL valid for 7 days)
            
        Raises:
            GDPRError: If export fails
            DatabaseError: If database operations fail
        """
        try:
            logger.log(
                'info',
                'Starting GDPR data export',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id
            )
            
            # Collect data from all tables
            export_data = {
                'export_metadata': {
                    'export_date': datetime.utcnow().isoformat(),
                    'user_id': user_id,
                    'request_id': request_id,
                    'format_version': '1.0'
                },
                'profile': self._get_user_profile(user_id),
                'devices': self._get_user_devices(user_id),
                'sensor_readings': self._get_sensor_readings(user_id),
                'alerts': self._get_user_alerts(user_id),
                'service_requests': self._get_service_requests(user_id),
                'audit_logs': self._get_audit_logs(user_id)
            }
            
            # Upload to S3
            export_key = f"gdpr-exports/{user_id}/{request_id}/{datetime.utcnow().isoformat()}.json"
            
            if not self.export_bucket:
                raise GDPRError(
                    'Export bucket not configured',
                    'EXPORT_BUCKET_NOT_CONFIGURED',
                    {'user_id': user_id}
                )
            
            self.s3.put_object(
                Bucket=self.export_bucket,
                Key=export_key,
                Body=json.dumps(export_data, indent=2, default=str),
                ServerSideEncryption='AES256',
                ContentType='application/json',
                Metadata={
                    'user_id': user_id,
                    'request_id': request_id,
                    'export_date': datetime.utcnow().isoformat()
                }
            )
            
            logger.log(
                'info',
                'Data export uploaded to S3',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id,
                export_key=export_key
            )
            
            # Generate presigned URL (valid for 7 days)
            presigned_url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.export_bucket,
                    'Key': export_key
                },
                ExpiresIn=604800  # 7 days in seconds
            )
            
            # Send notification to user
            if user_email and self.notification_topic:
                self._notify_user(user_id, user_email, presigned_url, request_id)
            
            logger.log(
                'info',
                'GDPR data export completed successfully',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id
            )
            
            return presigned_url
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to export user data: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id,
                error=str(e)
            )
            raise GDPRError(
                f'Failed to export user data: {str(e)}',
                'EXPORT_FAILED',
                {'user_id': user_id, 'request_id': request_id}
            )
    
    def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve user profile data.
        
        Args:
            user_id: The user identifier
            
        Returns:
            User profile data dictionary
        """
        try:
            table = self.dynamodb.Table(self.users_table_name)
            response = table.get_item(Key={'userId': user_id})
            return response.get('Item', {})
        except Exception as e:
            logger.log(
                'error',
                f'Failed to retrieve user profile: {str(e)}',
                service='gdpr_service',
                user_id=user_id
            )
            return {'error': f'Failed to retrieve profile: {str(e)}'}
    
    def _get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all devices owned by the user.
        
        Args:
            user_id: The user identifier
            
        Returns:
            List of device data dictionaries
        """
        try:
            table = self.dynamodb.Table(self.devices_table_name)
            response = table.query(
                IndexName='user_id-created_at-index',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            return response.get('Items', [])
        except Exception as e:
            logger.log(
                'error',
                f'Failed to retrieve user devices: {str(e)}',
                service='gdpr_service',
                user_id=user_id
            )
            return [{'error': f'Failed to retrieve devices: {str(e)}'}]
    
    def _get_sensor_readings(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all sensor readings from user's devices.
        
        Args:
            user_id: The user identifier
            
        Returns:
            List of sensor reading data dictionaries
        """
        try:
            # First get all user devices
            devices = self._get_user_devices(user_id)
            
            if not devices or 'error' in devices[0]:
                return []
            
            readings = []
            table = self.dynamodb.Table(self.readings_table_name)
            
            # Query readings for each device
            for device in devices:
                device_id = device.get('device_id')
                if not device_id:
                    continue
                
                try:
                    response = table.query(
                        IndexName='DeviceIndex',
                        KeyConditionExpression=Key('deviceId').eq(device_id),
                        Limit=1000  # Limit per device to prevent excessive data
                    )
                    readings.extend(response.get('Items', []))
                    
                    # Handle pagination if needed
                    while 'LastEvaluatedKey' in response and len(readings) < 10000:
                        response = table.query(
                            IndexName='DeviceIndex',
                            KeyConditionExpression=Key('deviceId').eq(device_id),
                            ExclusiveStartKey=response['LastEvaluatedKey'],
                            Limit=1000
                        )
                        readings.extend(response.get('Items', []))
                        
                except Exception as e:
                    logger.log(
                        'warning',
                        f'Failed to retrieve readings for device {device_id}: {str(e)}',
                        service='gdpr_service',
                        user_id=user_id,
                        device_id=device_id
                    )
                    continue
            
            return readings
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to retrieve sensor readings: {str(e)}',
                service='gdpr_service',
                user_id=user_id
            )
            return [{'error': f'Failed to retrieve sensor readings: {str(e)}'}]
    
    def _get_user_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all alerts for user's devices.
        
        Args:
            user_id: The user identifier
            
        Returns:
            List of alert data dictionaries
        """
        try:
            # Get all user devices first
            devices = self._get_user_devices(user_id)
            
            if not devices or 'error' in devices[0]:
                return []
            
            alerts = []
            table = self.dynamodb.Table(self.alerts_table_name)
            
            # Query alerts for each device
            for device in devices:
                device_id = device.get('device_id')
                if not device_id:
                    continue
                
                try:
                    response = table.query(
                        IndexName='DeviceAlerts',
                        KeyConditionExpression=Key('deviceId').eq(device_id)
                    )
                    alerts.extend(response.get('Items', []))
                except Exception as e:
                    logger.log(
                        'warning',
                        f'Failed to retrieve alerts for device {device_id}: {str(e)}',
                        service='gdpr_service',
                        user_id=user_id,
                        device_id=device_id
                    )
                    continue
            
            return alerts
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to retrieve alerts: {str(e)}',
                service='gdpr_service',
                user_id=user_id
            )
            return [{'error': f'Failed to retrieve alerts: {str(e)}'}]
    
    def _get_service_requests(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all service requests associated with the user.
        
        Args:
            user_id: The user identifier
            
        Returns:
            List of service request data dictionaries
        """
        try:
            table = self.dynamodb.Table(self.service_requests_table_name)
            
            # Query by consumer ID
            response = table.query(
                IndexName='ConsumerIndex',
                KeyConditionExpression=Key('consumerId').eq(user_id)
            )
            
            service_requests = response.get('Items', [])
            
            # Also check if user is a technician
            try:
                tech_response = table.query(
                    IndexName='TechnicianIndex',
                    KeyConditionExpression=Key('technicianId').eq(user_id)
                )
                service_requests.extend(tech_response.get('Items', []))
            except Exception:
                pass  # TechnicianIndex might not exist or user might not be a technician
            
            return service_requests
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to retrieve service requests: {str(e)}',
                service='gdpr_service',
                user_id=user_id
            )
            return [{'error': f'Failed to retrieve service requests: {str(e)}'}]
    
    def _get_audit_logs(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs for the user.
        
        Args:
            user_id: The user identifier
            
        Returns:
            List of audit log data dictionaries
        """
        try:
            table = self.dynamodb.Table(self.audit_logs_table_name)
            response = table.query(
                IndexName='user_id-timestamp-index',
                KeyConditionExpression=Key('user_id').eq(user_id),
                Limit=1000  # Limit audit logs to prevent excessive data
            )
            return response.get('Items', [])
        except Exception as e:
            logger.log(
                'warning',
                f'Failed to retrieve audit logs: {str(e)}',
                service='gdpr_service',
                user_id=user_id
            )
            # Audit logs table might not exist yet
            return []
    
    def _notify_user(
        self,
        user_id: str,
        user_email: str,
        download_url: str,
        request_id: str
    ) -> None:
        """
        Send notification email to user with download link.
        
        Args:
            user_id: The user identifier
            user_email: User's email address
            download_url: Presigned URL for downloading the export
            request_id: The GDPR request ID
        """
        try:
            message = {
                'subject': 'Your AquaChain Data Export is Ready',
                'body': f'''
Hello,

Your data export request (ID: {request_id}) has been completed.

You can download your data using the link below. This link will expire in 7 days.

Download Link: {download_url}

The export includes:
- Your profile information
- All devices registered to your account
- Sensor readings from your devices
- Alert history
- Service requests
- Audit logs of your account activity

If you did not request this export, please contact our support team immediately.

Best regards,
The AquaChain Team
                '''.strip()
            }
            
            self.sns.publish(
                TopicArn=self.notification_topic,
                Subject=message['subject'],
                Message=json.dumps({
                    'email': user_email,
                    'subject': message['subject'],
                    'body': message['body'],
                    'user_id': user_id,
                    'request_id': request_id
                })
            )
            
            logger.log(
                'info',
                'Export notification sent to user',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id
            )
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to send notification: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id
            )
            # Don't fail the export if notification fails
