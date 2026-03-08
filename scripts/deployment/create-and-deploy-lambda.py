#!/usr/bin/env python3
"""
Create and deploy the data processing Lambda function
This creates the Lambda function if it doesn't exist, or updates it if it does
"""

import boto3
import zipfile
import os
import json
import time
from pathlib import Path

def create_iam_role():
    """Create IAM role for Lambda function"""
    print("Step 1: Creating/checking IAM role...")
    
    iam_client = boto3.client('iam')
    role_name = 'AquaChain-DataProcessing-Lambda-Role'
    
    # Trust policy for Lambda
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        # Try to get existing role
        response = iam_client.get_role(RoleName=role_name)
        role_arn = response['Role']['Arn']
        print(f"✓ Using existing IAM role: {role_arn}")
        return role_arn
        
    except iam_client.exceptions.NoSuchEntityException:
        # Create new role
        print(f"  Creating new IAM role: {role_name}")
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='IAM role for AquaChain data processing Lambda function'
        )
        role_arn = response['Role']['Arn']
        
        # Attach basic Lambda execution policy
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        # Attach DynamoDB access policy
        dynamodb_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:Query",
                        "dynamodb:UpdateItem"
                    ],
                    "Resource": "arn:aws:dynamodb:us-east-1:*:table/AquaChain-*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:InvokeFunction"
                    ],
                    "Resource": "arn:aws:lambda:us-east-1:*:function:aquachain-*"
                }
            ]
        }
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='DynamoDBAndLambdaAccess',
            PolicyDocument=json.dumps(dynamodb_policy)
        )
        
        print(f"✓ Created IAM role: {role_arn}")
        print("  Waiting for IAM role to propagate...")
        time.sleep(10)  # Wait for IAM role to be available
        
        return role_arn

def create_deployment_package():
    """Create Lambda deployment package"""
    print("\nStep 2: Creating deployment package...")
    
    lambda_dir = Path("lambda/data_processing")
    zip_path = lambda_dir / "package.zip"
    
    # Remove old package if exists
    if zip_path.exists():
        zip_path.unlink()
    
    # Create zip file with handler.py
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        handler_path = lambda_dir / "handler.py"
        zipf.write(handler_path, "handler.py")
    
    print(f"✓ Created deployment package: {zip_path}")
    return zip_path

def create_or_update_lambda(role_arn, zip_path):
    """Create or update Lambda function"""
    print("\nStep 3: Creating/updating Lambda function...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    function_name = 'aquachain-function-data-processing-dev'
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        # Try to get existing function
        lambda_client.get_function(FunctionName=function_name)
        
        # Function exists, update it
        print(f"  Updating existing function: {function_name}")
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✓ Lambda function updated successfully")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Function doesn't exist, create it
        print(f"  Creating new function: {function_name}")
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='AquaChain IoT data processing Lambda function',
            Timeout=30,
            MemorySize=512,
            Environment={
                'Variables': {
                    'READINGS_TABLE': 'AquaChain-Readings',
                    'LEDGER_TABLE': 'aquachain-ledger',
                    'SEQUENCE_TABLE': 'AquaChain-Sequence',
                    'ML_INFERENCE_FUNCTION': 'aquachain-function-ml-inference-dev'
                }
            }
        )
        
        print(f"✓ Lambda function created successfully")
    
    print(f"  Function ARN: {response['FunctionArn']}")
    print(f"  Last Modified: {response['LastModified']}")
    print(f"  Code Size: {response['CodeSize']} bytes")
    
    return True

def test_lambda():
    """Test Lambda function with sample ESP32 data"""
    print("\nStep 4: Testing Lambda function...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    function_name = 'aquachain-function-data-processing-dev'
    
    # Sample ESP32 data
    test_payload = {
        "deviceId": "ESP32-001",
        "timestamp": "2026-03-08T14:00:00Z",
        "location": {
            "latitude": 0,
            "longitude": 0
        },
        "readings": {
            "pH": 7.0,
            "turbidity": 300,
            "tds": 45,
            "temperature": 30
        },
        "diagnostics": {
            "batteryLevel": 100,
            "signalStrength": -70,
            "sensorStatus": "normal"
        }
    }
    
    try:
        # Wait for Lambda to be ready
        print("  Waiting for Lambda to be ready...")
        time.sleep(5)
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"\n✓ Lambda test invocation completed!")
        print(f"  Status Code: {response['StatusCode']}")
        print(f"  Response:")
        print(f"    {json.dumps(response_payload, indent=4)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Lambda test failed: {str(e)}")
        return False

def cleanup(zip_path):
    """Clean up deployment artifacts"""
    if zip_path.exists():
        zip_path.unlink()
        print(f"\n✓ Cleaned up deployment package")

def main():
    """Main deployment function"""
    print("=" * 60)
    print("Creating/Updating Data Processing Lambda Function")
    print("=" * 60)
    print()
    
    try:
        # Create IAM role
        role_arn = create_iam_role()
        
        # Create deployment package
        zip_path = create_deployment_package()
        
        # Create or update Lambda function
        if not create_or_update_lambda(role_arn, zip_path):
            cleanup(zip_path)
            return 1
        
        # Test the deployment
        test_lambda()
        
        # Cleanup
        cleanup(zip_path)
        
        print()
        print("=" * 60)
        print("Deployment Complete!")
        print("=" * 60)
        print()
        print("The Lambda function has been created/updated with simplified validation.")
        print("Your ESP32 device should now be able to send data successfully.")
        print()
        print("Next steps:")
        print("1. Configure IoT Rule to trigger this Lambda function")
        print("2. Check CloudWatch Logs for validation success messages")
        print("3. Query DynamoDB to verify new readings are being stored")
        print("4. Monitor your ESP32 device for successful data transmission")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Deployment failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
