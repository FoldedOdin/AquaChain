#!/usr/bin/env python3
"""
Multi-User ESP32 Device Provisioning Script for AquaChain
Provisions devices with user association for multi-consumer support
"""

import boto3
import json
import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
from botocore.exceptions import ClientError

# Import secure validation module
from device_validation import DeviceValidator, DeviceValidationError


class MultiUserDeviceProvisioner:
    """Handles device provisioning with user association"""
    
    def __init__(self, region='us-east-1'):
        self.region = region
        self.iot_client = boto3.client('iot', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.devices_table = self.dynamodb.Table('AquaChain-Devices-dev')
        self.users_table = self.dynamodb.Table('AquaChain-Users-dev')
    
    def validate_user_exists(self, user_id):
        """Verify user exists before provisioning device"""
        try:
            response = self.users_table.get_item(Key={'userId': user_id})
            if 'Item' not in response:
                raise ValueError(f"User {user_id} does not exist")
            return response['Item']
        except ClientError as e:
            raise ValueError(f"Error validating user: {e}")
    
    def provision_device(self, device_id, user_id, device_metadata=None):
        """
        Provision a new ESP32 device with user association
        
        Args:
            device_id: Unique device identifier
            user_id: Cognito user ID (sub) who owns this device
            device_metadata: Optional dict with location, model, etc.
        """
        print(f"🚀 Provisioning device: {device_id}")
        print(f"👤 Owner: {user_id}")
        print(f"📍 Region: {self.region}")
        print("-" * 60)
        
        try:
            # SECURITY: Validate inputs
            print("🔒 Validating credentials...")
            validated_device_id = DeviceValidator.validate_device_id(device_id)
            validated_user_id = DeviceValidator.validate_user_id(user_id)
            
            # Verify user exists
            user = self.validate_user_exists(validated_user_id)
            print(f"✅ User validated: {user.get('email', 'N/A')}")
            
            # Step 1: Create IoT Thing
            print("1️⃣  Creating IoT Thing...")
            thing_attributes = {
                'deviceType': 'ESP32',
                'firmwareVersion': '1.0.0',
                'userId': user_id,  # ✅ User association in IoT Core
                'createdDate': datetime.utcnow().isoformat()
            }
            
            if device_metadata:
                thing_attributes.update(device_metadata)
            
            try:
                self.iot_client.create_thing(
                    thingName=validated_device_id,
                    thingTypeName='AquaChainWaterSensor',
                    attributePayload={'attributes': thing_attributes}
                )
                print(f"✅ IoT Thing created: {validated_device_id}")
            except self.iot_client.exceptions.ResourceAlreadyExistsException:
                print(f"⚠️  Thing already exists, updating attributes...")
                self.iot_client.update_thing(
                    thingName=validated_device_id,
                    attributePayload={'attributes': thing_attributes}
                )
            
            # Step 2: Create certificate and keys
            print("2️⃣  Creating device certificate...")
            cert_response = self.iot_client.create_keys_and_certificate(setAsActive=True)
            
            certificate_arn = cert_response['certificateArn']
            certificate_id = cert_response['certificateId']
            certificate_pem = cert_response['certificatePem']
            private_key = cert_response['keyPair']['PrivateKey']
            public_key = cert_response['keyPair']['PublicKey']
            
            print(f"✅ Certificate created: {certificate_id}")
            
            # Step 3: Create device-specific policy
            print("3️⃣  Creating device-specific IoT policy...")
            policy_name = f"{validated_device_id}_policy"
            policy_document = self._create_device_policy(validated_device_id)
            
            try:
                self.iot_client.create_policy(
                    policyName=policy_name,
                    policyDocument=json.dumps(policy_document)
                )
                print(f"✅ Policy created: {policy_name}")
            except self.iot_client.exceptions.ResourceAlreadyExistsException:
                print(f"ℹ️  Policy already exists: {policy_name}")
            
            # Step 4: Attach policy to certificate
            print("4️⃣  Attaching policy to certificate...")
            self.iot_client.attach_policy(
                policyName=policy_name,
                target=certificate_arn
            )
            print("✅ Policy attached")
            
            # Step 5: Attach certificate to thing
            print("5️⃣  Attaching certificate to thing...")
            self.iot_client.attach_thing_principal(
                thingName=validated_device_id,
                principal=certificate_arn
            )
            print("✅ Certificate attached to thing")
            
            # Step 6: Get IoT endpoint
            print("6️⃣  Getting IoT endpoint...")
            endpoint_response = self.iot_client.describe_endpoint(endpointType='iot:Data-ATS')
            iot_endpoint = endpoint_response['endpointAddress']
            print(f"✅ IoT Endpoint: {iot_endpoint}")
            
            # Step 7: ✅ CRITICAL - Record device-user mapping in DynamoDB
            print("7️⃣  Recording device ownership in DynamoDB...")
            device_record = {
                'device_id': validated_device_id,
                'user_id': validated_user_id,  # ✅ Source of truth for ownership
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active',
                'certificate_id': certificate_id,
                'certificate_arn': certificate_arn,
                'iot_endpoint': iot_endpoint,
                'firmware_version': '1.0.0',
                'last_seen': None,
                'metadata': device_metadata or {}
            }
            
            self.devices_table.put_item(Item=device_record)
            print("✅ Device ownership recorded")
            
            # Step 8: Update user's device list
            print("8️⃣  Updating user's device list...")
            self.users_table.update_item(
                Key={'userId': validated_user_id},
                UpdateExpression='SET deviceIds = list_append(if_not_exists(deviceIds, :empty_list), :device)',
                ExpressionAttributeValues={
                    ':device': [validated_device_id],
                    ':empty_list': []
                }
            )
            print("✅ User device list updated")
            
            # Step 9: Save certificates and generate config
            print("9️⃣  Saving certificates and configuration...")
            self._save_certificates(validated_device_id, certificate_pem, public_key, private_key)
            self._generate_arduino_config(validated_device_id, validated_user_id, certificate_pem, 
                                         private_key, iot_endpoint)
            self._generate_device_info(device_record)
            
            print("\n" + "=" * 60)
            print("🎉 MULTI-USER DEVICE PROVISIONING COMPLETE!")
            print("=" * 60)
            print(f"📱 Device ID: {validated_device_id}")
            print(f"👤 Owner: {validated_user_id} ({user.get('email', 'N/A')})")
            print(f"🔑 Certificate ID: {certificate_id}")
            print(f"🌐 IoT Endpoint: {iot_endpoint}")
            print(f"\n📁 Files created:")
            print(f"   • certificates/{validated_device_id}-certificate.pem")
            print(f"   • certificates/{validated_device_id}-private-key.pem")
            print(f"   • esp32-firmware/{validated_device_id}_config.h")
            print(f"   • certificates/{validated_device_id}-info.json")
            
            return {
                'device_id': validated_device_id,
                'user_id': validated_user_id,
                'certificate_id': certificate_id,
                'iot_endpoint': iot_endpoint
            }
            
        except Exception as e:
            print(f"❌ Error provisioning device: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_device_policy(self, device_id):
        """Create strict device-specific IoT policy"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "iot:Connect",
                    "Resource": f"arn:aws:iot:{self.region}:*:client/{device_id}",
                    "Condition": {
                        "StringEquals": {
                            "iot:Connection.Thing.ThingName": device_id
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": "iot:Publish",
                    "Resource": [
                        f"arn:aws:iot:{self.region}:*:topic/aquachain/{device_id}/data",
                        f"arn:aws:iot:{self.region}:*:topic/aquachain/{device_id}/telemetry",
                        f"arn:aws:iot:{self.region}:*:topic/aquachain/{device_id}/heartbeat"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": ["iot:Subscribe", "iot:Receive"],
                    "Resource": [
                        f"arn:aws:iot:{self.region}:*:topicfilter/aquachain/{device_id}/commands",
                        f"arn:aws:iot:{self.region}:*:topic/aquachain/{device_id}/commands"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": ["iot:GetThingShadow", "iot:UpdateThingShadow"],
                    "Resource": f"arn:aws:iot:{self.region}:*:thing/{device_id}"
                }
            ]
        }
    
    def _save_certificates(self, device_id, certificate_pem, public_key, private_key):
        """Save certificates to files"""
        cert_dir = Path('certificates')
        cert_dir.mkdir(exist_ok=True)
        
        with open(cert_dir / f'{device_id}-certificate.pem', 'w') as f:
            f.write(certificate_pem)
        
        with open(cert_dir / f'{device_id}-private-key.pem', 'w') as f:
            f.write(private_key)
        
        with open(cert_dir / f'{device_id}-public-key.pem', 'w') as f:
            f.write(public_key)
        
        print(f"✅ Certificates saved")
    
    def _generate_arduino_config(self, device_id, user_id, certificate_pem, private_key, iot_endpoint):
        """Generate Arduino configuration with user context"""
        firmware_dir = Path('esp32-firmware')
        firmware_dir.mkdir(exist_ok=True)
        
        config_content = f'''/*
 * AquaChain Multi-User Device Configuration
 * Device ID: {device_id}
 * Owner: {user_id}
 * Generated: {datetime.utcnow().isoformat()}
 */

#ifndef DEVICE_CONFIG_H
#define DEVICE_CONFIG_H

// Device Configuration
#define DEVICE_ID "{device_id}"
#define USER_ID "{user_id}"
#define AWS_IOT_ENDPOINT "{iot_endpoint}"
#define FIRMWARE_VERSION "1.0.0"

// WiFi Configuration (UPDATE THESE)
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// Sensor Configuration
#define PH_SENSOR_PIN A0
#define TDS_SENSOR_PIN A3
#define TURBIDITY_SENSOR_PIN A6
#define DHT_PIN 4
#define DHT_TYPE DHT22

// Timing
#define SENSOR_READING_INTERVAL 30000
#define HEARTBEAT_INTERVAL 300000

#endif
'''
        
        with open(firmware_dir / f'{device_id}_config.h', 'w') as f:
            f.write(config_content)
        
        print(f"✅ Arduino config generated")
    
    def _generate_device_info(self, device_record):
        """Generate device info JSON"""
        cert_dir = Path('certificates')
        info_file = cert_dir / f"{device_record['device_id']}-info.json"
        
        with open(info_file, 'w') as f:
            json.dump(device_record, f, indent=2, default=str)
        
        print(f"✅ Device info saved")
    
    def list_user_devices(self, user_id):
        """List all devices owned by a user"""
        print(f"📱 Devices for user: {user_id}")
        print("-" * 60)
        
        try:
            response = self.devices_table.query(
                IndexName='user_id-created_at-index',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
            
            devices = response.get('Items', [])
            
            if not devices:
                print("No devices found for this user")
                return []
            
            for device in devices:
                print(f"🔹 {device['device_id']}")
                print(f"   Status: {device.get('status', 'unknown')}")
                print(f"   Created: {device.get('created_at', 'N/A')}")
                print(f"   Last Seen: {device.get('last_seen', 'Never')}")
                print()
            
            return devices
            
        except Exception as e:
            print(f"❌ Error listing devices: {e}")
            return []
    
    def delete_device(self, device_id, user_id):
        """Delete device with ownership verification"""
        print(f"🗑️  Deleting device: {device_id}")
        
        try:
            # Verify ownership
            device = self.devices_table.get_item(Key={'device_id': device_id}).get('Item')
            
            if not device:
                print(f"❌ Device not found: {device_id}")
                return False
            
            if device['user_id'] != user_id:
                print(f"❌ Access denied: Device belongs to different user")
                return False
            
            # Get and detach principals
            principals = self.iot_client.list_thing_principals(thingName=device_id)
            
            for principal in principals.get('principals', []):
                # Detach policies
                policies = self.iot_client.list_attached_policies(target=principal)
                for policy in policies.get('policies', []):
                    self.iot_client.detach_policy(
                        policyName=policy['policyName'],
                        target=principal
                    )
                
                # Detach from thing
                self.iot_client.detach_thing_principal(
                    thingName=device_id,
                    principal=principal
                )
                
                # Delete certificate
                cert_id = principal.split('/')[-1]
                self.iot_client.update_certificate(
                    certificateId=cert_id,
                    newStatus='INACTIVE'
                )
                self.iot_client.delete_certificate(certificateId=cert_id)
            
            # Delete thing
            self.iot_client.delete_thing(thingName=device_id)
            
            # Delete from DynamoDB
            self.devices_table.delete_item(Key={'device_id': device_id})
            
            # Remove from user's device list
            self.users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='DELETE deviceIds :device',
                ExpressionAttributeValues={':device': {device_id}}
            )
            
            print(f"✅ Device deleted successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting device: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='AquaChain Multi-User Device Provisioning')
    parser.add_argument('action', choices=['provision', 'list', 'delete'],
                       help='Action to perform')
    parser.add_argument('--device-id', help='Device ID')
    parser.add_argument('--user-id', help='Cognito User ID (sub)')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--location', help='Device location (JSON)')
    
    args = parser.parse_args()
    
    provisioner = MultiUserDeviceProvisioner(region=args.region)
    
    if args.action == 'provision':
        if not args.device_id or not args.user_id:
            print("❌ Both --device-id and --user-id are required")
            sys.exit(1)
        
        metadata = {}
        if args.location:
            metadata['location'] = json.loads(args.location)
        
        result = provisioner.provision_device(args.device_id, args.user_id, metadata)
        sys.exit(0 if result else 1)
    
    elif args.action == 'list':
        if not args.user_id:
            print("❌ --user-id is required")
            sys.exit(1)
        
        provisioner.list_user_devices(args.user_id)
    
    elif args.action == 'delete':
        if not args.device_id or not args.user_id:
            print("❌ Both --device-id and --user-id are required")
            sys.exit(1)
        
        response = input(f"⚠️  Delete {args.device_id}? (yes/no): ")
        if response.lower() == 'yes':
            provisioner.delete_device(args.device_id, args.user_id)


if __name__ == "__main__":
    main()
