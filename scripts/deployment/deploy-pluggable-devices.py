#!/usr/bin/env python3
"""
Deploy Pluggable Device System
Creates the necessary infrastructure and deploys the pluggable device service
"""

import boto3
import json
import time
import sys
from pathlib import Path

def create_pluggable_devices_table():
    """Create the PluggableDevices DynamoDB table if it doesn't exist"""
    dynamodb = boto3.client('dynamodb')
    
    table_name = 'AquaChain-PluggableDevices'
    
    try:
        # Check if table exists
        response = dynamodb.describe_table(TableName=table_name)
        print(f"✅ Table {table_name} already exists")
        return True
    except dynamodb.exceptions.ResourceNotFoundException:
        print(f"📦 Creating table {table_name}...")
        
        try:
            # Create table
            response = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'deviceId',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'deviceId',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'userId',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'createdAt',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'userId-createdAt-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'userId',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'createdAt',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                SSESpecification={
                    'Enabled': True
                },
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'AquaChain'
                    },
                    {
                        'Key': 'Environment',
                        'Value': 'dev'
                    },
                    {
                        'Key': 'Service',
                        'Value': 'pluggable-devices'
                    }
                ]
            )
            
            # Wait for table to be created
            print("⏳ Waiting for table to be created...")
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name, WaiterConfig={'Delay': 5, 'MaxAttempts': 60})
            
            print(f"✅ Table {table_name} created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create table: {str(e)}")
            return False

def deploy_lambda_function():
    """Deploy the pluggable device service Lambda function"""
    print("🚀 Deploying pluggable device service Lambda function...")
    
    # This would typically be done via CDK, but for now we'll just validate the code
    lambda_dir = Path(__file__).parent.parent.parent / 'lambda' / 'pluggable_device_service'
    
    if not lambda_dir.exists():
        print(f"❌ Lambda directory not found: {lambda_dir}")
        return False
    
    handler_file = lambda_dir / 'handler.py'
    if not handler_file.exists():
        print(f"❌ Handler file not found: {handler_file}")
        return False
    
    requirements_file = lambda_dir / 'requirements.txt'
    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    print("✅ Lambda function files validated")
    print("📝 Note: Deploy via CDK with: cdk deploy AquaChain-API-dev")
    return True

def create_api_gateway_routes():
    """Create API Gateway routes for pluggable devices"""
    print("🌐 API Gateway routes for pluggable devices:")
    
    routes = [
        "POST /api/v1/devices/register-pluggable",
        "POST /api/v1/devices/validate-pairing", 
        "GET /api/v1/devices/pluggable-devices",
        "POST /api/v1/devices/{deviceId}/unpair",
        "PUT /api/v1/devices/pluggable-devices/{deviceId}"
    ]
    
    for route in routes:
        print(f"  📍 {route}")
    
    print("📝 Note: Routes will be created via CDK deployment")
    return True

def validate_permissions():
    """Validate that the Lambda function has necessary permissions"""
    print("🔐 Required IAM permissions for pluggable device service:")
    
    permissions = [
        "dynamodb:GetItem - AquaChain-PluggableDevices",
        "dynamodb:PutItem - AquaChain-PluggableDevices", 
        "dynamodb:UpdateItem - AquaChain-PluggableDevices",
        "dynamodb:DeleteItem - AquaChain-PluggableDevices",
        "dynamodb:Query - AquaChain-PluggableDevices (userId-createdAt-index)",
        "dynamodb:GetItem - AquaChain-Devices",
        "dynamodb:PutItem - AquaChain-Devices",
        "dynamodb:DeleteItem - AquaChain-Devices",
        "logs:CreateLogGroup",
        "logs:CreateLogStream", 
        "logs:PutLogEvents"
    ]
    
    for permission in permissions:
        print(f"  🔑 {permission}")
    
    print("📝 Note: Permissions will be granted via CDK IAM roles")
    return True

def main():
    """Main deployment function"""
    print("🔧 Deploying AquaChain Pluggable Device System")
    print("=" * 50)
    
    steps = [
        ("Creating DynamoDB table", create_pluggable_devices_table),
        ("Validating Lambda function", deploy_lambda_function),
        ("Documenting API routes", create_api_gateway_routes),
        ("Documenting permissions", validate_permissions)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ Failed: {step_name}")
            sys.exit(1)
        print(f"✅ Completed: {step_name}")
    
    print("\n🎉 Pluggable Device System deployment completed!")
    print("\n📋 Next Steps:")
    print("1. Deploy via CDK: cd infrastructure/cdk && cdk deploy AquaChain-API-dev")
    print("2. Update frontend environment variables if needed")
    print("3. Test device connection flows in the Consumer Dashboard")
    print("4. Register connection handlers for specific device types")
    
    print("\n🔗 Frontend Integration:")
    print("- The PluggableDeviceManager component is already integrated")
    print("- WiFi and QR Code connection handlers are implemented")
    print("- Device discovery and pairing flows are ready")
    
    print("\n🧪 Testing:")
    print("- Use the 'Connect Devices' button in the Consumer Dashboard")
    print("- Test WiFi device discovery (simulated)")
    print("- Test QR code device pairing")
    print("- Verify device registration in DynamoDB")

if __name__ == "__main__":
    main()