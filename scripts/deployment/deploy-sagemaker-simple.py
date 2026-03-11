#!/usr/bin/env python3
"""
Simple SageMaker Deployment Script

This is a simplified version that handles errors gracefully and provides
clear feedback at each step.
"""

import boto3
import json
import sys
import os
from botocore.exceptions import ClientError, NoCredentialsError

def check_aws_credentials():
    """Check AWS credentials first"""
    print("🔑 Checking AWS credentials...")
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        account_id = identity['Account']
        print(f"✅ AWS Account: {account_id}")
        print(f"✅ User/Role: {identity['Arn']}")
        return account_id
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("   Run: aws configure")
        return None
    except ClientError as e:
        print(f"❌ AWS credentials error: {e}")
        return None

def create_s3_bucket(account_id):
    """Create S3 bucket for models"""
    print("📦 Creating S3 bucket for ML models...")
    
    bucket_name = f'aquachain-ml-models-dev-{account_id}'
    s3_client = boto3.client('s3', region_name='ap-south-1')
    
    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket already exists: {bucket_name}")
        return bucket_name
    except ClientError:
        # Create bucket
        try:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': 'ap-south-1'}
            )
            print(f"✅ Created bucket: {bucket_name}")
            return bucket_name
        except ClientError as e:
            print(f"❌ Failed to create bucket: {e}")
            return None

def cleanup_existing_sagemaker_resources():
    """Clean up existing SageMaker resources to avoid conflicts"""
    print("🧹 Cleaning up existing SageMaker resources...")
    
    sagemaker_client = boto3.client('sagemaker', region_name='ap-south-1')
    
    # Delete existing endpoint
    try:
        endpoint_name = 'aquachain-wqi-endpoint-dev'
        sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        print(f"   Deleting endpoint: {endpoint_name}")
        sagemaker_client.delete_endpoint(EndpointName=endpoint_name)
        
        # Wait for endpoint deletion
        import time
        while True:
            try:
                sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
                print("   Waiting for endpoint deletion...")
                time.sleep(10)
            except ClientError as e:
                if 'ValidationException' in str(e):
                    print("   ✅ Endpoint deleted")
                    break
                raise
                
    except ClientError as e:
        if 'ValidationException' in str(e):
            print("   No existing endpoint found")
        else:
            print(f"   ⚠️  Error checking endpoint: {e}")
    
    # Delete existing endpoint config
    try:
        config_name = 'aquachain-wqi-endpoint-config-dev'
        sagemaker_client.describe_endpoint_config(EndpointConfigName=config_name)
        print(f"   Deleting endpoint config: {config_name}")
        sagemaker_client.delete_endpoint_config(EndpointConfigName=config_name)
        print("   ✅ Endpoint config deleted")
    except ClientError as e:
        if 'ValidationException' in str(e):
            print("   No existing endpoint config found")
        else:
            print(f"   ⚠️  Error checking endpoint config: {e}")
    
    # Delete existing model (already done, but check)
    try:
        model_name = 'aquachain-wqi-model-dev'
        sagemaker_client.describe_model(ModelName=model_name)
        print(f"   Deleting model: {model_name}")
        sagemaker_client.delete_model(ModelName=model_name)
        print("   ✅ Model deleted")
    except ClientError as e:
        if 'ValidationException' in str(e):
            print("   No existing model found")
        else:
            print(f"   ⚠️  Error checking model: {e}")

