#!/usr/bin/env python3
"""
Setup AWS IoT Code Signing
Creates signing profile and configures firmware signing workflow
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError

signer = boto3.client('signer')
s3 = boto3.client('s3')
iot = boto3.client('iot')


def create_signing_profile(profile_name='aquachain-firmware-signing'):
    """Create code signing profile for firmware"""
    try:
        # Check if profile already exists
        try:
            response = signer.get_signing_profile(profileName=profile_name)
            print(f"✓ Signing profile '{profile_name}' already exists")
            return response['profileName']
        except signer.exceptions.ResourceNotFoundException:
            pass
        
        # Create new signing profile
        response = signer.put_signing_profile(
            profileName=profile_name,
            platformId='AWSIoTDeviceManagement-SHA256-ECDSA',
            signatureValidityPeriod={
                'value': 5,
                'type': 'YEARS'
            },
            tags={
                'Project': 'AquaChain',
                'Purpose': 'FirmwareSigning'
            }
        )
        
        print(f"✓ Created signing profile: {response['profileName']}")
        print(f"  Profile ARN: {response['arn']}")
        return response['profileName']
        
    except ClientError as e:
        print(f"✗ Error creating signing profile: {e}")
        return None


def verify_firmware_bucket(bucket_name):
    """Verify firmware bucket exists and is configured correctly"""
    try:
        # Check if bucket exists
        s3.head_bucket(Bucket=bucket_name)
        print(f"✓ Firmware bucket '{bucket_name}' exists")
        
        # Check versioning
        versioning = s3.get_bucket_versioning(Bucket=bucket_name)
        if versioning.get('Status') == 'Enabled':
            print(f"✓ Bucket versioning is enabled")
        else:
            print(f"⚠ Warning: Bucket versioning is not enabled")
        
        # Check encryption
        try:
            encryption = s3.get_bucket_encryption(Bucket=bucket_name)
            print(f"✓ Bucket encryption is configured")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                print(f"⚠ Warning: Bucket encryption is not configured")
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"✗ Firmware bucket '{bucket_name}' does not exist")
            print(f"  Create it with: aws s3 mb s3://{bucket_name}")
        else:
            print(f"✗ Error checking bucket: {e}")
        return False


def create_signing_job_example(profile_name, bucket_name):
    """Create example signing job configuration"""
    example_config = {
        "source": {
            "s3": {
                "bucketName": bucket_name,
                "key": "unsigned/firmware-v1.0.0.bin",
                "version": "null"
            }
        },
        "destination": {
            "s3": {
                "bucketName": bucket_name,
                "prefix": "signed/v1.0.0/"
            }
        },
        "profileName": profile_name
    }
    
    print("\n" + "="*60)
    print("Example Signing Job Configuration:")
    print("="*60)
    print(json.dumps(example_config, indent=2))
    print("\nTo sign firmware, use:")
    print(f"  aws signer start-signing-job --cli-input-json file://signing-job.json")
    
    # Save example config
    with open('signing-job-example.json', 'w') as f:
        json.dump(example_config, f, indent=2)
    
    print(f"\n✓ Saved example configuration to: signing-job-example.json")


def test_signing_workflow(profile_name, bucket_name):
    """Test the signing workflow with a dummy file"""
    print("\n" + "="*60)
    print("Testing Signing Workflow")
    print("="*60)
    
    # Create a test firmware file
    test_content = b"TEST_FIRMWARE_CONTENT_v1.0.0"
    test_key = "unsigned/test-firmware.bin"
    
    try:
        # Upload test file
        s3.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content
        )
        print(f"✓ Uploaded test firmware to s3://{bucket_name}/{test_key}")
        
        # Start signing job
        response = signer.start_signing_job(
            source={
                's3': {
                    'bucketName': bucket_name,
                    'key': test_key,
                    'version': 'null'
                }
            },
            destination={
                's3': {
                    'bucketName': bucket_name,
                    'prefix': 'signed/test/'
                }
            },
            profileName=profile_name
        )
        
        job_id = response['jobId']
        print(f"✓ Started signing job: {job_id}")
        print(f"  Check status with: aws signer describe-signing-job --job-id {job_id}")
        
        return True
        
    except ClientError as e:
        print(f"✗ Error testing signing workflow: {e}")
        return False


def print_setup_summary(profile_name, bucket_name):
    """Print setup summary and next steps"""
    print("\n" + "="*60)
    print("Setup Summary")
    print("="*60)
    print(f"Signing Profile: {profile_name}")
    print(f"Firmware Bucket: {bucket_name}")
    print("\nNext Steps:")
    print("1. Upload unsigned firmware to: s3://{}/unsigned/".format(bucket_name))
    print("2. Sign firmware using the OTA Lambda function or AWS CLI")
    print("3. Signed firmware will be stored in: s3://{}/signed/".format(bucket_name))
    print("\nEnvironment Variables for Lambda:")
    print(f"  FIRMWARE_BUCKET={bucket_name}")
    print(f"  SIGNING_PROFILE_NAME={profile_name}")


def main():
    """Main setup function"""
    print("="*60)
    print("AWS IoT Code Signing Setup")
    print("="*60)
    
    # Configuration
    profile_name = 'aquachain-firmware-signing'
    
    # Get account ID for bucket name
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    bucket_name = f'aquachain-firmware-{account_id}'
    
    print(f"\nAccount ID: {account_id}")
    print(f"Region: {boto3.session.Session().region_name}")
    print()
    
    # Step 1: Create signing profile
    print("Step 1: Creating signing profile...")
    profile = create_signing_profile(profile_name)
    if not profile:
        print("\n✗ Failed to create signing profile")
        sys.exit(1)
    
    # Step 2: Verify firmware bucket
    print("\nStep 2: Verifying firmware bucket...")
    if not verify_firmware_bucket(bucket_name):
        print("\n⚠ Firmware bucket not found or not configured correctly")
        print("  Deploy the IoT Code Signing CDK stack to create the bucket")
    
    # Step 3: Create example configuration
    print("\nStep 3: Creating example configuration...")
    create_signing_job_example(profile_name, bucket_name)
    
    # Step 4: Test signing workflow (optional)
    print("\nStep 4: Testing signing workflow...")
    response = input("Run signing workflow test? (y/n): ")
    if response.lower() == 'y':
        test_signing_workflow(profile_name, bucket_name)
    else:
        print("Skipping test")
    
    # Print summary
    print_setup_summary(profile_name, bucket_name)
    
    print("\n✓ Code signing setup complete!")


if __name__ == '__main__':
    main()
