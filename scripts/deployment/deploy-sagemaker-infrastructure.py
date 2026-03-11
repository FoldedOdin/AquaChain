#!/usr/bin/env python3
"""
Deploy SageMaker Infrastructure for AquaChain

This script deploys the complete SageMaker infrastructure:
1. Creates SageMaker stack with CDK
2. Sets up model training and endpoint
3. Updates Lambda functions to use SageMaker
4. Tests the complete pipeline
"""

import boto3
import subprocess
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Configuration
REGION = 'ap-south-1'
ENVIRONMENT = 'dev'  # Change as needed

def get_account_id():
    """Get AWS account ID safely"""
    try:
        return boto3.client('sts').get_caller_identity()['Account']
    except Exception as e:
        print(f"❌ Error getting AWS account ID: {e}")
        print("Please ensure AWS credentials are configured:")
        print("  1. Run 'aws configure' to set up credentials")
        print("  2. Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        print("  3. Or ensure IAM role is attached if running on EC2")
        sys.exit(1)

def run_command(command: str, cwd: str = None) -> tuple:
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            command.split(),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def deploy_cdk_stack():
    """Deploy SageMaker CDK stack"""
    print("🏗️  Deploying SageMaker CDK stack...")
    
    # Change to infrastructure directory
    infra_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'infrastructure', 'cdk')
    
    # Deploy SageMaker stack
    success, output = run_command(
        f"cdk deploy AquaChain-SageMaker-{ENVIRONMENT} --require-approval never",
        cwd=infra_dir
    )
    
    if success:
        print("✅ SageMaker stack deployed successfully")
        return True
    else:
        print(f"❌ SageMaker stack deployment failed: {output}")
        return False

def create_model_bucket(account_id: str):
    """Create S3 bucket for ML models if it doesn't exist"""
    print("📦 Setting up model bucket...")
    
    s3_client = boto3.client('s3')
    bucket_name = f'aquachain-ml-models-{ENVIRONMENT}-{account_id}'
    
    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket {bucket_name} already exists")
    except:
        # Create bucket
        try:
            if REGION == 'us-east-1':
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': REGION}
                )
            
            # Enable versioning
            s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            print(f"✅ Created bucket: {bucket_name}")
        except Exception as e:
            print(f"❌ Failed to create bucket: {e}")
            return False
    
    return bucket_name

def setup_sagemaker_model():
    """Set up SageMaker model training and endpoint"""
    print("🤖 Setting up SageMaker model...")
    
    # Run the model setup script
    model_setup_script = os.path.join(
        os.path.dirname(__file__), '..', '..', 'lambda', 'ml_inference', 'sagemaker_model_setup.py'
    )
    
    success, output = run_command(f"python {model_setup_script}")
    
    if success:
        print("✅ SageMaker model setup completed")
        print(output)
        return True
    else:
        print(f"❌ SageMaker model setup failed: {output}")
        return False

def update_lambda_functions(account_id: str):
    """Update Lambda functions to use SageMaker"""
    print("🔄 Updating Lambda functions...")
    
    lambda_client = boto3.client('lambda')
    
    # Update data processing Lambda environment variables
    function_name = f'aquachain-function-data-processing-{ENVIRONMENT}'
    endpoint_name = f'aquachain-wqi-endpoint-{ENVIRONMENT}'
    
    try:
        # Get current environment variables
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        # Update environment variables
        env_vars['SAGEMAKER_ENDPOINT_NAME'] = endpoint_name
        
        # Remove old ML_INFERENCE_FUNCTION if it exists
        if 'ML_INFERENCE_FUNCTION' in env_vars:
            del env_vars['ML_INFERENCE_FUNCTION']
        
        # Update function
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': env_vars}
        )
        
        print(f"✅ Updated {function_name} environment variables")
        
        # Update IAM role to include SageMaker permissions
        iam_client = boto3.client('iam')
        role_name = f'aquachain-role-data-processing-{ENVIRONMENT}'
        
        # Create SageMaker invoke policy
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "sagemaker:InvokeEndpoint"
                    ],
                    "Resource": [
                        f"arn:aws:sagemaker:{REGION}:{account_id}:endpoint/{endpoint_name}"
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
        except Exception as e:
            print(f"⚠️  Warning: Could not update IAM permissions: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update Lambda function: {e}")
        return False

def test_sagemaker_integration():
    """Test the complete SageMaker integration"""
    print("🧪 Testing SageMaker integration...")
    
    # Test SageMaker endpoint directly
    runtime = boto3.client('sagemaker-runtime')
    endpoint_name = f'aquachain-wqi-endpoint-{ENVIRONMENT}'
    
    test_payload = {
        'deviceId': 'ESP32-INTEGRATION-TEST',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'readings': {
            'pH': 7.1,
            'turbidity': 3.2,
            'tds': 420,
            'temperature': 24.5
        },
        'location': {
            'latitude': 12.9716,
            'longitude': 77.5946
        }
    }
    
    try:
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Accept='application/json',
            Body=json.dumps(test_payload)
        )
        
        result = json.loads(response['Body'].read().decode('utf-8'))
        
        print("✅ SageMaker endpoint test successful:")
        print(f"   WQI: {result['wqi']}")
        print(f"   Anomaly Type: {result['anomalyType']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Model Version: {result['modelVersion']}")
        
        return True
        
    except Exception as e:
        print(f"❌ SageMaker endpoint test failed: {e}")
        return False

