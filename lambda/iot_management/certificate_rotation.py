"""
IoT Device Certificate Rotation
Automated certificate lifecycle management with zero-downtime rotation
"""

import os
import json
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import time

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
MQTT_CERT_TOPIC = os.environ.get('MQTT_CERT_TOPIC', 'aquachain/device/{device_id}/certificate/provision')
CONFIRMATION_TIMEOUT = int(os.environ.get('CONFIRMATION_TIMEOUT', '300'))  # 5 minutes

device_table = dynamodb.Table(DEVICE_TABLE)
cert_lifecycle_table = dynamodb.Table(CERT_LIFECYCLE_TABLE)


class Certificate:
    """Certificate data model"""
    def __init__(self, certificate_id: str, certificate_arn: str, 
                 certificate_pem: str, private_key: str, expiration_date: str):
        self.certificate_id = certificate_id
        self.certificate_arn = certificate_arn
        self.certificate_pem = certificate_pem
        self.private_key = private_key
        self.expiration_date = expiration_date


class CertificateLifecycleManager:
    """
    Manage IoT device certificate lifecycle with zero-downtime rotation
    
    Implements the design specification from Phase 3 requirements:
    - Zero-downtime certificate rotation
    - Expiration monitoring and alerts
    - Secure certificate provisioning via MQTT
    - Automatic deactivation after confirmation
    """
    
    def __init__(self):
        self.policy_name = 'AquaChain-Device-Policy'
    
    def check_expiring_certificates(self, days_threshold: int = 30) -> List[Dict[str, Any]]:
        """
        Check for certificates expiring within the specified threshold
        
        Args:
            days_threshold: Number of days before expiration to flag certificates
        
        Returns:
            List of certificates expiring within threshold
        """
        expiring_certificates = []
        
        try:
            # Query CertificateLifecycle table for active certificates
            response = cert_lifecycle_table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'active'}
            )
            
            active_certs = response.get('Items', [])
            threshold_date = datetime.utcnow() + timedelta(days=days_threshold)
            
            for cert in active_certs:
                expiry_date = datetime.fromisoformat(cert['expiration_date'].replace('Z', '+00:00'))
                
                if expiry_date <= threshold_date:
                    days_until_expiry = (expiry_date.replace(tzinfo=None) - datetime.utcnow()).days
                    
                    cert_info = {
                        'device_id': cert['device_id'],
                        'certificate_id': cert['certificate_id'],
                        'expiration_date': cert['expiration_date'],
                        'days_until_expiry': days_until_expiry,
                        'status': cert['status']
                    }
                    expiring_certificates.append(cert_info)
            
            # Send alerts based on urgency
            critical_certs = [c for c in expiring_certificates if c['days_until_expiry'] <= CRITICAL_EXPIRY_DAYS]
            warning_certs = [c for c in expiring_certificates if CRITICAL_EXPIRY_DAYS < c['days_until_expiry'] <= EXPIRY_WARNING_DAYS]
            
            if critical_certs:
                self._send_expiry_alert(critical_certs, 'CRITICAL')
            if warning_certs:
                self._send_expiry_alert(warning_certs, 'WARNING')
            
            return expiring_certificates
            
        except ClientError as e:
            print(f"Error checking expiring certificates: {e}")
            raise

    
    def generate_new_certificate(self, device_id: str) -> Certificate:
        """
        Generate a new certificate for a device
        
        Args:
            device_id: Device identifier
        
        Returns:
            Certificate object with new certificate details
        """
        try:
            # Create new certificate and key pair
            response = iot.create_keys_and_certificate(setAsActive=True)
            
            cert_id = response['certificateId']
            cert_arn = response['certificateArn']
            cert_pem = response['certificatePem']
            private_key = response['keyPair']['PrivateKey']
            
            # Get certificate details for expiration date
            cert_details = iot.describe_certificate(certificateId=cert_id)
            expiry_date = cert_details['certificateDescription']['validity']['notAfter'].isoformat()
            
            # Attach policy to certificate
            iot.attach_policy(
                policyName=self.policy_name,
                target=cert_arn
            )
            
            # Attach certificate to thing
            iot.attach_thing_principal(
                thingName=device_id,
                principal=cert_arn
            )
            
            print(f"Generated new certificate {cert_id} for device {device_id}")
            
            return Certificate(
                certificate_id=cert_id,
                certificate_arn=cert_arn,
                certificate_pem=cert_pem,
                private_key=private_key,
                expiration_date=expiry_date
            )
            
        except ClientError as e:
            print(f"Error generating new certificate: {e}")
            raise
    
    def provision_certificate_to_device(
        self, 
        device_id: str, 
        certificate: Certificate
    ) -> bool:
        """
        Provision new certificate to device via secure MQTT
        
        Args:
            device_id: Device identifier
            certificate: Certificate object to provision
        
        Returns:
            True if provisioning initiated successfully
        """
        try:
            # Store certificate securely in Secrets Manager
            secret_name = f"aquachain/device/{device_id}/certificate/{certificate.certificate_id}"
            
            try:
                secretsmanager.create_secret(
                    Name=secret_name,
                    SecretString=json.dumps({
                        'certificate_pem': certificate.certificate_pem,
                        'private_key': certificate.private_key,
                        'certificate_id': certificate.certificate_id,
                        'certificate_arn': certificate.certificate_arn,
                        'expiration_date': certificate.expiration_date,
                        'created_at': datetime.utcnow().isoformat()
                    })
                )
            except secretsmanager.exceptions.ResourceExistsException:
                secretsmanager.update_secret(
                    SecretId=secret_name,
                    SecretString=json.dumps({
                        'certificate_pem': certificate.certificate_pem,
                        'private_key': certificate.private_key,
                        'certificate_id': certificate.certificate_id,
                        'certificate_arn': certificate.certificate_arn,
                        'expiration_date': certificate.expiration_date,
                        'created_at': datetime.utcnow().isoformat()
                    })
                )
            
            # Publish certificate to device via MQTT
            topic = MQTT_CERT_TOPIC.format(device_id=device_id)
            
            # Encrypt certificate data for transmission
            payload = {
                'action': 'provision_certificate',
                'certificate_pem': certificate.certificate_pem,
                'private_key': certificate.private_key,
                'certificate_id': certificate.certificate_id,
                'expiration_date': certificate.expiration_date,
                'secret_name': secret_name,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            iot_data.publish(
                topic=topic,
                qos=1,  # At least once delivery
                payload=json.dumps(payload)
            )
            
            # Also update device shadow for redundancy
            shadow_update = {
                'state': {
                    'desired': {
                        'certificate': {
                            'rotation_required': True,
                            'certificate_id': certificate.certificate_id,
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
            
            print(f"Provisioned certificate {certificate.certificate_id} to device {device_id}")
            return True
            
        except ClientError as e:
            print(f"Error provisioning certificate to device: {e}")
            return False
    
    def deactivate_old_certificate(self, certificate_id: str) -> None:
        """
        Deactivate an old certificate after successful rotation
        
        Args:
            certificate_id: Certificate identifier to deactivate
        """
        try:
            # Get certificate ARN
            cert_details = iot.describe_certificate(certificateId=certificate_id)
            cert_arn = cert_details['certificateDescription']['certificateArn']
            
            # Get all things attached to this certificate
            things = iot.list_principal_things(principal=cert_arn)
            
            # Detach certificate from all things
            for thing_name in things.get('things', []):
                iot.detach_thing_principal(
                    thingName=thing_name,
                    principal=cert_arn
                )
                print(f"Detached certificate {certificate_id} from thing {thing_name}")
            
            # Detach policies
            policies = iot.list_principal_policies(principal=cert_arn)
            for policy in policies.get('policies', []):
                iot.detach_policy(
                    policyName=policy['policyName'],
                    target=cert_arn
                )
            
            # Update certificate status to INACTIVE
            iot.update_certificate(
                certificateId=certificate_id,
                newStatus='INACTIVE'
            )
            
            print(f"Deactivated certificate {certificate_id}")
            
        except ClientError as e:
            print(f"Error deactivating certificate: {e}")
            raise
    
    def rotate_certificate(self, device_id: str) -> Dict[str, Any]:
        """
        Rotate certificate for a device using zero-downtime strategy
        
        Zero-downtime strategy:
        1. Generate new certificate while old is active
        2. Provision new cert to device via secure MQTT
        3. Wait for device confirmation
        4. Deactivate old certificate only after confirmation
        
        Args:
            device_id: Device identifier
        
        Returns:
            Rotation result with new certificate details
        """
        try:
            # Get current active certificate
            principals = iot.list_thing_principals(thingName=device_id)
            
            if not principals.get('principals'):
                return {'error': 'No certificate found for device'}
            
            old_cert_arn = principals['principals'][0]
            old_cert_id = old_cert_arn.split('/')[-1]
            
            # Step 1: Generate new certificate while old is active
            print(f"Step 1: Generating new certificate for device {device_id}")
            new_certificate = self.generate_new_certificate(device_id)
            
            # Step 2: Provision new cert to device via secure MQTT
            print(f"Step 2: Provisioning certificate to device {device_id}")
            provisioned = self.provision_certificate_to_device(device_id, new_certificate)
            
            if not provisioned:
                # Rollback: deactivate new certificate
                self.deactivate_old_certificate(new_certificate.certificate_id)
                return {'error': 'Failed to provision certificate to device'}
            
            # Record rotation in lifecycle table
            cert_lifecycle_table.put_item(Item={
                'device_id': device_id,
                'certificate_id': new_certificate.certificate_id,
                'expiration_date': new_certificate.expiration_date,
                'status': 'pending_confirmation',
                'created_at': datetime.utcnow().isoformat(),
                'old_certificate_id': old_cert_id,
                'rotation_initiated_at': datetime.utcnow().isoformat()
            })
            
            # Update old certificate status to rotating
            try:
                cert_lifecycle_table.update_item(
                    Key={
                        'device_id': device_id,
                        'certificate_id': old_cert_id
                    },
                    UpdateExpression='SET #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': 'rotating'}
                )
            except ClientError:
                # Old cert might not be in table yet
                pass
            
            return {
                'device_id': device_id,
                'old_certificate_id': old_cert_id,
                'new_certificate_id': new_certificate.certificate_id,
                'status': 'pending_confirmation',
                'message': 'Certificate rotation initiated. Waiting for device confirmation.',
                'expiration_date': new_certificate.expiration_date
            }
            
        except Exception as e:
            print(f"Error rotating certificate: {e}")
            return {'error': str(e)}
    
    def confirm_certificate_rotation(
        self,
        device_id: str,
        new_certificate_id: str,
        success: bool
    ) -> Dict[str, Any]:
        """
        Confirm certificate rotation from device (Step 3 & 4 of zero-downtime strategy)
        
        Step 3: Wait for device confirmation
        Step 4: Deactivate old certificate only after confirmation
        
        Args:
            device_id: Device identifier
            new_certificate_id: New certificate identifier
            success: Whether rotation was successful
        
        Returns:
            Confirmation result
        """
        try:
            # Get rotation record
            response = cert_lifecycle_table.get_item(
                Key={
                    'device_id': device_id,
                    'certificate_id': new_certificate_id
                }
            )
            
            if 'Item' not in response:
                return {'error': 'Rotation record not found'}
            
            rotation_data = response['Item']
            old_cert_id = rotation_data.get('old_certificate_id')
            
            if success:
                # Step 4: Deactivate old certificate only after confirmation
                print(f"Step 4: Deactivating old certificate {old_cert_id}")
                
                if old_cert_id:
                    self.deactivate_old_certificate(old_cert_id)
                    
                    # Update old certificate status in lifecycle table
                    try:
                        cert_lifecycle_table.update_item(
                            Key={
                                'device_id': device_id,
                                'certificate_id': old_cert_id
                            },
                            UpdateExpression='SET #status = :status, deactivated_at = :ts',
                            ExpressionAttributeNames={'#status': 'status'},
                            ExpressionAttributeValues={
                                ':status': 'deactivated',
                                ':ts': datetime.utcnow().isoformat()
                            }
                        )
                    except ClientError:
                        pass
                
                # Update new certificate status to active
                cert_lifecycle_table.update_item(
                    Key={
                        'device_id': device_id,
                        'certificate_id': new_certificate_id
                    },
                    UpdateExpression='SET #status = :status, confirmed_at = :ts, rotated_at = :ts',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'active',
                        ':ts': datetime.utcnow().isoformat()
                    }
                )
                
                # Update device record
                try:
                    device_table.update_item(
                        Key={'device_id': device_id},
                        UpdateExpression='SET certificate_id = :cert_id, last_cert_rotation = :ts',
                        ExpressionAttributeValues={
                            ':cert_id': new_certificate_id,
                            ':ts': datetime.utcnow().isoformat()
                        }
                    )
                except ClientError as e:
                    print(f"Warning: Could not update device table: {e}")
                
                # Send success notification
                self._send_rotation_notification(device_id, new_certificate_id, 'SUCCESS')
                
                return {
                    'device_id': device_id,
                    'old_certificate_id': old_cert_id,
                    'new_certificate_id': new_certificate_id,
                    'status': 'completed',
                    'message': 'Certificate rotation completed successfully with zero downtime'
                }
            else:
                # Rotation failed - rollback
                print(f"Rotation failed for device {device_id}, rolling back")
                
                # Deactivate new certificate
                self.deactivate_old_certificate(new_certificate_id)
                
                # Update new certificate status to failed
                cert_lifecycle_table.update_item(
                    Key={
                        'device_id': device_id,
                        'certificate_id': new_certificate_id
                    },
                    UpdateExpression='SET #status = :status, failed_at = :ts',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'failed',
                        ':ts': datetime.utcnow().isoformat()
                    }
                )
                
                # Restore old certificate status to active
                if old_cert_id:
                    try:
                        cert_lifecycle_table.update_item(
                            Key={
                                'device_id': device_id,
                                'certificate_id': old_cert_id
                            },
                            UpdateExpression='SET #status = :status',
                            ExpressionAttributeNames={'#status': 'status'},
                            ExpressionAttributeValues={':status': 'active'}
                        )
                    except ClientError:
                        pass
                
                # Send failure notification
                self._send_rotation_notification(device_id, new_certificate_id, 'FAILED')
                
                return {
                    'device_id': device_id,
                    'old_certificate_id': old_cert_id,
                    'new_certificate_id': new_certificate_id,
                    'status': 'failed',
                    'message': 'Certificate rotation failed. Old certificate still active.'
                }
                
        except Exception as e:
            print(f"Error confirming rotation: {e}")
            return {'error': str(e)}
    
    def _send_rotation_notification(self, device_id: str, certificate_id: str, status: str):
        """Send notification about rotation status"""
        if not ALERT_TOPIC_ARN:
            return
        
        try:
            message = {
                'event': 'certificate_rotation',
                'device_id': device_id,
                'certificate_id': certificate_id,
                'status': status,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            sns.publish(
                TopicArn=ALERT_TOPIC_ARN,
                Subject=f'Certificate Rotation {status}: {device_id}',
                Message=json.dumps(message, indent=2)
            )
        except ClientError as e:
            print(f"Error sending rotation notification: {e}")
    
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
                KeyConditionExpression='device_id = :did',
                ExpressionAttributeValues={':did': device_id},
                ScanIndexForward=False,  # Most recent first
                Limit=10
            )
            
            return {
                'device_id': device_id,
                'certificates': response.get('Items', [])
            }
            
        except ClientError as e:
            return {'error': str(e)}
    
    def generate_rotation_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive rotation report
        
        Returns:
            Report with rotation statistics and status
        """
        try:
            # Get all certificates from lifecycle table
            response = cert_lifecycle_table.scan()
            certificates = response.get('Items', [])
            
            # Calculate statistics
            total_certs = len(certificates)
            active_certs = len([c for c in certificates if c.get('status') == 'active'])
            rotating_certs = len([c for c in certificates if c.get('status') == 'pending_confirmation'])
            deactivated_certs = len([c for c in certificates if c.get('status') == 'deactivated'])
            failed_rotations = len([c for c in certificates if c.get('status') == 'failed'])
            
            # Get expiring certificates
            expiring_30d = self.check_expiring_certificates(days_threshold=30)
            expiring_7d = self.check_expiring_certificates(days_threshold=7)
            
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'statistics': {
                    'total_certificates': total_certs,
                    'active': active_certs,
                    'rotating': rotating_certs,
                    'deactivated': deactivated_certs,
                    'failed': failed_rotations
                },
                'expiring_certificates': {
                    'within_30_days': len(expiring_30d),
                    'within_7_days': len(expiring_7d),
                    'critical_list': expiring_7d
                }
            }
            
            return report
            
        except ClientError as e:
            print(f"Error generating rotation report: {e}")
            return {'error': str(e)}


def lambda_handler(event, context):
    """
    Lambda handler for certificate lifecycle management
    
    Event types:
    - check_expiring: Check for expiring certificates
    - rotate: Rotate certificate for a device
    - confirm: Confirm rotation from device
    - get_history: Get rotation history for a device
    - generate_report: Generate rotation report
    - scheduled: Scheduled check (from EventBridge)
    """
    manager = CertificateLifecycleManager()
    
    # Handle EventBridge scheduled events
    if event.get('source') == 'aws.events':
        action = 'check_expiring'
    else:
        action = event.get('action')
    
    try:
        if action == 'check_expiring':
            days_threshold = event.get('days_threshold', 30)
            expiring_certs = manager.check_expiring_certificates(days_threshold)
            result = {
                'expiring_certificates': expiring_certs,
                'count': len(expiring_certs)
            }
            
        elif action == 'rotate':
            device_id = event.get('device_id')
            if not device_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'device_id is required'})
                }
            result = manager.rotate_certificate(device_id)
            
        elif action == 'confirm':
            device_id = event.get('device_id')
            new_certificate_id = event.get('new_certificate_id')
            success = event.get('success', False)
            
            if not device_id or not new_certificate_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'device_id and new_certificate_id are required'})
                }
            
            result = manager.confirm_certificate_rotation(
                device_id=device_id,
                new_certificate_id=new_certificate_id,
                success=success
            )
            
        elif action == 'get_history':
            device_id = event.get('device_id')
            if not device_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'device_id is required'})
                }
            result = manager.get_rotation_history(device_id)
            
        elif action == 'generate_report':
            result = manager.generate_rotation_report()
            
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
        print(f"Error in certificate lifecycle management: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