def deploy_cdk_stack():
    """Deploy SageMaker CDK stack"""
    print("🏗️  Deploying SageMaker CDK stack...")
    
    # Change to CDK directory
    cdk_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'infrastructure', 'cdk')
    original_dir = os.getcwd()
    
    try:
        os.chdir(cdk_dir)
        
        # Run CDK deploy with shell=True to use PATH
        import subprocess
        result = subprocess.run([
            'cdk', 'deploy', 'AquaChain-SageMaker-dev', 
            '--require-approval', 'never'
        ], capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print("✅ SageMaker CDK stack deployed successfully")
            return True
        else:
            print(f"❌ CDK deployment failed:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ CDK deployment error: {e}")
        return False
    finally:
        os.chdir(original_dir)

def get_stack_outputs():
    """Get CloudFormation stack outputs for endpoint name"""
    print("📋 Getting stack outputs...")
    
    cf_client = boto3.client('cloudformation', region_name='ap-south-1')
    stack_name = 'AquaChain-SageMaker-dev'
    
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
        
        outputs = {}
        for output in stack.get('Outputs', []):
            outputs[output['OutputKey']] = output['OutputValue']
        
        print(f"✅ Stack outputs retrieved:")
        for key, value in outputs.items():
            print(f"   {key}: {value}")
        
        return outputs
        
    except ClientError as e:
        print(f"❌ Failed to get stack outputs: {e}")
        return {}

def update_lambda_environment(stack_outputs):
    """Update Lambda environment variables"""
    print("🔄 Updating Lambda environment variables...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    function_name = 'aquachain-function-data-processing-dev'
    
    # Get endpoint name from stack outputs
    endpoint_name = stack_outputs.get('SageMakerEndpointName')
    if not endpoint_name:
        print("⚠️  No SageMaker endpoint name found in stack outputs")
        return False
    
    try:
        # Get current environment
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        # Update environment variables
        env_vars['SAGEMAKER_ENDPOINT_NAME'] = endpoint_name
        
        # Remove old ML function variable if exists
        if 'ML_INFERENCE_FUNCTION' in env_vars:
            del env_vars['ML_INFERENCE_FUNCTION']
        
        # Update function
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': env_vars}
        )
        
        print(f"✅ Updated Lambda environment: {function_name}")
        print(f"   SAGEMAKER_ENDPOINT_NAME: {endpoint_name}")
        return True
        
    except ClientError as e:
        print(f"❌ Failed to update Lambda: {e}")
        return False

def test_sagemaker_endpoint(stack_outputs):
    """Test SageMaker endpoint"""
    print("🧪 Testing SageMaker endpoint...")
    
    runtime = boto3.client('sagemaker-runtime', region_name='ap-south-1')
    
    # Get endpoint name from stack outputs
    endpoint_name = stack_outputs.get('SageMakerEndpointName')
    if not endpoint_name:
        print("⚠️  No SageMaker endpoint name found in stack outputs")
        return False
    
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
    """Main deployment process"""
    print("🚀 AquaChain SageMaker Simple Deployment")
    print("=" * 50)
    
    # Step 1: Check credentials
    account_id = check_aws_credentials()
    if not account_id:
        print("\n❌ Cannot proceed without AWS credentials")
        print("Run: aws configure")
        return False
    
    print(f"\n🎯 Deploying to account: {account_id}")
    print("=" * 50)
    
    # Step 2: Clean up existing resources
    cleanup_existing_sagemaker_resources()
    
    # Step 3: Create S3 bucket
    bucket_name = create_s3_bucket(account_id)
    if not bucket_name:
        print("\n❌ Failed to create S3 bucket")
        return False
    
    # Step 4: Deploy CDK stack
    if not deploy_cdk_stack():
        print("\n❌ CDK deployment failed")
        return False
    
    # Step 5: Get stack outputs
    stack_outputs = get_stack_outputs()
    if not stack_outputs:
        print("\n❌ Failed to get stack outputs")
        return False
    
    # Step 6: Update Lambda
    if not update_lambda_environment(stack_outputs):
        print("\n❌ Lambda update failed")
        return False
    
    # Step 7: Test endpoint (optional)
    test_sagemaker_endpoint(stack_outputs)
    
    print("\n🎉 SageMaker deployment completed!")
    print("\nNext steps:")
    print("1. Setup pre-trained models: python lambda/ml_inference/sagemaker_model_setup.py")
    print("2. Test IoT data pipeline")
    print("3. Monitor CloudWatch metrics")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)