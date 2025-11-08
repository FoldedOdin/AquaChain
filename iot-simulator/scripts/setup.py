#!/usr/bin/env python3
"""
Setup script for AquaChain IoT Simulator
Configures AWS credentials, creates device certificates, and validates setup
"""

import boto3
import json
import os
import sys
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError
import argparse

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials configured for account: {identity['Account']}")
        return True
    except NoCredentialsError:
        print("❌ AWS credentials not configured")
        print("Please run: aws configure")
        return False
    except Exception as e:
        print(f"❌ Error checking AWS credentials: {e}")
        return False

def check_iot_endpoint(region):
    """Get and validate IoT endpoint"""
    try:
        iot = boto3.client('iot', region_name=region)
        response = iot.describe_endpoint(endpointType='iot:Data-ATS')
        endpoint = response['endpointAddress']
        print(f"✅ IoT endpoint found: {endpoint}")
        return endpoint
    except Exception as e:
        print(f"❌ Error getting IoT endpoint: {e}")
        return None

def create_device_certificates(device_ids, region):
    """Create device certificates for simulation"""
    try:
        iot = boto3.client('iot', region_name=region)
        certificates_dir = Path("certificates")
        certificates_dir.mkdir(exist_ok=True)
        
        created_certs = []
        
        for device_id in device_ids:
            try:
                # Create certificate
                response = iot.create_keys_and_certificate(setAsActive=True)
                
                cert_arn = response['certificateArn']
                cert_id = response['certificateId']
                
                # Save certificate files
                cert_file = certificates_dir / f"{device_id}-certificate.pem.crt"
                private_key_file = certificates_dir / f"{device_id}-private.pem.key"
                
                with open(cert_file, 'w') as f:
                    f.write(response['certificatePem'])
                
                with open(private_key_file, 'w') as f:
                    f.write(response['keyPair']['PrivateKey'])
                
                # Create IoT policy for device
                policy_name = f"AquaChainDevice-{device_id}"
                policy_document = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "iot:Connect",
                            "Resource": f"arn:aws:iot:{region}:*:client/{device_id}"
                        },
                        {
                            "Effect": "Allow",
                            "Action": "iot:Publish",
                            "Resource": f"arn:aws:iot:{region}:*:topic/aquachain/{device_id}/data"
                        },
                        {
                            "Effect": "Allow",
                            "Action": "iot:Subscribe",
                            "Resource": f"arn:aws:iot:{region}:*:topicfilter/aquachain/{device_id}/commands/*"
                        },
                        {
                            "Effect": "Allow",
                            "Action": "iot:Receive",
                            "Resource": f"arn:aws:iot:{region}:*:topic/aquachain/{device_id}/commands/*"
                        }
                    ]
                }
                
                try:
                    iot.create_policy(
                        policyName=policy_name,
                        policyDocument=json.dumps(policy_document)
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                        raise
                
                # Attach policy to certificate
                iot.attach_policy(
                    policyName=policy_name,
                    target=cert_arn
                )
                
                created_certs.append({
                    'deviceId': device_id,
                    'certificateId': cert_id,
                    'certificateArn': cert_arn
                })
                
                print(f"✅ Created certificate for device: {device_id}")
                
            except Exception as e:
                print(f"❌ Failed to create certificate for {device_id}: {e}")
        
        # Download Amazon Root CA certificate
        import urllib.request
        ca_url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
        ca_file = certificates_dir / "AmazonRootCA1.pem"
        
        if not ca_file.exists():
            urllib.request.urlretrieve(ca_url, ca_file)
            print("✅ Downloaded Amazon Root CA certificate")
        
        return created_certs
        
    except Exception as e:
        print(f"❌ Error creating device certificates: {e}")
        return []

def update_config_files(iot_endpoint, region):
    """Update configuration files with AWS settings"""
    try:
        # Update aws_config.json
        config_file = Path("config/aws_config.json")
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        config['aws']['iot_endpoint'] = iot_endpoint
        config['aws']['region'] = region
        config['aws']['use_simulator_auth'] = False  # Use real certificates
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Updated AWS configuration")
        return True
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

def validate_setup():
    """Validate that setup is complete"""
    checks = []
    
    # Check configuration files
    config_files = [
        "config/devices.json",
        "config/aws_config.json"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            checks.append(f"✅ {config_file} exists")
        else:
            checks.append(f"❌ {config_file} missing")
    
    # Check certificates directory
    cert_dir = Path("certificates")
    if cert_dir.exists() and list(cert_dir.glob("*.pem.*")):
        checks.append("✅ Device certificates found")
    else:
        checks.append("❌ Device certificates missing")
    
    # Check dependencies
    try:
        import boto3, paho.mqtt, pydantic, rich
        checks.append("✅ Python dependencies installed")
    except ImportError as e:
        checks.append(f"❌ Missing dependency: {e}")
    
    print("\n📋 Setup Validation:")
    for check in checks:
        print(f"  {check}")
    
    return all("✅" in check for check in checks)

def main():
    parser = argparse.ArgumentParser(description="Setup AquaChain IoT Simulator")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--create-certs", action="store_true", help="Create device certificates")
    parser.add_argument("--validate-only", action="store_true", help="Only validate setup")
    
    args = parser.parse_args()
    
    print("🔧 AquaChain IoT Simulator Setup")
    print("=" * 40)
    
    if args.validate_only:
        if validate_setup():
            print("\n✅ Setup validation passed!")
            sys.exit(0)
        else:
            print("\n❌ Setup validation failed!")
            sys.exit(1)
    
    # Check AWS credentials
    if not check_aws_credentials():
        sys.exit(1)
    
    # Get IoT endpoint
    iot_endpoint = check_iot_endpoint(args.region)
    if not iot_endpoint:
        sys.exit(1)
    
    # Create device certificates if requested
    if args.create_certs:
        # Load device configuration
        try:
            with open("config/devices.json", 'r') as f:
                device_config = json.load(f)
            
            device_ids = [d['deviceId'] for d in device_config['devices'] if d.get('enabled', True)]
            
            if device_ids:
                print(f"\n🔐 Creating certificates for {len(device_ids)} devices...")
                created_certs = create_device_certificates(device_ids, args.region)
                
                if created_certs:
                    print(f"\n✅ Created {len(created_certs)} device certificates")
                else:
                    print("\n❌ Failed to create device certificates")
                    sys.exit(1)
            else:
                print("⚠️  No enabled devices found in configuration")
        
        except Exception as e:
            print(f"❌ Error reading device configuration: {e}")
            sys.exit(1)
    
    # Update configuration files
    if update_config_files(iot_endpoint, args.region):
        print("✅ Configuration updated")
    else:
        sys.exit(1)
    
    # Final validation
    print("\n🔍 Validating setup...")
    if validate_setup():
        print("\n🎉 Setup complete! You can now run the simulator:")
        print("   python simulator.py")
    else:
        print("\n❌ Setup incomplete. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()