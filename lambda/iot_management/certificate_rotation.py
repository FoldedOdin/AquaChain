"""
IoT Device Certificate Rotation
Automated certificate lifecycle management
"""

import os
import json
import boto3
from typing import Dict, Any, List
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

iot = boto3.client('iot')
iot_data = boto3.client('iot-data')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
secretsmanager = boto3.client('secretsmanager')

# Environment variables
DEVICE_TABLE = os.environ.get('DEVICE_TABLE', 'aquachain-devices')
CERT_LIFECYCLE_TABLE = os.environ.get('CERT_LIFECYCLE_TABLE', 'aquachain-cert-lifecycle')
ALERT_TOPIC_ARN = os.environ.get('ALERT_TOPIC_ARN')
EXPIRY_WARNING_DAYS = int(os.environ.get('EXPIRY_WARNING_DAYS', '30'))
CRITICAL_EXPIRY_DAYS = int(os.environ.get('CRITICAL_EXPIRY_DAYS', '7'))

device_table = dynamodb.Table(DEVICE_TABLE)
cert_lifecycle_table = dynamodb.Table(CERT_LIFECYCLE_TABLE)


class CertificateRotationManager:
    """Manage IoT device certificate rotation"""
    
    def __init__(self):
        self.policy_name = 'AquaChain-Device-Policy'
    
    def check_certificate_expiry(self) -> Dict[str, Any]:
        """
        Check all device certificates for expiry
        
        Returns:
            Summary of certificates requiring attention
        """
        expiring_soon = []
        expiring_critical = []
        
        try:
            # Get all devices
            devices_response = device_table.scan()
            devices = devices_response.get('Items', [])
            
            for device in devices:
                device_id = device['device_id']
                
                # Get device certificates
                principals = iot.list_thing_principals(thingName=device_id)
                
                for principal in principals.get('principals', []):
                    cert_id = principal.split('/')[-1]
                    cert_details = iot.describe_certificate(certificateId=cert_id)
                    cert_desc = cert_details['certificateDescription']
                    
                    if cert_desc['status'] != 'ACTIVE':
                        continue
                    
                    # Parse expiry date
                    expiry_date = cert_desc['validity']['notAfter']
                    days_until_expiry = (expiry_date.replace(tzinfo=None) - datetime.utcnow()).days
                    
                    cert_info = {
                        'device_id': device_id,
                        'certificate_id': cert_id,
                        'expiry_date': expiry_date.isoformat(),
                        'days_until_expiry': days_until_expiry
                    }
                    
                    if days_until_expiry <= CRITICAL_EXPIRY_DAYS:
                        expiring_critical.append(cert_info)
                    elif days_until_expiry <= EXPIRY_WARNING_DAYS:
                        expiring_soon.append(cert_info)
            
            # Send alerts
            if expiring_critical:
                self._send_expiry_alert(expiring_critical, 'CRITICAL')
            if expiring_soon:
                self._send_expiry_alert(expiring_soon, 'WARNING')
            
            return {
                'total_devices': len(devices),
                'expiring_critical': len(expiring_critical),
                'expiring_soon': len(expiring_soon),
                'critical_certificates': expiring_critical,
                'warning_certificates': expiring_soon
            }
            
        except ClientError as e:
            print(f"Error checking certificate expiry: {e}")
            return {'error': str(e)}

    
    def rotate_certificate(self, device_id: str) -> Dict[str, Any]:
        """
        Rotate certificate for a device
        
        Args:
            device_id: Device identifier
        
        Returns:
            Rotation result with new certificate details
        """
        rotation_id = f"rotation-{device_id}-{int(datetime.utcnow().timestamp())}"
        
        try:
            # Get current certificate
            principals = iot.list_thing_principals(thingName=device_id)
            
            if not principals.get('principals'):
                return {'error': 'No certificate found for device'}
            
            old_cert_arn = principals['principals'][0]
            old_cert_id = old_cert_arn.split('/')[-1]
            
            # Create new certificate
            new_cert_response = iot.create_keys_and_certificate(setAsActive=True)
            
            new_cert_id = new_cert_response['certificateId']
            new_cert_arn = new_cert_response['certificateArn']
            new_cert_pem = new_cert_response['certificatePem']
            new_private_key = new_cert_response['keyPair']['PrivateKey']
            
            # Store new certificate securely in Secrets Manager
            secret_name = f"aquachain/device/{device_id}/certificate"
            try:
                secretsmanager.create_secret(
                    Name=secret_name,
                    SecretString=json.dumps({
                        'certificate_pem': new_cert_pem,
                        'private_key': new_private_key,
                        'certificate_id': new_cert_id,
                        'created_at': datetime.utcnow().isoformat()
                    })
                )
            except secretsmanager.exceptions.ResourceExistsException:
                secretsmanager.update_secret(
                    SecretId=secret_name,
                    SecretString=json.dumps({
                        'certificate_pem': new_cert_pem,
                        'private_key': new_private_key,
                        'certificate_id': new_cert_id,
                        'created_at': datetime.utcnow().isoformat()
                    })
                )
            
            # Attach policy to new certificate
            iot.attach_policy(
                policyName=self.policy_name,
                target=new_cert_arn
            )
            
            # Attach new certificate to thing
            iot.attach_thing_principal(
                thingName=device_id,
                principal=new_cert_arn
            )
            
            # Notify device of new certificate via shadow
            self._notify_device_certificate(device_id, secret_name)
            
            # Log rotation
            cert_lifecycle_table.put_item(Item={
                'rotation_id': rotation_id,
                'device_id': device_id,
                'old_certificate_id': old_cert_id,
                'new_certificate_id': new_cert_id,
                'rotation_date': datetime.utcnow().isoformat(),
                'status': 'pending_confirmation',
                'secret_name': secret_name
            })
            
            return {
                'rotation_id': rotation_id,
                'device_id': device_id,
                'new_certificate_id': new_cert_id,
                'secret_name': secret_name,
                'status': 'pending_confirmation',
                'message': 'New certificate created. Waiting for device confirmation.'
            }
            
        except ClientError as e:
            print(f"Error rotating certificate: {e}")
            return {'error': str(e)}
    
    def confirm_certificate_rotation(
        self,
        rotation_id: str,
        device_id: str,
        success: bool
    ) -> Dict[str, Any]:
        """
        Confirm certificate rotation from device
        
        Args:
            rotation_id: Rotation identifier
            device_id: Device identifier
            success: Whether rotation was successful
        
        Returns:
            Confirmation result
        """
        try:
            # Get rotation record
            rotation = cert_lifecycle_table.get_item(Key={'rotation_id': rotation_id})
            
            if 'Item' not in rotation:
                return {'error': 'Rotation record not found'}
            
            rotation_data = rotation['Item']
            
            if success:
                # Deactivate old certificate
                old_cert_id = rotation_data['old_certificate_id']
                
                # Detach old certificate from thing
                principals = iot.list_thing_principals(thingName=device_id)
                for principal in principals.get('principals', []):
                    if old_cert_id in principal:
                        iot.detach_thing_principal(
                            thingName=device_id,
                            principal=principal
                        )
                        
                        # Update certificate to INACTIVE
                        iot.update_certificate(
                            certificateId=old_cert_id,
                            newStatus='INACTIVE'
                        )
                        break
                
                # Update rotation status
                cert_lifecycle_table.update_item(
                    Key={'rotation_id': rotation_id},
                    UpdateExpression='SET #status = :status, confirmed_at = :ts',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'completed',
                        ':ts': datetime.utcnow().isoformat()
                    }
                )
                
                # Update device record
                device_table.update_item(
                    Key={'device_id': device_id},
                    UpdateExpression='SET certificate_id = :cert_id, last_cert_rotation = :ts',
                    ExpressionAttributeValues={
                        ':cert_id': rotation_data['new_certificate_id'],
                        ':ts': datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    'rotation_id': rotation_id,
                    'device_id': device_id,
                    'status': 'completed',
                    'message': 'Certificate rotation completed successfully'
                }
            else:
                # Rotation failed - rollback
                new_cert_id = rotation_data['new_certificate_id']
                
                # Deactivate new certificate
                iot.update_certificate(
                    certificateId=new_cert_id,
                    newStatus='INACTIVE'
                )
                
                # Update rotation status
                cert_lifecycle_table.update_item(
                    Key={'rotation_id': rotation_id},
                    UpdateExpression='SET #status = :status, confirmed_at = :ts',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'failed',
                        ':ts': datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    'rotation_id': rotation_id,
                    'device_id': device_id,
                    'status': 'failed',
                    'message': 'Certificate rotation failed. Old certificate still active.'
                }
                
        except ClientError as e:
            print(f"Error confirming rotation: {e}")
            return {'error': str(e)}
    
    def _notify_device_certificate(self, device_id: str, secret_name: str):
        """Notify device of new certificate via shadow"""
        try:
            shadow_update = {
                'state': {
                    'desired': {
                        'certificate': {
                            'rotation_required': True,
                            'secret_name': secret_name,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    }
                }
            }
            
            iot_data.update_thing_shadow(
                thingName=device_id,
                payload=json.dumps(shadow_update)
            )
            
            print(f"Notified device {device_id} of certificate rotation")
            
        except ClientError as e:
            print(f"Error notifying device: {e}")
    
    def _send_expiry_alert(self, certificates: List[Dict], severity: str):
        """Send alert for expiring certificates"""
        if not ALERT_TOPIC_ARN:
            return
        
        try:
            message = {
                'severity': severity,
                'certificate_count': len(certificates),
                'certificates': certificates,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            sns.publish(
                TopicArn=ALERT_TOPIC_ARN,
                Subject=f'{severity}: Device Certificates Expiring',
                Message=json.dumps(message, indent=2)
            )
        except ClientError as e:
            print(f"Error sending alert: {e}")
    
    def get_rotation_history(self, device_id: str) -> Dict[str, Any]:
        """Get certificate rotation history for a device"""
        try:
            response = cert_lifecycle_table.query(
                IndexName='device-date-index',
                KeyConditionExpression='device_id = :did',
                ExpressionAttributeValues={':did': device_id},
                ScanIndexForward=False,  # Most recent first
                Limit=10
            )
            
            return {
                'device_id': device_id,
                'rotations': response.get('Items', [])
            }
            
        except ClientError as e:
            return {'error': str(e)}


def lambda_handler(event, context):
    """
    Lambda handler for certificate rotation
    
    Event types:
    - check_expiry: Check all certificates for expiry
    - rotate: Rotate certificate for a device
    - confirm: Confirm rotation from device
    - get_history: Get rotation history
    """
    manager = CertificateRotationManager()
    
    action = event.get('action')
    
    try:
        if action == 'check_expiry':
            result = manager.check_certificate_expiry()
            
        elif action == 'rotate':
            result = manager.rotate_certificate(event['device_id'])
            
        elif action == 'confirm':
            result = manager.confirm_certificate_rotation(
                rotation_id=event['rotation_id'],
                device_id=event['device_id'],
                success=event['success']
            )
            
        elif action == 'get_history':
            result = manager.get_rotation_history(event['device_id'])
            
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
        print(f"Error in certificate rotation: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
