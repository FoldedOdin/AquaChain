#!/usr/bin/env python3
"""
Update Lambda Functions for SageMaker

This script updates the Lambda functions to use SageMaker endpoints
after the CDK stack has been deployed.
"""

import boto3
import json
from botocore.exceptions import ClientError

def update_lambda_environment():
    """Update Lambda environment variables"""
    print("🔄 Updating Lambda environment variables...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    function_name = 'aquachain-function-data-processing-dev'
    endpoint_name = 'aquachain-wqi-endpoint-dev'
    
    try:
        # Get current environment
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        print(f"Current environment variables: {list(env_vars.keys())}")
        
        # Update environment variables
        env_vars['SAGEMAKER_ENDPOINT_NAME'] = endpoint_name
        
        # Remove old ML function variable if exists
        if 'ML_INFERENCE_FUNCTION' in env_vars:
            print("Removing old ML_INFERENCE_FUNCTION variable")
            del env_vars['ML_INFERENCE_FUNCTION']
        
        # Update function
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': env_vars}
        )
        
        print(f"✅ Updated Lambda environment: {function_name}")
        print(f"✅ Set SAGEMAKER_ENDPOINT_NAME: {endpoint_name}")
        return True
        
    except ClientError as e:
        print(f"❌ Failed to update Lambda: {e}")
        return False

def update_lambda_permissions():
    """Update Lambda IAM permissions for SageMaker"""
    print("🔐 Updating Lambda IAM permissions...")
    
    iam_client = boto3.client('iam')
    role_name = 'aquachain-role-data-processing-dev'
    
    # SageMaker invoke policy
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "sagemaker:InvokeEndpoint"
                ],
                "Resource": [
                    "arn:aws:sagemaker:ap-south-1:758346259059:endpoint/aquachain-wqi-endpoint-dev"
                ]
            }
        ]
    }
    
    try:
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='SageMakerInvokeEndpointPolicy',
            PolicyDocument=json.dumps(policy_document)
        )
        print(f"✅ Updated IAM permissions for {role_name}")
        return True
    except ClientError as e:
        print(f"❌ Failed to update IAM permissions: {e}")
        print("   This might be expected if the role doesn't exist yet")
        return False

def test_sagemaker_endpoint():
    """Test SageMaker endpoint"""
    print("🧪 Testing SageMaker endpoint...")
    
    runtime = boto3.client('sagemaker-runtime', region_name='ap-south-1')
    endpoint_name = 'aquachain-wqi-endpoint-dev'
    
    test_payload = {
        'deviceId': 'ESP32-TEST',
        'timestamp': '2026-03-11T12:00:00Z',
        'readings': {
            'pH': 7.2,
            'turbidity': 3.5,
            'tds': 450,
            'temperature': 22.5,
            'humidity': 65.0
        },
        'location': {'latitude': 12.9716, 'longitude': 77.5946}
    }
    
    try:
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Accept='application/json',
            Body=json.dumps(test_payload)
        )
        
        result = json.loads(response['Body'].read().decode('utf-8'))
        
        print("✅ SageMaker endpoint test successful!")
        print(f"   WQI: {result.get('wqi', 'N/A')}")
        print(f"   Anomaly: {result.get('anomalyType', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        return True
        
    except ClientError as e:
        print(f"⚠️  SageMaker endpoint test failed: {e}")
        print("   This is expected if the endpoint doesn't exist yet")
        return False

def main():
    """Main update process"""
    print("🔄 AquaChain Lambda SageMaker Update")
    print("=" * 40)
    
    # Update Lambda environment
    if not update_lambda_environment():
        print("❌ Failed to update Lambda environment")
        return False
    
    # Update IAM permissions
    update_lambda_permissions()  # Don't fail if this doesn't work
    
    # Test endpoint
    test_sagemaker_endpoint()
    
    print("\n✅ Lambda update completed!")
    print("\nNext steps:")
    print("1. Deploy SageMaker models: python lambda/ml_inference/sagemaker_model_setup.py")
    print("2. Test IoT data pipeline")
    print("3. Monitor CloudWatch metrics")
    
    return True

if __name__ == "__main__":
    main()