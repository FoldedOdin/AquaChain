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

    
    def create_ota_update(
        self,
        firmware_version: str,
        signed_firmware_key: str,
        target_devices: List[str] = None,
        target_all: bool = False
    ) -> Dict[str, Any]:
        """
        Create OTA update for devices
        
        Args:
            firmware_version: Version of firmware
            signed_firmware_key: S3 key of signed firmware
            target_devices: List of device IDs to update
            target_all: Update all devices
        
        Returns:
            OTA update details
        """
        update_id = f"ota-{firmware_version}-{int(datetime.utcnow().timestamp())}"
        
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
        
        # Create update record
        update_record = {
            'update_id': update_id,
            'firmware_version': firmware_version,
            'firmware_key': signed_firmware_key,
            'firmware_size': firmware_size,
            'checksum': checksum,
            'target_devices': target_devices,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'in_progress',
            'devices_updated': 0,
            'devices_failed': 0
        }
        
        firmware_history_table.put_item(Item=update_record)
        
        # Notify devices via shadow update
        for device_id in target_devices:
            self._notify_device_update(device_id, firmware_version, signed_firmware_key, checksum)
        
        return update_record
    
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
                device_table.update_item(
                    Key={'device_id': device_id},
                    UpdateExpression='SET firmware_version = :ver, last_updated = :ts',
                    ExpressionAttributeValues={
                        ':ver': firmware_version,
                        ':ts': timestamp
                    }
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
            
            # Get firmware history
            history = firmware_history_table.query(
                IndexName='device-version-index',
                KeyConditionExpression='device_id = :did',
                ExpressionAttributeValues={':did': device_id},
                ScanIndexForward=False,  # Most recent first
                Limit=self.max_rollback_versions + 1
            )
            
            versions = history.get('Items', [])
            
            if len(versions) < 2:
                return {'error': 'No previous version available for rollback'}
            
            # Determine rollback version
            if target_version:
                rollback_version = next(
                    (v for v in versions if v['firmware_version'] == target_version),
                    None
                )
                if not rollback_version:
                    return {'error': f'Version {target_version} not found in history'}
            else:
                # Rollback to previous version
                rollback_version = versions[1]
            
            # Initiate rollback update
            result = self._notify_device_update(
                device_id,
                rollback_version['firmware_version'],
                rollback_version['firmware_key'],
                rollback_version['checksum']
            )
            
            return {
                'device_id': device_id,
                'current_version': current_version,
                'rollback_version': rollback_version['firmware_version'],
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


def lambda_handler(event, context):
    """
    Lambda handler for OTA firmware updates
    
    Event types:
    - sign_firmware: Sign firmware image
    - create_update: Create OTA update
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
            
        elif action == 'create_update':
            result = manager.create_ota_update(
                firmware_version=event['firmware_version'],
                signed_firmware_key=event['signed_firmware_key'],
                target_devices=event.get('target_devices'),
                target_all=event.get('target_all', False)
            )
            
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
