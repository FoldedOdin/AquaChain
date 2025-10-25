"""
OTA Firmware Update Manager
Secure over-the-air firmware updates for IoT devices
"""

import os
import json
import boto3
import hashlib
from typing import Dict, Any, List
from datetime import datetime
from botocore.exceptions import ClientError
from job_templates import (
    create_firmware_update_job_document,
    create_rollback_job_document,
    create_gradual_rollout_config,
    create_abort_config,
    create_timeout_config
)

s3 = boto3.client('s3')
iot = boto3.client('iot')
iot_data = boto3.client('iot-data')
dynamodb = boto3.resource('dynamodb')
signer = boto3.client('signer')
sns = boto3.client('sns')

# Environment variables
FIRMWARE_BUCKET = os.environ.get('FIRMWARE_BUCKET', 'aquachain-firmware')
DEVICE_TABLE = os.environ.get('DEVICE_TABLE', 'aquachain-devices')
FIRMWARE_HISTORY_TABLE = os.environ.get('FIRMWARE_HISTORY_TABLE', 'aquachain-firmware-history')
SIGNING_PROFILE_NAME = os.environ.get('SIGNING_PROFILE_NAME', 'aquachain-firmware-signing')
ALERT_TOPIC_ARN = os.environ.get('ALERT_TOPIC_ARN')

device_table = dynamodb.Table(DEVICE_TABLE)
firmware_history_table = dynamodb.Table(FIRMWARE_HISTORY_TABLE)