def test_lambda_integration():
    """Test Lambda integration with SageMaker"""
    print("🔗 Testing Lambda-SageMaker integration...")
    
    lambda_client = boto3.client('lambda')
    function_name = f'aquachain-function-data-processing-{ENVIRONMENT}'
    
    # Simulate IoT message
    test_event = {
        "deviceId": "ESP32-LAMBDA-TEST",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "location": {
            "latitude": 12.9716,
            "longitude": 77.5946
        },
        "readings": {
            "pH": 6.8,
            "turbidity": 4.1,
            "tds": 380,
            "temperature": 23.2
        },
        "diagnostics": {
            "batteryLevel": 85,
            "signalStrength": -45,
            "firmwareVersion": "2.1.0"
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print("✅ Lambda-SageMaker integration test successful")
            print(f"   Response: {result}")
            return True
        else:
            print(f"❌ Lambda test failed with status {response['StatusCode']}: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Lambda integration test failed: {e}")
        return False

def verify_data_pipeline():
    """Verify the complete data pipeline is working"""
    print("🔍 Verifying complete data pipeline...")
    
    dynamodb = boto3.resource('dynamodb')
    
    # Check if data is being stored in DynamoDB
    readings_table = dynamodb.Table(f'AquaChain-Readings-{ENVIRONMENT}')
    ledger_table = dynamodb.Table(f'aquachain-ledger-{ENVIRONMENT}')
    
    try:
        # Get recent readings
        response = readings_table.scan(Limit=5)
        readings_count = response['Count']
        
        # Get recent ledger entries
        ledger_response = ledger_table.scan(Limit=5)
        ledger_count = ledger_response['Count']
        
        print(f"✅ Data pipeline verification:")
        print(f"   Recent readings: {readings_count}")
        print(f"   Recent ledger entries: {ledger_count}")
        
        # Check if any readings have non-fallback WQI scores
        has_ml_predictions = False
        for item in response.get('Items', []):
            if 'qualityScore' in item and item['qualityScore'] != 50:
                has_ml_predictions = True
                break
        
        if has_ml_predictions:
            print("✅ ML predictions are being generated (non-fallback WQI scores found)")
        else:
            print("⚠️  Only fallback WQI scores found - check SageMaker integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Data pipeline verification failed: {e}")
        return False

def cleanup_old_lambda_ml_function():
    """Clean up old Lambda-based ML inference function"""
    print("🧹 Cleaning up old Lambda ML function...")
    
    lambda_client = boto3.client('lambda')
    old_function_name = f'aquachain-function-ml-inference-{ENVIRONMENT}'
    
    try:
        # Check if function exists
        lambda_client.get_function(FunctionName=old_function_name)
        
        # Function exists, ask user if they want to delete it
        response = input(f"Old ML inference Lambda function '{old_function_name}' found. Delete it? (y/N): ")
        
        if response.lower() == 'y':
            lambda_client.delete_function(FunctionName=old_function_name)
            print(f"✅ Deleted old Lambda function: {old_function_name}")
        else:
            print(f"⚠️  Keeping old Lambda function: {old_function_name}")
            
    except lambda_client.exceptions.ResourceNotFoundException:
        print("✅ No old Lambda ML function to clean up")
    except Exception as e:
        print(f"⚠️  Could not clean up old Lambda function: {e}")

def main():
    """Main deployment process"""
    print("🚀 AquaChain SageMaker Infrastructure Deployment")
    print("=" * 60)
    
    # Get account ID safely
    ACCOUNT_ID = get_account_id()
    
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {REGION}")
    print(f"Account: {ACCOUNT_ID}")
    print("=" * 60)
    
    steps = [
        ("Create Model Bucket", lambda: create_model_bucket(ACCOUNT_ID)),
        ("Deploy CDK Stack", deploy_cdk_stack),
        ("Setup SageMaker Model", setup_sagemaker_model),
        ("Update Lambda Functions", lambda: update_lambda_functions(ACCOUNT_ID)),
        ("Test SageMaker Integration", test_sagemaker_integration),
        ("Test Lambda Integration", test_lambda_integration),
        ("Verify Data Pipeline", verify_data_pipeline),
        ("Cleanup Old Resources", cleanup_old_lambda_ml_function),
    ]
    
    results = []
    
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        print("-" * 40)
        
        try:
            success = step_func()
            results.append((step_name, success))
            
            if success:
                print(f"✅ {step_name} completed successfully")
            else:
                print(f"❌ {step_name} failed")
                
                # Ask if user wants to continue
                response = input("Continue with remaining steps? (y/N): ")
                if response.lower() != 'y':
                    break
                    
        except Exception as e:
            print(f"❌ {step_name} failed with exception: {e}")
            results.append((step_name, False))
            
            response = input("Continue with remaining steps? (y/N): ")
            if response.lower() != 'y':
                break
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    for step_name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{step_name:<30} {status}")
    
    successful_steps = sum(1 for _, success in results if success)
    total_steps = len(results)
    
    print(f"\nCompleted: {successful_steps}/{total_steps} steps")
    
    if successful_steps == total_steps:
        print("\n🎉 SageMaker deployment completed successfully!")
        print("\nNext steps:")
        print("1. Monitor SageMaker endpoint metrics in CloudWatch")
        print("2. Test with real IoT device data")
        print("3. Set up model retraining pipeline")
        print("4. Configure alerts for model performance")
    else:
        print(f"\n⚠️  Deployment partially completed ({successful_steps}/{total_steps} steps)")
        print("Review failed steps and retry as needed.")

if __name__ == "__main__":
    main()