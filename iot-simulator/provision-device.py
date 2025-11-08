#!/usr/bin/env python3
"""
ESP32 Device Provisioning Script for AquaChain
Automates the creation of AWS IoT Things, certificates, and policies
"""

import boto3
import json
import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

# Import secure validation module
from device_validation import DeviceValidator, DeviceValidationError

def create_iot_policy():
    """Create the AquaChain device policy if it doesn't exist"""
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iot:Connect"
                ],
                "Resource": "arn:aws:iot:*:*:client/AquaChain-Device-*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iot:Publish"
                ],
                "Resource": [
                    "arn:aws:iot:*:*:topic/aquachain/+/data",
                    "arn:aws:iot:*:*:topic/aquachain/+/status",
                    "arn:aws:iot:*:*:topic/aquachain/+/diagnostics",
                    "arn:aws:iot:*:*:topic/aquachain/+/heartbeat"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iot:Subscribe",
                    "iot:Receive"
                ],
                "Resource": [
                    "arn:aws:iot:*:*:topicfilter/aquachain/+/commands",
                    "arn:aws:iot:*:*:topicfilter/aquachain/+/config"
                ]
            }
        ]
    }
    
    return policy_document

def provision_device(device_id, region='us-east-1', thing_type='AquaChainWaterSensor'):
    """Provision a new ESP32 device in AWS IoT Core"""
    
    print(f"🚀 Provisioning device: {device_id}")
    print(f"📍 Region: {region}")
    print(f"🏷️  Thing Type: {thing_type}")
    print("-" * 50)
    
    try:
        # SECURITY: Validate device ID before provisioning
        print("🔒 Validating device credentials...")
        try:
            validated_device_id = DeviceValidator.validate_device_id(device_id)
            validated_thing_type = DeviceValidator.validate_thing_name(thing_type)
            print(f"✅ Device ID validated: {validated_device_id}")
        except DeviceValidationError as e:
            print(f"❌ Validation failed: {e}")
            return False
        
        iot_client = boto3.client('iot', region_name=region)
        
        # Step 1: Create Thing Type (if it doesn't exist)
        try:
            print("1️⃣  Creating/checking Thing Type...")
            iot_client.create_thing_type(
                thingTypeName=thing_type,
                thingTypeDescription="AquaChain water quality monitoring device"
            )
            print(f"✅ Thing Type '{thing_type}' created")
        except iot_client.exceptions.ResourceAlreadyExistsException:
            print(f"ℹ️  Thing Type '{thing_type}' already exists")
        
        # Step 2: Create IoT Thing
        try:
            print(f"2️⃣  Creating IoT Thing: {device_id}")
            iot_client.create_thing(
                thingName=device_id,
                thingTypeName=thing_type,
                attributePayload={
                    'attributes': {
                        'deviceType': 'ESP32',
                        'firmwareVersion': '1.0.0',
                        'location': 'field',
                        'createdDate': datetime.now().isoformat()
                    }
                }
            )
            print(f"✅ IoT Thing '{device_id}' created")
        except iot_client.exceptions.ResourceAlreadyExistsException:
            print(f"ℹ️  IoT Thing '{device_id}' already exists")
        
        # Step 3: Create device policy (if it doesn't exist)
        policy_name = 'AquaChainDevicePolicy'
        try:
            print("3️⃣  Creating/checking device policy...")
            policy_document = create_iot_policy()
            iot_client.create_policy(
                policyName=policy_name,
                policyDocument=json.dumps(policy_document)
            )
            print(f"✅ Policy '{policy_name}' created")
        except iot_client.exceptions.ResourceAlreadyExistsException:
            print(f"ℹ️  Policy '{policy_name}' already exists")
        
        # Step 4: Create certificate and keys
        print("4️⃣  Creating device certificate...")
        cert_response = iot_client.create_keys_and_certificate(setAsActive=True)
        
        certificate_arn = cert_response['certificateArn']
        certificate_id = cert_response['certificateId']
        certificate_pem = cert_response['certificatePem']
        public_key = cert_response['keyPair']['PublicKey']
        private_key = cert_response['keyPair']['PrivateKey']
        
        print(f"✅ Certificate created: {certificate_id}")
        
        # Step 5: Attach policy to certificate
        print("5️⃣  Attaching policy to certificate...")
        iot_client.attach_policy(
            policyName=policy_name,
            target=certificate_arn
        )
        print("✅ Policy attached to certificate")
        
        # Step 6: Attach certificate to thing
        print("6️⃣  Attaching certificate to thing...")
        iot_client.attach_thing_principal(
            thingName=device_id,
            principal=certificate_arn
        )
        print("✅ Certificate attached to thing")
        
        # Step 7: Get IoT endpoint
        print("7️⃣  Getting IoT endpoint...")
        endpoint_response = iot_client.describe_endpoint(endpointType='iot:Data-ATS')
        iot_endpoint = endpoint_response['endpointAddress']
        print(f"✅ IoT Endpoint: {iot_endpoint}")
        
        # Step 8: Save certificates and generate config
        print("8️⃣  Saving certificates and generating configuration...")
        save_certificates(device_id, certificate_pem, public_key, private_key, certificate_id)
        generate_arduino_config(device_id, certificate_pem, private_key, iot_endpoint)
        generate_device_info(device_id, certificate_arn, certificate_id, iot_endpoint, region)
        
        print("\n" + "=" * 60)
        print("🎉 DEVICE PROVISIONING COMPLETE!")
        print("=" * 60)
        print(f"📱 Device ID: {device_id}")
        print(f"🔑 Certificate ID: {certificate_id}")
        print(f"🌐 IoT Endpoint: {iot_endpoint}")
        print(f"📁 Files created:")
        print(f"   • certificates/{device_id}-certificate.pem")
        print(f"   • certificates/{device_id}-private-key.pem")
        print(f"   • certificates/{device_id}-public-key.pem")
        print(f"   • esp32-firmware/{device_id}_config.h")
        print(f"   • certificates/{device_id}-info.json")
        print("\n📋 Next Steps:")
        print("1. Copy the generated config file to your Arduino project")
        print("2. Update WiFi credentials in the config file")
        print("3. Flash the firmware to your ESP32 device")
        print("4. Monitor serial output for connection status")
        
        return True
        
    except Exception as e:
        print(f"❌ Error provisioning device: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_certificates(device_id, certificate_pem, public_key, private_key, certificate_id):
    """Save certificates to files"""
    
    cert_dir = Path('certificates')
    cert_dir.mkdir(exist_ok=True)
    
    # Save certificate
    with open(cert_dir / f'{device_id}-certificate.pem', 'w') as f:
        f.write(certificate_pem)
    
    # Save private key
    with open(cert_dir / f'{device_id}-private-key.pem', 'w') as f:
        f.write(private_key)
    
    # Save public key
    with open(cert_dir / f'{device_id}-public-key.pem', 'w') as f:
        f.write(public_key)
    
    print(f"✅ Certificates saved to certificates/ directory")

def generate_arduino_config(device_id, certificate_pem, private_key, iot_endpoint):
    """Generate Arduino configuration header file"""
    
    firmware_dir = Path('esp32-firmware')
    firmware_dir.mkdir(exist_ok=True)
    
    config_content = f'''/*
 * AquaChain Device Configuration
 * Generated automatically by provision-device.py
 * Device ID: {device_id}
 * Generated: {datetime.now().isoformat()}
 */

#ifndef DEVICE_CONFIG_H
#define DEVICE_CONFIG_H

// Device Configuration
#define DEVICE_ID "{device_id}"
#define AWS_IOT_ENDPOINT "{iot_endpoint}"
#define FIRMWARE_VERSION "1.0.0"

// WiFi Configuration (UPDATE THESE VALUES)
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// Device Location (UPDATE WITH ACTUAL COORDINATES)
#define DEVICE_LATITUDE 37.7749
#define DEVICE_LONGITUDE -122.4194

// Sensor Configuration
#define PH_SENSOR_PIN A0
#define TDS_SENSOR_PIN A3
#define TURBIDITY_SENSOR_PIN A6
#define DHT_PIN 4
#define DHT_TYPE DHT22

// I2C Configuration
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22

// Timing Configuration
#define SENSOR_READING_INTERVAL 30000   // 30 seconds
#define HEARTBEAT_INTERVAL 300000       // 5 minutes

// Power Management
#define ENABLE_POWER_SAVING false
#define WDT_TIMEOUT 30

#endif // DEVICE_CONFIG_H

/*
 * IMPORTANT: Update the certificates in certificates.h with the values below:
 */

/*
Device Certificate (paste into certificates.h):
{certificate_pem}
*/

/*
Device Private Key (paste into certificates.h):
{private_key}
*/
'''
    
    config_file = firmware_dir / f'{device_id}_config.h'
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Arduino config generated: {config_file}")

def generate_device_info(device_id, certificate_arn, certificate_id, iot_endpoint, region):
    """Generate device information JSON file"""
    
    cert_dir = Path('certificates')
    
    device_info = {
        "deviceId": device_id,
        "certificateArn": certificate_arn,
        "certificateId": certificate_id,
        "iotEndpoint": iot_endpoint,
        "region": region,
        "createdAt": datetime.now().isoformat(),
        "status": "provisioned",
        "thingType": "AquaChainWaterSensor",
        "policyName": "AquaChainDevicePolicy"
    }
    
    info_file = cert_dir / f'{device_id}-info.json'
    with open(info_file, 'w') as f:
        json.dump(device_info, f, indent=2)
    
    print(f"✅ Device info saved: {info_file}")

def list_devices(region='us-east-1'):
    """List all provisioned AquaChain devices"""
    
    try:
        iot_client = boto3.client('iot', region_name=region)
        
        print("📱 AquaChain Devices:")
        print("-" * 50)
        
        # List things with AquaChain prefix
        response = iot_client.list_things(
            thingTypeName='AquaChainWaterSensor',
            maxResults=50
        )
        
        if not response['things']:
            print("No AquaChain devices found")
            return
        
        for thing in response['things']:
            thing_name = thing['thingName']
            attributes = thing.get('attributes', {})
            
            print(f"🔹 {thing_name}")
            print(f"   Created: {attributes.get('createdDate', 'Unknown')}")
            print(f"   Firmware: {attributes.get('firmwareVersion', 'Unknown')}")
            print(f"   Location: {attributes.get('location', 'Unknown')}")
            print()
            
    except Exception as e:
        print(f"❌ Error listing devices: {e}")

def delete_device(device_id, region='us-east-1'):
    """Delete a device and clean up all resources"""
    
    print(f"🗑️  Deleting device: {device_id}")
    
    try:
        iot_client = boto3.client('iot', region_name=region)
        
        # Get thing principals (certificates)
        try:
            principals_response = iot_client.list_thing_principals(thingName=device_id)
            principals = principals_response.get('principals', [])
            
            for principal in principals:
                certificate_id = principal.split('/')[-1]
                
                # Detach policies from certificate
                try:
                    policies_response = iot_client.list_attached_policies(target=principal)
                    for policy in policies_response.get('policies', []):
                        iot_client.detach_policy(
                            policyName=policy['policyName'],
                            target=principal
                        )
                        print(f"✅ Detached policy: {policy['policyName']}")
                except Exception as e:
                    print(f"⚠️  Error detaching policies: {e}")
                
                # Detach certificate from thing
                try:
                    iot_client.detach_thing_principal(
                        thingName=device_id,
                        principal=principal
                    )
                    print(f"✅ Detached certificate from thing")
                except Exception as e:
                    print(f"⚠️  Error detaching certificate: {e}")
                
                # Deactivate and delete certificate
                try:
                    iot_client.update_certificate(
                        certificateId=certificate_id,
                        newStatus='INACTIVE'
                    )
                    iot_client.delete_certificate(certificateId=certificate_id)
                    print(f"✅ Deleted certificate: {certificate_id}")
                except Exception as e:
                    print(f"⚠️  Error deleting certificate: {e}")
        
        except Exception as e:
            print(f"⚠️  Error getting thing principals: {e}")
        
        # Delete the thing
        try:
            iot_client.delete_thing(thingName=device_id)
            print(f"✅ Deleted thing: {device_id}")
        except Exception as e:
            print(f"⚠️  Error deleting thing: {e}")
        
        print(f"🎉 Device {device_id} deleted successfully")
        
    except Exception as e:
        print(f"❌ Error deleting device: {e}")

def main():
    parser = argparse.ArgumentParser(description='AquaChain ESP32 Device Provisioning')
    parser.add_argument('action', choices=['provision', 'list', 'delete'], 
                       help='Action to perform')
    parser.add_argument('device_id', nargs='?', 
                       help='Device ID (required for provision and delete)')
    parser.add_argument('--region', default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    
    args = parser.parse_args()
    
    if args.action == 'provision':
        if not args.device_id:
            print("❌ Device ID is required for provisioning")
            print("Usage: python provision-device.py provision AquaChain-Device-001")
            sys.exit(1)
        
        success = provision_device(args.device_id, args.region)
        sys.exit(0 if success else 1)
    
    elif args.action == 'list':
        list_devices(args.region)
    
    elif args.action == 'delete':
        if not args.device_id:
            print("❌ Device ID is required for deletion")
            print("Usage: python provision-device.py delete AquaChain-Device-001")
            sys.exit(1)
        
        # Confirm deletion
        response = input(f"⚠️  Are you sure you want to delete {args.device_id}? (yes/no): ")
        if response.lower() == 'yes':
            delete_device(args.device_id, args.region)
        else:
            print("❌ Deletion cancelled")

if __name__ == "__main__":
    main()