class OTAUpdateManager:
    """Manage secure OTA firmware updates"""
    
    def __init__(self):
        self.max_rollback_versions = 3
        self.rollout_stages = [
            {'percentage': 10, 'wait_minutes': 30},
            {'percentage': 50, 'wait_minutes': 60},
            {'percentage': 100, 'wait_minutes': 0}
        ]
    
    def sign_firmware(
        self,
        firmware_key: str,
        version: str
    ) -> Dict[str, Any]:
        """
        Sign firmware image using AWS IoT code signing
        
        Args:
            firmware_key: S3 key of firmware image
            version: Firmware version
        
        Returns:
            Signing job details
        """
        job_id = f"firmware-signing-{version}-{int(datetime.utcnow().timestamp())}"
        
        try:
            # Start signing job
            response = signer.start_signing_job(
                source={
                    's3': {
                        'bucketName': FIRMWARE_BUCKET,
                        'key': firmware_key,
                        'version': 'null'
                    }
                },
                destination={
                    's3': {
                        'bucketName': FIRMWARE_BUCKET,
                        'prefix': f'signed/{version}/'
                    }
                },
                profileName=SIGNING_PROFILE_NAME
            )
            
            job_id = response['jobId']
            
            # Wait for signing to complete
            waiter = signer.get_waiter('successful_signing_job')
            waiter.wait(jobId=job_id)
            
            # Get signed firmware details
            job_details = signer.describe_signing_job(jobId=job_id)
            
            signed_key = job_details['signedObject']['s3']['key']
            
            return {
                'job_id': job_id,
                'signed_key': signed_key,
                'status': 'completed',
                'version': version
            }
            
        except ClientError as e:
            print(f"Error signing firmware: {e}")
            return {
                'job_id': job_id,
                'status': 'failed',
                'error': str(e)
            }

    
    def create_firmware_job(
        self,
        firmware_version: str,
        signed_firmware_key: str,
        target_devices: List[str] = None,
        target_all: bool = False,
        rollout_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create IoT Job for firmware update with gradual rollout
        
        Args:
            firmware_version: Version of firmware
            signed_firmware_key: S3 key of signed firmware
            target_devices: List of device IDs to update
            target_all: Update all devices
            rollout_config: Custom rollout configuration
        
        Returns:
            Job details including job_id
        """
        job_id = f"ota-{firmware_version}-{int(datetime.utcnow().timestamp())}"
        
        try:
            # Get firmware metadata
            firmware_obj = s3.head_object(Bucket=FIRMWARE_BUCKET, Key=signed_firmware_key)
            firmware_size = firmware_obj['ContentLength']
            
            # Calculate checksum
            firmware_data = s3.get_object(Bucket=FIRMWARE_BUCKET, Key=signed_firmware_key)
            checksum = hashlib.sha256(firmware_data['Body'].read()).hexdigest()
            
            # Get target devices
            if target_all:
                target_devices = self._get_all_devices()
            elif not target_devices:
                return {'error': 'No target devices specified'}
            
            # Generate presigned URL for firmware download
            download_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': FIRMWARE_BUCKET, 'Key': signed_firmware_key},
                ExpiresIn=7200  # 2 hours
            )
            
            # Create job document using template
            job_document = create_firmware_update_job_document(
                firmware_version=firmware_version,
                firmware_url=download_url,
                firmware_size=firmware_size,
                checksum=checksum
            )
            
            # Configure rollout - use provided config or default gradual rollout
            if not rollout_config:
                # Determine rollout stage based on number of devices
                device_count = len(target_devices)
                if device_count <= 10:
                    rollout = create_gradual_rollout_config('initial')
                elif device_count <= 50:
                    rollout = create_gradual_rollout_config('medium')
                else:
                    rollout = create_gradual_rollout_config('full')
            else:
                rollout = rollout_config
            
            # Create IoT Job with safety configurations
            response = iot.create_job(
                jobId=job_id,
                targets=[f'arn:aws:iot:{os.environ.get("AWS_REGION", "us-east-1")}:{os.environ.get("AWS_ACCOUNT_ID")}:thing/{device_id}' 
                        for device_id in target_devices],
                document=json.dumps(job_document),
                description=f'Firmware update to version {firmware_version}',
                targetSelection='SNAPSHOT',
                jobExecutionsRolloutConfig=rollout,
                timeoutConfig=create_timeout_config(30),
                abortConfig=create_abort_config()
            )
            
            # Store job record
            job_record = {
                'job_id': job_id,
                'firmware_version': firmware_version,
                'firmware_key': signed_firmware_key,
                'firmware_size': firmware_size,
                'checksum': checksum,
                'target_devices': target_devices,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'IN_PROGRESS',
                'job_arn': response['jobArn'],
                'devices_total': len(target_devices),
                'devices_updated': 0,
                'devices_failed': 0,
                'devices_in_progress': 0
            }
            
            firmware_history_table.put_item(Item=job_record)
            
            return {
                'job_id': job_id,
                'job_arn': response['jobArn'],
                'status': 'created',
                'firmware_version': firmware_version,
                'target_devices_count': len(target_devices)
            }
            
        except ClientError as e:
            print(f"Error creating firmware job: {e}")
            return {'error': str(e)}
    
    def track_update_progress(self, job_id: str) -> Dict[str, Any]:
        """
        Track progress of firmware update job
        
        Args:
            job_id: IoT Job identifier
        
        Returns:
            Job progress details
        """
        try:
            # Get job status from IoT
            job_response = iot.describe_job(jobId=job_id)
            job = job_response['job']
            
            # Get job execution summary
            status = job['status']
            job_process_details = job.get('jobProcessDetails', {})
            
            progress = {
                'job_id': job_id,
                'status': status,
                'queued': job_process_details.get('numberOfQueuedThings', 0),
                'in_progress': job_process_details.get('numberOfInProgressThings', 0),
                'succeeded': job_process_details.get('numberOfSucceededThings', 0),
                'failed': job_process_details.get('numberOfFailedThings', 0),
                'rejected': job_process_details.get('numberOfRejectedThings', 0),
                'removed': job_process_details.get('numberOfRemovedThings', 0),
                'canceled': job_process_details.get('numberOfCanceledThings', 0),
                'timed_out': job_process_details.get('numberOfTimedOutThings', 0),
                'created_at': job.get('createdAt', '').isoformat() if job.get('createdAt') else None,
                'last_updated': job.get('lastUpdatedAt', '').isoformat() if job.get('lastUpdatedAt') else None
            }
            
            # Calculate completion percentage
            total = progress['succeeded'] + progress['failed'] + progress['in_progress'] + progress['queued']
            if total > 0:
                progress['completion_percentage'] = (progress['succeeded'] / total) * 100
            else:
                progress['completion_percentage'] = 0
            
            # Update DynamoDB record
            firmware_history_table.update_item(
                Key={'job_id': job_id},
                UpdateExpression='SET #status = :status, devices_updated = :succeeded, devices_failed = :failed, devices_in_progress = :in_progress, last_updated = :ts',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':succeeded': progress['succeeded'],
                    ':failed': progress['failed'],
                    ':in_progress': progress['in_progress'],
                    ':ts': datetime.utcnow().isoformat()
                }
            )
            
            # Check for failures and trigger alerts
            if progress['failed'] > 0 or progress['timed_out'] > 0:
                self._send_update_alert(job_id, progress)
            
            return progress
            
        except ClientError as e:
            print(f"Error tracking update progress: {e}")
            return {'error': str(e)}
    
    def create_ota_update(
        self,
        firmware_version: str,
        signed_firmware_key: str,
        target_devices: List[str] = None,
        target_all: bool = False
    ) -> Dict[str, Any]:
        """
        Legacy method - redirects to create_firmware_job
        
        Args:
            firmware_version: Version of firmware
            signed_firmware_key: S3 key of signed firmware
            target_devices: List of device IDs to update
            target_all: Update all devices
        
        Returns:
            OTA update details
        """
        return self.create_firmware_job(
            firmware_version=firmware_version,
            signed_firmware_key=signed_firmware_key,
            target_devices=target_devices,
            target_all=target_all
        )
    
    def _notify_device_update(
        self,
        device_id: str,
        version: str,
        firmware_key: str,
        checksum: str
    ):
        """Notify device of available firmware update via shadow"""
        try:
            # Verify device certificate before providing update
            if not self._verify_device_certificate(device_id):
                print(f"Device {device_id} certificate verification failed")
                return
            
            # Generate presigned URL for firmware download
            download_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': FIRMWARE_BUCKET, 'Key': firmware_key},
                ExpiresIn=3600  # 1 hour
            )
            
            # Update device shadow
            shadow_update = {
                'state': {
                    'desired': {
                        'firmware': {
                            'version': version,
                            'url': download_url,
                            'checksum': checksum,
                            'update_available': True
                        }
                    }
                }
            }
            
            iot_data.update_thing_shadow(
                thingName=device_id,
                payload=json.dumps(shadow_update)
            )
            
            print(f"Notified device {device_id} of firmware update {version}")
            
        except ClientError as e:
            print(f"Error notifying device {device_id}: {e}")
    
    def _verify_device_certificate(self, device_id: str) -> bool:
        """Verify device certificate is valid"""
        try:
            # Get device principal (certificate)
            response = iot.list_thing_principals(thingName=device_id)
            
            if not response.get('principals'):
                return False
            
            # Check certificate status
            for principal in response['principals']:
                cert_id = principal.split('/')[-1]
                cert_details = iot.describe_certificate(certificateId=cert_id)
                
                if cert_details['certificateDescription']['status'] == 'ACTIVE':
                    return True
            
            return False
            
        except ClientError as e:
            print(f"Error verifying certificate for {device_id}: {e}")
            return False
    
    def handle_update_status(
        self,
        device_id: str,
        firmware_version: str,
        status: str,
        error_message: str = None
    ) -> Dict[str, Any]:
        """
        Handle firmware update status from device
        
        Args:
            device_id: Device identifier
            firmware_version: Firmware version
            status: Update status (success, failed, in_progress)
            error_message: Error message if failed
        
        Returns:
            Status update result
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Update device record
        try:
            if status == 'success':
                # Get current version before updating
                device = device_table.get_item(Key={'device_id': device_id})
                current_version = device.get('Item', {}).get('firmware_version')
                
                # Update device with new version and store previous
                update_expr = 'SET firmware_version = :ver, last_updated = :ts'
                expr_values = {
                    ':ver': firmware_version,
                    ':ts': timestamp
                }
                
                if current_version:
                    update_expr += ', previous_firmware_version = :prev'
                    expr_values[':prev'] = current_version
                
                device_table.update_item(
                    Key={'device_id': device_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeValues=expr_values
                )
                
                # Clear shadow update flag
                shadow_update = {
                    'state': {
                        'desired': {
                            'firmware': {
                                'update_available': False
                            }
                        }
                    }
                }
                iot_data.update_thing_shadow(
                    thingName=device_id,
                    payload=json.dumps(shadow_update)
                )
                
            elif status == 'failed':
                # Log failure
                print(f"Firmware update failed for {device_id}: {error_message}")
                
                # Check if automatic rollback should be triggered
                self._check_and_trigger_rollback(device_id, firmware_version, error_message)
                
                # Send alert
                if ALERT_TOPIC_ARN:
                    sns.publish(
                        TopicArn=ALERT_TOPIC_ARN,
                        Subject=f'Firmware Update Failed: {device_id}',
                        Message=json.dumps({
                            'device_id': device_id,
                            'firmware_version': firmware_version,
                            'error': error_message,
                            'timestamp': timestamp
                        }, indent=2)
                    )
            
            return {
                'device_id': device_id,
                'status': status,
                'timestamp': timestamp
            }
            
        except ClientError as e:
            print(f"Error updating device status: {e}")
            return {'error': str(e)}
    
    def _check_and_trigger_rollback(
        self,
        device_id: str,
        failed_version: str,
        error_message: str
    ):
        """Check if automatic rollback should be triggered"""
        try:
            # Get device info
            device = device_table.get_item(Key={'device_id': device_id})
            
            if 'Item' not in device:
                return
            
            device_data = device['Item']
            previous_version = device_data.get('previous_firmware_version')
            
            # Trigger automatic rollback if previous version exists
            if previous_version:
                print(f"Triggering automatic rollback for {device_id} to version {previous_version}")
                self.rollback_firmware(device_id, previous_version)
                
        except Exception as e:
            print(f"Error checking rollback trigger: {e}")
    
    def _send_update_alert(self, job_id: str, progress: Dict[str, Any]):
        """Send alert for update failures"""
        if not ALERT_TOPIC_ARN:
            return
        
        try:
            sns.publish(
                TopicArn=ALERT_TOPIC_ARN,
                Subject=f'Firmware Update Issues Detected: {job_id}',
                Message=json.dumps({
                    'job_id': job_id,
                    'failed_devices': progress['failed'],
                    'timed_out_devices': progress['timed_out'],
                    'completion_percentage': progress['completion_percentage'],
                    'timestamp': datetime.utcnow().isoformat()
                }, indent=2)
            )
        except ClientError as e:
            print(f"Error sending update alert: {e}")
    
    def rollback_firmware(
        self,
        device_id: str,
        target_version: str = None
    ) -> Dict[str, Any]:
        """
        Rollback device firmware to previous version
        
        Args:
            device_id: Device identifier
            target_version: Specific version to rollback to (optional)
        
        Returns:
            Rollback operation result
        """
        try:
            # Get device current version
            device = device_table.get_item(Key={'device_id': device_id})
            
            if 'Item' not in device:
                return {'error': 'Device not found'}
            
            current_version = device['Item'].get('firmware_version')
            previous_version = device['Item'].get('previous_firmware_version')
            
            # Determine rollback version
            if target_version:
                rollback_version = target_version
            elif previous_version:
                rollback_version = previous_version
            else:
                return {'error': 'No previous version available for rollback'}
            
            # Get firmware details for rollback version
            # Query firmware history for the rollback version
            history_response = firmware_history_table.scan(
                FilterExpression='firmware_version = :ver',
                ExpressionAttributeValues={':ver': rollback_version},
                Limit=1
            )
            
            if not history_response.get('Items'):
                return {'error': f'Firmware version {rollback_version} not found in history'}
            
            rollback_firmware = history_response['Items'][0]
            
            # Create rollback job
            job_id = f"rollback-{device_id}-{int(datetime.utcnow().timestamp())}"
            
            # Generate presigned URL
            download_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': FIRMWARE_BUCKET, 'Key': rollback_firmware['firmware_key']},
                ExpiresIn=3600
            )
            
            # Create job document using template
            job_document = create_rollback_job_document(
                firmware_version=rollback_version,
                firmware_url=download_url,
                firmware_size=rollback_firmware.get('firmware_size', 0),
                checksum=rollback_firmware.get('checksum', ''),
                reason='manual_rollback'
            )
            
            # Create IoT Job for single device
            response = iot.create_job(
                jobId=job_id,
                targets=[f'arn:aws:iot:{os.environ.get("AWS_REGION", "us-east-1")}:{os.environ.get("AWS_ACCOUNT_ID")}:thing/{device_id}'],
                document=json.dumps(job_document),
                description=f'Rollback firmware from {current_version} to {rollback_version}',
                targetSelection='SNAPSHOT',
                timeoutConfig={
                    'inProgressTimeoutInMinutes': 15
                }
            )
            
            # Log rollback
            firmware_history_table.put_item(Item={
                'job_id': job_id,
                'firmware_version': rollback_version,
                'firmware_key': rollback_firmware['firmware_key'],
                'target_devices': [device_id],
                'created_at': datetime.utcnow().isoformat(),
                'status': 'IN_PROGRESS',
                'operation_type': 'rollback',
                'previous_version': current_version
            })
            
            # Send alert
            if ALERT_TOPIC_ARN:
                sns.publish(
                    TopicArn=ALERT_TOPIC_ARN,
                    Subject=f'Firmware Rollback Initiated: {device_id}',
                    Message=json.dumps({
                        'device_id': device_id,
                        'current_version': current_version,
                        'rollback_version': rollback_version,
                        'job_id': job_id,
                        'timestamp': datetime.utcnow().isoformat()
                    }, indent=2)
                )
            
            return {
                'device_id': device_id,
                'current_version': current_version,
                'rollback_version': rollback_version,
                'job_id': job_id,
                'status': 'rollback_initiated'
            }
            
        except ClientError as e:
            print(f"Error rolling back firmware: {e}")
            return {'error': str(e)}
    
    def _get_all_devices(self) -> List[str]:
        """Get all registered device IDs"""
        try:
            response = device_table.scan(
                ProjectionExpression='device_id'
            )
            return [item['device_id'] for item in response.get('Items', [])]
        except ClientError as e:
            print(f"Error getting devices: {e}")
            return []
    
    def get_firmware_status(self, update_id: str) -> Dict[str, Any]:
        """Get status of firmware update"""
        try:
            response = firmware_history_table.get_item(Key={'update_id': update_id})
            
            if 'Item' not in response:
                return {'error': 'Update not found'}
            
            return response['Item']
            
        except ClientError as e:
            return {'error': str(e)}
    
    def monitor_and_rollback_failed_updates(self) -> Dict[str, Any]:
        """
        Monitor for failed updates and trigger automatic rollback
        Should be called periodically (e.g., via EventBridge schedule)
        
        Returns:
            Summary of rollback actions taken
        """
        rollback_actions = []
        
        try:
            # Get all in-progress jobs
            jobs_response = iot.list_jobs(status='IN_PROGRESS', maxResults=50)
            
            for job_summary in jobs_response.get('jobs', []):
                job_id = job_summary['jobId']
                
                # Get detailed job status
                progress = self.track_update_progress(job_id)
                
                # Check for failure conditions
                total_devices = (progress['succeeded'] + progress['failed'] + 
                               progress['in_progress'] + progress['queued'])
                
                if total_devices == 0:
                    continue
                
                failure_rate = (progress['failed'] + progress['timed_out']) / total_devices
                
                # If failure rate exceeds threshold, trigger rollback for failed devices
                if failure_rate > 0.3:  # 30% failure rate
                    print(f"High failure rate detected for job {job_id}: {failure_rate:.1%}")
                    
                    # Get failed device executions
                    executions = iot.list_job_executions_for_job(
                        jobId=job_id,
                        status='FAILED'
                    )
                    
                    for execution in executions.get('executionSummaries', []):
                        thing_arn = execution['thingArn']
                        device_id = thing_arn.split('/')[-1]
                        
                        # Trigger rollback
                        rollback_result = self.rollback_firmware(device_id)
                        
                        if 'error' not in rollback_result:
                            rollback_actions.append({
                                'device_id': device_id,
                                'job_id': job_id,
                                'action': 'rollback_triggered',
                                'rollback_job_id': rollback_result.get('job_id')
                            })
            
            return {
                'rollbacks_triggered': len(rollback_actions),
                'actions': rollback_actions,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            print(f"Error monitoring failed updates: {e}")
            return {'error': str(e)}


def lambda_handler(event, context):
    """
    Lambda handler for OTA firmware updates
    
    Event types:
    - sign_firmware: Sign firmware image
    - create_firmware_job: Create IoT Job for firmware update
    - create_update: Legacy - Create OTA update
    - track_progress: Track job progress
    - update_status: Handle device update status
    - rollback: Rollback firmware
    - get_status: Get update status
    """
    manager = OTAUpdateManager()
    
    action = event.get('action')
    
    try:
        if action == 'sign_firmware':
            result = manager.sign_firmware(
                firmware_key=event['firmware_key'],
                version=event['version']
            )
            
        elif action == 'create_firmware_job':
            result = manager.create_firmware_job(
                firmware_version=event['firmware_version'],
                signed_firmware_key=event['signed_firmware_key'],
                target_devices=event.get('target_devices'),
                target_all=event.get('target_all', False),
                rollout_config=event.get('rollout_config')
            )
            
        elif action == 'create_update':
            result = manager.create_ota_update(
                firmware_version=event['firmware_version'],
                signed_firmware_key=event['signed_firmware_key'],
                target_devices=event.get('target_devices'),
                target_all=event.get('target_all', False)
            )
            
        elif action == 'track_progress':
            result = manager.track_update_progress(event['job_id'])
            
        elif action == 'update_status':
            result = manager.handle_update_status(
                device_id=event['device_id'],
                firmware_version=event['firmware_version'],
                status=event['status'],
                error_message=event.get('error_message')
            )
            
        elif action == 'rollback':
            result = manager.rollback_firmware(
                device_id=event['device_id'],
                target_version=event.get('target_version')
            )
            
        elif action == 'get_status':
            result = manager.get_firmware_status(event['update_id'])
            
        elif action == 'monitor_rollback':
            result = manager.monitor_and_rollback_failed_updates()
            
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown action: {action}'})
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str)
        }
        
    except Exception as e:
        print(f"Error in OTA update manager: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
