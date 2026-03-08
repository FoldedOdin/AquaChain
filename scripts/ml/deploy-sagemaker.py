#!/usr/bin/env python3
"""
Deploy SageMaker Infrastructure and Training Pipeline
Automates the complete SageMaker setup for AquaChain
"""

import boto3
import subprocess
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(message):
    """Print formatted header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{message}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def print_success(message):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_warning(message):
    """Print warning message"""
    print(f"{YELLOW}⚠ {message}{RESET}")


def print_error(message):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message):
    """Print info message"""
    print(f"{BLUE}ℹ {message}{RESET}")


def check_prerequisites():
    """Check if all prerequisites are met"""
    print_header("Checking Prerequisites")
    
    # Check AWS CLI
    try:
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        print_success(f"AWS CLI: {result.stdout.strip()}")
    except FileNotFoundError:
        print_error("AWS CLI not found. Please install AWS CLI.")
        return False
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print_success(f"AWS Account: {identity['Account']}")
        print_success(f"AWS User: {identity['Arn']}")
    except Exception as e:
        print_error(f"AWS credentials not configured: {e}")
        return False
    
    # Check CDK
    try:
        result = subprocess.run(['cdk', '--version'], capture_output=True, text=True)
        print_success(f"AWS CDK: {result.stdout.strip()}")
    except FileNotFoundError:
        print_error("AWS CDK not found. Please install: npm install -g aws-cdk")
        return False
    
    # Check Python packages
    try:
        import sagemaker
        print_success(f"SageMaker SDK: {sagemaker.__version__}")
    except ImportError:
        print_warning("SageMaker SDK not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'sagemaker'])
    
    return True


def get_environment():
    """Get deployment environment from user"""
    print_header("Select Deployment Environment")
    
    print("1. dev (Development)")
    print("2. staging (Staging)")
    print("3. prod (Production)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    env_map = {
        '1': 'dev',
        '2': 'staging',
        '3': 'prod'
    }
    
    env = env_map.get(choice, 'dev')
    print_info(f"Selected environment: {env}")
    
    return env


def check_model_artifacts(env):
    """Check if model artifacts exist in S3"""
    print_header("Checking Model Artifacts")
    
    s3 = boto3.client('s3')
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    bucket_name = f"aquachain-ml-models-{env}-{account_id}"
    model_key = "ml-models/current/model.tar.gz"
    
    try:
        s3.head_object(Bucket=bucket_name, Key=model_key)
        print_success(f"Model artifacts found: s3://{bucket_name}/{model_key}")
        return True
    except:
        print_warning(f"Model artifacts not found in S3")
        print_info(f"Expected location: s3://{bucket_name}/{model_key}")
        
        upload = input("\nDo you want to upload model artifacts now? (y/n): ").strip().lower()
        if upload == 'y':
            return upload_model_artifacts(env)
        else:
            print_warning("Continuing without model artifacts. Endpoint creation may fail.")
            return False


def upload_model_artifacts(env):
    """Upload model artifacts to S3"""
    print_header("Uploading Model Artifacts")
    
    # Check if models exist locally
    project_root = Path(__file__).parent.parent.parent
    models_dir = project_root / "ml_models_native"
    
    if not models_dir.exists():
        print_error(f"Models directory not found: {models_dir}")
        print_info("Run: python scripts/ml/convert-models-to-native.py")
        return False
    
    # Package models
    print_info("Packaging models for SageMaker...")
    package_script = project_root / "scripts" / "ml" / "package-native-models.py"
    
    try:
        subprocess.run([sys.executable, str(package_script)], check=True)
        print_success("Models packaged successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to package models: {e}")
        return False


def deploy_sagemaker_stack(env):
    """Deploy SageMaker CDK stack"""
    print_header(f"Deploying SageMaker Stack ({env})")
    
    project_root = Path(__file__).parent.parent.parent
    cdk_dir = project_root / "infrastructure" / "cdk"
    
    stack_name = f"AquaChain-SageMaker-{env}"
    
    print_info(f"Deploying stack: {stack_name}")
    print_info("This may take 10-15 minutes...")
    
    try:
        # Change to CDK directory
        os.chdir(cdk_dir)
        
        # Deploy stack
        result = subprocess.run(
            ['cdk', 'deploy', stack_name, '--require-approval', 'never'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success(f"Stack deployed successfully: {stack_name}")
            
            # Extract outputs
            print_info("\nStack Outputs:")
            if "Outputs:" in result.stdout:
                outputs_section = result.stdout.split("Outputs:")[1]
                print(outputs_section)
            
            return True
        else:
            print_error(f"Stack deployment failed")
            print(result.stderr)
            return False
            
    except Exception as e:
        print_error(f"Deployment error: {e}")
        return False


def wait_for_endpoint(env):
    """Wait for SageMaker endpoint to be in service"""
    print_header("Waiting for SageMaker Endpoint")
    
    sagemaker = boto3.client('sagemaker')
    endpoint_name = f"aquachain-wqi-endpoint-{env}"
    
    print_info(f"Endpoint: {endpoint_name}")
    print_info("This may take 5-10 minutes...")
    
    max_wait_time = 600  # 10 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
            status = response['EndpointStatus']
            
            if status == 'InService':
                print_success(f"Endpoint is in service!")
                return True
            elif status in ['Failed', 'RolledBack']:
                print_error(f"Endpoint creation failed: {status}")
                return False
            else:
                print_info(f"Status: {status} (waiting...)")
                time.sleep(30)
                
        except sagemaker.exceptions.ClientError as e:
            if 'Could not find endpoint' in str(e):
                print_info("Endpoint not found yet (waiting...)")
                time.sleep(30)
            else:
                print_error(f"Error checking endpoint: {e}")
                return False
    
    print_warning("Endpoint creation timeout. Check AWS Console for status.")
    return False


def deploy_training_pipeline(env):
    """Deploy SageMaker training pipeline"""
    print_header("Deploying Training Pipeline")
    
    try:
        # Import pipeline module
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lambda" / "ml_inference"))
        from sagemaker_pipeline import AquaChainMLPipeline
        
        # Get AWS account info
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity()['Account']
        region = boto3.Session().region_name or 'ap-south-1'
        
        # Get SageMaker role ARN
        role_arn = f"arn:aws:iam::{account_id}:role/AquaChain-SageMaker-ExecutionRole-{env}"
        bucket_name = f"aquachain-data-lake-{env}"
        
        print_info(f"Role ARN: {role_arn}")
        print_info(f"Bucket: {bucket_name}")
        print_info(f"Region: {region}")
        
        # Initialize pipeline
        pipeline = AquaChainMLPipeline(role_arn, bucket_name, region)
        
        # Create model package group
        print_info("Creating model package group...")
        pipeline.create_model_package_group()
        
        # Deploy pipeline
        print_info("Deploying pipeline...")
        pipeline.deploy_pipeline()
        
        print_success("Training pipeline deployed successfully")
        
        # Ask if user wants to start execution
        start = input("\nDo you want to start pipeline execution now? (y/n): ").strip().lower()
        if start == 'y':
            print_info("Starting pipeline execution...")
            execution = pipeline.start_pipeline_execution()
            print_success(f"Pipeline execution started")
            print_info(f"ARN: {execution['PipelineExecutionArn']}")
        
        return True
        
    except Exception as e:
        print_error(f"Pipeline deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_lambda_config(env):
    """Update Lambda function environment variables"""
    print_header("Updating Lambda Configuration")
    
    lambda_client = boto3.client('lambda')
    function_name = f"AquaChain-Function-MLInference-{env}"
    endpoint_name = f"aquachain-wqi-endpoint-{env}"
    
    try:
        # Get current configuration
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        
        # Update environment variables
        env_vars = response.get('Environment', {}).get('Variables', {})
        env_vars['SAGEMAKER_ENDPOINT_NAME'] = endpoint_name
        env_vars['ENABLE_MONITORING'] = 'true'
        
        # Update function
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': env_vars}
        )
        
        print_success(f"Lambda function updated: {function_name}")
        print_info(f"SAGEMAKER_ENDPOINT_NAME: {endpoint_name}")
        
        return True
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print_warning(f"Lambda function not found: {function_name}")
        print_info("Deploy compute stack first: cdk deploy AquaChain-Compute-{env}")
        return False
    except Exception as e:
        print_error(f"Lambda update failed: {e}")
        return False


def test_inference(env):
    """Test SageMaker inference"""
    print_header("Testing Inference")
    
    lambda_client = boto3.client('lambda')
    function_name = f"AquaChain-Function-MLInference-{env}"
    
    # Test payload
    payload = {
        "deviceId": "ESP32-TEST-001",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "readings": {
            "pH": 7.2,
            "turbidity": 3.5,
            "tds": 450,
            "temperature": 25.0
        },
        "location": {
            "latitude": 19.0760,
            "longitude": 72.8777
        }
    }
    
    print_info("Invoking Lambda function...")
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print_success("Inference successful!")
            
            body = json.loads(result.get('body', '{}'))
            print_info(f"\nResults:")
            print(f"  WQI: {body.get('wqi')}")
            print(f"  Anomaly Type: {body.get('anomalyType')}")
            print(f"  Confidence: {body.get('confidence')}")
            print(f"  Model Version: {body.get('modelVersion')}")
            print(f"  Latency: {body.get('latencyMs')}ms")
            
            return True
        else:
            print_error(f"Inference failed: {result}")
            return False
            
    except Exception as e:
        print_error(f"Test failed: {e}")
        return False


def print_summary(env, results):
    """Print deployment summary"""
    print_header("Deployment Summary")
    
    print(f"Environment: {env}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    for step, success in results.items():
        status = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
        print(f"{status} {step}")
    
    print()
    
    if all(results.values()):
        print_success("All steps completed successfully!")
        print()
        print_info("Next Steps:")
        print("1. Monitor endpoint in AWS Console: SageMaker → Endpoints")
        print("2. View training pipeline: SageMaker → Pipelines")
        print("3. Check CloudWatch logs for inference requests")
        print("4. Set up CloudWatch alarms for monitoring")
    else:
        print_warning("Some steps failed. Review errors above.")
        print()
        print_info("Troubleshooting:")
        print("1. Check AWS Console for detailed error messages")
        print("2. Review CloudWatch logs")
        print("3. Verify IAM permissions")
        print("4. Check S3 bucket access")


def main():
    """Main deployment function"""
    print_header("AquaChain SageMaker Deployment")
    print_info(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites check failed. Exiting.")
        sys.exit(1)
    
    # Get environment
    env = get_environment()
    
    # Deployment steps
    results = {}
    
    # Step 1: Check model artifacts
    results['Model Artifacts'] = check_model_artifacts(env)
    
    # Step 2: Deploy SageMaker stack
    if input("\nDeploy SageMaker stack? (y/n): ").strip().lower() == 'y':
        results['SageMaker Stack'] = deploy_sagemaker_stack(env)
        
        if results['SageMaker Stack']:
            # Step 3: Wait for endpoint
            results['Endpoint Ready'] = wait_for_endpoint(env)
    else:
        print_info("Skipping SageMaker stack deployment")
        results['SageMaker Stack'] = False
        results['Endpoint Ready'] = False
    
    # Step 4: Deploy training pipeline
    if input("\nDeploy training pipeline? (y/n): ").strip().lower() == 'y':
        results['Training Pipeline'] = deploy_training_pipeline(env)
    else:
        print_info("Skipping training pipeline deployment")
        results['Training Pipeline'] = False
    
    # Step 5: Update Lambda configuration
    if results.get('Endpoint Ready', False):
        if input("\nUpdate Lambda configuration? (y/n): ").strip().lower() == 'y':
            results['Lambda Config'] = update_lambda_config(env)
        else:
            print_info("Skipping Lambda configuration")
            results['Lambda Config'] = False
    
    # Step 6: Test inference
    if results.get('Lambda Config', False):
        if input("\nTest inference? (y/n): ").strip().lower() == 'y':
            results['Inference Test'] = test_inference(env)
        else:
            print_info("Skipping inference test")
            results['Inference Test'] = False
    
    # Print summary
    print_summary(env, results)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n\nDeployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
