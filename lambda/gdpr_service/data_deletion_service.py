"""
Data Deletion Service for GDPR compliance.

This module provides functionality to permanently delete all user data
for GDPR Right to Erasure (Article 17) compliance.
"""

import boto3
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from boto3.dynamodb.conditions import Key

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from errors import GDPRError, DatabaseError
from structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class DataDeletionService:
    """
    Service for deleting user data in compliance with GDPR Article 17
    (Right to erasure / Right to be forgotten).
    """
    
    def __init__(self):
        """Initialize the DataDeletionService with AWS clients."""
        self.dynamodb = boto3.resource('dynamodb')
        self.s3 = boto3.client('s3')
        self.cognito = boto3.client('cognito-idp')
        self.sns = boto3.client('sns')
        
        # Table names from environment variables
        self.users_table_name = os.environ.get('USERS_TABLE', 'aquachain-users')
        self.devices_table_name = os.environ.get('DEVICES_TABLE', 'aquachain-devices')
        self.readings_table_name = os.environ.get('READINGS_TABLE', 'aquachain-readings')
        self.alerts_table_name = os.environ.get('ALERTS_TABLE', 'aquachain-alerts')
        self.audit_logs_table_name = os.environ.get('AUDIT_LOGS_TABLE', 'aquachain-audit-logs')
        self.service_requests_table_name = os.environ.get('SERVICE_REQUESTS_TABLE', 'aquachain-service-requests')
        self.user_consents_table_name = os.environ.get('USER_CONSENTS_TABLE', 'aquachain-user-consents')
        
        # Cognito User Pool ID
        self.user_pool_id = os.environ.get('USER_POOL_ID')
        
        # S3 bucket for deletion summaries
        self.compliance_bucket = os.environ.get('COMPLIANCE_BUCKET')
        
        # SNS topic for notifications
        self.notification_topic = os.environ.get('NOTIFICATION_TOPIC_ARN')
    
    def delete_user_data(
        self,
        user_id: str,
        request_id: str,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Permanently delete all user data.
        
        This method deletes data from all tables and anonymizes audit logs
        (which cannot be deleted for compliance reasons).
        
        Args:
            user_id: The unique identifier of the user
            request_id: The GDPR request ID for tracking
            user_email: Optional email address for notification
            
        Returns:
            Deletion summary dictionary containing counts of deleted items
            
        Raises:
            GDPRError: If deletion fails
            DatabaseError: If database operations fail
        """
        try:
            logger.log(
                'info',
                'Starting GDPR data deletion',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id
            )
            
            deletion_summary = {
                'deletion_metadata': {
                    'deletion_date': datetime.utcnow().isoformat(),
                    'user_id': user_id,
                    'request_id': request_id,
                    'format_version': '1.0'
                },
                'deleted_items': {},
                'anonymized_items': {},
                'errors': []
            }
            
            # Delete data from all tables
            deletion_summary['deleted_items']['profile'] = self._delete_user_profile(user_id)
            deletion_summary['deleted_items']['devices'] = self._delete_user_devices(user_id)
            deletion_summary['deleted_items']['readings'] = self._delete_sensor_readings(user_id)
            deletion_summary['deleted_items']['alerts'] = self._delete_user_alerts(user_id)
            deletion_summary['deleted_items']['service_requests'] = self._delete_service_requests(user_id)
            deletion_summary['deleted_items']['consents'] = self._delete_user_consents(user_id)
            
            # Anonymize audit logs (cannot delete for compliance)
            deletion_summary['anonymized_items']['audit_logs'] = self._anonymize_audit_logs(user_id)
            
            # Delete Cognito user account
            deletion_summary['deleted_items']['cognito_account'] = self._delete_cognito_user(user_id)
            
            # Store deletion record for compliance
            self._store_deletion_record(deletion_summary)
            
            # Send confirmation email
            if user_email and self.notification_topic:
                self._notify_user(user_id, user_email, deletion_summary, request_id)
            
            logger.log(
                'info',
                'GDPR data deletion completed successfully',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id,
                deleted_items=deletion_summary['deleted_items'],
                anonymized_items=deletion_summary['anonymized_items']
            )
            
            return deletion_summary
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to delete user data: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id,
                error=str(e)
            )
            raise GDPRError(
                f'Failed to delete user data: {str(e)}',
                'DELETION_FAILED',
                {'user_id': user_id, 'request_id': request_id}
            )
    
    def _delete_user_profile(self, user_id: str) -> int:
        """
        Delete user profile data.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Number of items deleted (0 or 1)
        """
        try:
            table = self.dynamodb.Table(self.users_table_name)
            response = table.delete_item(
                Key={'userId': user_id},
                ReturnValues='ALL_OLD'
            )
            
            deleted = 1 if 'Attributes' in response else 0
            
            logger.log(
                'info',
                f'Deleted user profile',
                service='gdpr_service',
                user_id=user_id,
                deleted_count=deleted
            )
            
            return deleted
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to delete user profile: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                error=str(e)
            )
            return 0
    
    def _delete_user_devices(self, user_id: str) -> int:
        """
        Delete all devices owned by the user.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Number of devices deleted
        """
        try:
            table = self.dynamodb.Table(self.devices_table_name)
            
            # Query devices by user_id
            response = table.query(
                IndexName='user_id-created_at-index',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            
            devices = response.get('Items', [])
            count = 0
            
            # Delete each device
            for device in devices:
                device_id = device.get('device_id')
                if device_id:
                    try:
                        table.delete_item(Key={'device_id': device_id})
                        count += 1
                    except Exception as e:
                        logger.log(
                            'warning',
                            f'Failed to delete device {device_id}: {str(e)}',
                            service='gdpr_service',
                            user_id=user_id,
                            device_id=device_id
                        )
            
            logger.log(
                'info',
                f'Deleted user devices',
                service='gdpr_service',
                user_id=user_id,
                deleted_count=count
            )
            
            return count
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to delete user devices: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                error=str(e)
            )
            return 0
    
    def _delete_sensor_readings(self, user_id: str) -> int:
        """
        Delete all sensor readings from user's devices.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Number of readings deleted
        """
        try:
            # First get all user devices
            devices_table = self.dynamodb.Table(self.devices_table_name)
            devices_response = devices_table.query(
                IndexName='user_id-created_at-index',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            
            devices = devices_response.get('Items', [])
            
            if not devices:
                return 0
            
            readings_table = self.dynamodb.Table(self.readings_table_name)
            total_count = 0
            
            # Delete readings for each device
            for device in devices:
                device_id = device.get('device_id')
                if not device_id:
                    continue
                
                try:
                    # Query readings for this device
                    response = readings_table.query(
                        IndexName='DeviceIndex',
                        KeyConditionExpression=Key('deviceId').eq(device_id)
                    )
                    
                    readings = response.get('Items', [])
                    
                    # Delete each reading
                    for reading in readings:
                        reading_id = reading.get('readingId')
                        timestamp = reading.get('timestamp')
                        
                        if reading_id and timestamp:
                            try:
                                readings_table.delete_item(
                                    Key={
                                        'readingId': reading_id,
                                        'timestamp': timestamp
                                    }
                                )
                                total_count += 1
                            except Exception as e:
                                logger.log(
                                    'warning',
                                    f'Failed to delete reading: {str(e)}',
                                    service='gdpr_service',
                                    user_id=user_id,
                                    reading_id=reading_id
                                )
                    
                    # Handle pagination
                    while 'LastEvaluatedKey' in response:
                        response = readings_table.query(
                            IndexName='DeviceIndex',
                            KeyConditionExpression=Key('deviceId').eq(device_id),
                            ExclusiveStartKey=response['LastEvaluatedKey']
                        )
                        
                        readings = response.get('Items', [])
                        
                        for reading in readings:
                            reading_id = reading.get('readingId')
                            timestamp = reading.get('timestamp')
                            
                            if reading_id and timestamp:
                                try:
                                    readings_table.delete_item(
                                        Key={
                                            'readingId': reading_id,
                                            'timestamp': timestamp
                                        }
                                    )
                                    total_count += 1
                                except Exception:
                                    pass
                    
                except Exception as e:
                    logger.log(
                        'warning',
                        f'Failed to delete readings for device {device_id}: {str(e)}',
                        service='gdpr_service',
                        user_id=user_id,
                        device_id=device_id
                    )
                    continue
            
            logger.log(
                'info',
                f'Deleted sensor readings',
                service='gdpr_service',
                user_id=user_id,
                deleted_count=total_count
            )
            
            return total_count
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to delete sensor readings: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                error=str(e)
            )
            return 0
    
    def _delete_user_alerts(self, user_id: str) -> int:
        """
        Delete all alerts for user's devices.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Number of alerts deleted
        """
        try:
            # Get all user devices first
            devices_table = self.dynamodb.Table(self.devices_table_name)
            devices_response = devices_table.query(
                IndexName='user_id-created_at-index',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            
            devices = devices_response.get('Items', [])
            
            if not devices:
                return 0
            
            alerts_table = self.dynamodb.Table(self.alerts_table_name)
            total_count = 0
            
            # Delete alerts for each device
            for device in devices:
                device_id = device.get('device_id')
                if not device_id:
                    continue
                
                try:
                    response = alerts_table.query(
                        IndexName='DeviceAlerts',
                        KeyConditionExpression=Key('deviceId').eq(device_id)
                    )
                    
                    alerts = response.get('Items', [])
                    
                    for alert in alerts:
                        alert_id = alert.get('alertId')
                        if alert_id:
                            try:
                                alerts_table.delete_item(Key={'alertId': alert_id})
                                total_count += 1
                            except Exception:
                                pass
                    
                except Exception as e:
                    logger.log(
                        'warning',
                        f'Failed to delete alerts for device {device_id}: {str(e)}',
                        service='gdpr_service',
                        user_id=user_id,
                        device_id=device_id
                    )
                    continue
            
            logger.log(
                'info',
                f'Deleted user alerts',
                service='gdpr_service',
                user_id=user_id,
                deleted_count=total_count
            )
            
            return total_count
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to delete user alerts: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                error=str(e)
            )
            return 0
    
    def _delete_service_requests(self, user_id: str) -> int:
        """
        Delete all service requests associated with the user.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Number of service requests deleted
        """
        try:
            table = self.dynamodb.Table(self.service_requests_table_name)
            total_count = 0
            
            # Query by consumer ID
            try:
                response = table.query(
                    IndexName='ConsumerIndex',
                    KeyConditionExpression=Key('consumerId').eq(user_id)
                )
                
                for item in response.get('Items', []):
                    request_id = item.get('requestId')
                    if request_id:
                        try:
                            table.delete_item(Key={'requestId': request_id})
                            total_count += 1
                        except Exception:
                            pass
            except Exception:
                pass  # Index might not exist
            
            # Also check if user is a technician
            try:
                tech_response = table.query(
                    IndexName='TechnicianIndex',
                    KeyConditionExpression=Key('technicianId').eq(user_id)
                )
                
                for item in tech_response.get('Items', []):
                    request_id = item.get('requestId')
                    if request_id:
                        try:
                            table.delete_item(Key={'requestId': request_id})
                            total_count += 1
                        except Exception:
                            pass
            except Exception:
                pass  # Index might not exist or user might not be a technician
            
            logger.log(
                'info',
                f'Deleted service requests',
                service='gdpr_service',
                user_id=user_id,
                deleted_count=total_count
            )
            
            return total_count
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to delete service requests: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                error=str(e)
            )
            return 0
    
    def _delete_user_consents(self, user_id: str) -> int:
        """
        Delete user consent records.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Number of consent records deleted (0 or 1)
        """
        try:
            table = self.dynamodb.Table(self.user_consents_table_name)
            response = table.delete_item(
                Key={'user_id': user_id},
                ReturnValues='ALL_OLD'
            )
            
            deleted = 1 if 'Attributes' in response else 0
            
            logger.log(
                'info',
                f'Deleted user consents',
                service='gdpr_service',
                user_id=user_id,
                deleted_count=deleted
            )
            
            return deleted
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to delete user consents: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                error=str(e)
            )
            return 0
    
    def _anonymize_audit_logs(self, user_id: str) -> int:
        """
        Anonymize audit logs by replacing user_id with hashed value.
        
        Audit logs cannot be deleted for compliance reasons, but we can
        anonymize the user_id to protect privacy.
        
        Args:
            user_id: The user identifier
            
        Returns:
            Number of audit logs anonymized
        """
        try:
            table = self.dynamodb.Table(self.audit_logs_table_name)
            
            # Generate anonymized ID
            anonymized_id = f"DELETED_{hashlib.sha256(user_id.encode()).hexdigest()[:16]}"
            
            # Query audit logs by user_id
            response = table.query(
                IndexName='user_id-timestamp-index',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            
            count = 0
            
            # Update each audit log
            for item in response.get('Items', []):
                log_id = item.get('log_id')
                timestamp = item.get('timestamp')
                
                if log_id and timestamp:
                    try:
                        table.update_item(
                            Key={
                                'log_id': log_id,
                                'timestamp': timestamp
                            },
                            UpdateExpression='SET user_id = :anon_id, anonymized = :true, anonymized_at = :timestamp',
                            ExpressionAttributeValues={
                                ':anon_id': anonymized_id,
                                ':true': True,
                                ':timestamp': datetime.utcnow().isoformat()
                            }
                        )
                        count += 1
                    except Exception as e:
                        logger.log(
                            'warning',
                            f'Failed to anonymize audit log {log_id}: {str(e)}',
                            service='gdpr_service',
                            user_id=user_id,
                            log_id=log_id
                        )
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = table.query(
                    IndexName='user_id-timestamp-index',
                    KeyConditionExpression=Key('user_id').eq(user_id),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                
                for item in response.get('Items', []):
                    log_id = item.get('log_id')
                    timestamp = item.get('timestamp')
                    
                    if log_id and timestamp:
                        try:
                            table.update_item(
                                Key={
                                    'log_id': log_id,
                                    'timestamp': timestamp
                                },
                                UpdateExpression='SET user_id = :anon_id, anonymized = :true, anonymized_at = :timestamp',
                                ExpressionAttributeValues={
                                    ':anon_id': anonymized_id,
                                    ':true': True,
                                    ':timestamp': datetime.utcnow().isoformat()
                                }
                            )
                            count += 1
                        except Exception:
                            pass
            
            logger.log(
                'info',
                f'Anonymized audit logs',
                service='gdpr_service',
                user_id=user_id,
                anonymized_count=count,
                anonymized_id=anonymized_id
            )
            
            return count
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to anonymize audit logs: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                error=str(e)
            )
            return 0
    
    def _delete_cognito_user(self, user_id: str) -> int:
        """
        Delete user account from Cognito User Pool.
        
        Args:
            user_id: The user identifier (Cognito sub)
            
        Returns:
            Number of accounts deleted (0 or 1)
        """
        try:
            if not self.user_pool_id:
                logger.log(
                    'warning',
                    'User pool ID not configured, skipping Cognito deletion',
                    service='gdpr_service',
                    user_id=user_id
                )
                return 0
            
            # Delete user from Cognito
            self.cognito.admin_delete_user(
                UserPoolId=self.user_pool_id,
                Username=user_id
            )
            
            logger.log(
                'info',
                f'Deleted Cognito user account',
                service='gdpr_service',
                user_id=user_id
            )
            
            return 1
            
        except self.cognito.exceptions.UserNotFoundException:
            logger.log(
                'warning',
                'Cognito user not found',
                service='gdpr_service',
                user_id=user_id
            )
            return 0
        except Exception as e:
            logger.log(
                'error',
                f'Failed to delete Cognito user: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                error=str(e)
            )
            return 0
    
    def _store_deletion_record(self, deletion_summary: Dict[str, Any]) -> None:
        """
        Store deletion summary in S3 for compliance record-keeping.
        
        Args:
            deletion_summary: The deletion summary dictionary
        """
        try:
            if not self.compliance_bucket:
                logger.log(
                    'warning',
                    'Compliance bucket not configured, skipping deletion record storage',
                    service='gdpr_service'
                )
                return
            
            user_id = deletion_summary['deletion_metadata']['user_id']
            request_id = deletion_summary['deletion_metadata']['request_id']
            
            # Store in S3
            record_key = f"gdpr-deletions/{user_id}/{request_id}/{datetime.utcnow().isoformat()}.json"
            
            self.s3.put_object(
                Bucket=self.compliance_bucket,
                Key=record_key,
                Body=json.dumps(deletion_summary, indent=2, default=str),
                ServerSideEncryption='AES256',
                ContentType='application/json',
                Metadata={
                    'user_id': user_id,
                    'request_id': request_id,
                    'deletion_date': deletion_summary['deletion_metadata']['deletion_date']
                }
            )
            
            logger.log(
                'info',
                'Stored deletion record in compliance bucket',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id,
                record_key=record_key
            )
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to store deletion record: {str(e)}',
                service='gdpr_service',
                error=str(e)
            )
            # Don't fail the deletion if record storage fails
    
    def _notify_user(
        self,
        user_id: str,
        user_email: str,
        deletion_summary: Dict[str, Any],
        request_id: str
    ) -> None:
        """
        Send confirmation email to user about data deletion.
        
        Args:
            user_id: The user identifier
            user_email: User's email address
            deletion_summary: The deletion summary
            request_id: The GDPR request ID
        """
        try:
            deleted_counts = deletion_summary.get('deleted_items', {})
            anonymized_counts = deletion_summary.get('anonymized_items', {})
            
            message = {
                'subject': 'Your AquaChain Account Has Been Deleted',
                'body': f'''
Hello,

Your account deletion request (ID: {request_id}) has been completed.

The following data has been permanently deleted:
- Profile: {deleted_counts.get('profile', 0)} record(s)
- Devices: {deleted_counts.get('devices', 0)} device(s)
- Sensor Readings: {deleted_counts.get('readings', 0)} reading(s)
- Alerts: {deleted_counts.get('alerts', 0)} alert(s)
- Service Requests: {deleted_counts.get('service_requests', 0)} request(s)
- Consent Records: {deleted_counts.get('consents', 0)} record(s)
- Cognito Account: {deleted_counts.get('cognito_account', 0)} account(s)

The following data has been anonymized (required for compliance):
- Audit Logs: {anonymized_counts.get('audit_logs', 0)} log(s)

Your account and all associated data have been removed from our systems.
You will no longer be able to log in or access any AquaChain services.

If you did not request this deletion, please contact our support team immediately.

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
                'Deletion confirmation sent to user',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id
            )
            
        except Exception as e:
            logger.log(
                'error',
                f'Failed to send deletion notification: {str(e)}',
                service='gdpr_service',
                user_id=user_id,
                request_id=request_id,
                error=str(e)
            )
            # Don't fail the deletion if notification fails
