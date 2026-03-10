#!/usr/bin/env python3
"""
Deploy Device Management Lambda Function
Cross-platform Python deployment script
"""

import os
import sys
import shutil
import zipfile
import subprocess
import json
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

# Configuration
ENVIRONMENT = sys.argv[1] if len(sys.argv) > 1 else 'dev'
FUNCTION_NAME = f'aquachain-function-device-management-{ENVIRONMENT}'
REGION = 'ap-south-1'
LAMBDA_DIR = Path('lambda/device_management')
BUILD_DIR = LAMBDA_DIR / 'build'
ZIP_FILE = f'device-management-{ENVIRONMENT}.zip'

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name=REGION)
iam_client = boto3.client('iam', region_name=REGION)


def print_header(message):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(message)
    print("=" * 60 + "\n")


def print_step(step_num, message):
    """Print step message"""
    print(f"Step {step_num}: {message}...")


def clean_build():
    """Clean previous build"""
    print_step(1, "Cleaning previous build")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if Path(ZIP_FILE).exists():
        os.remove(ZIP_FILE)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    print("[OK] Build directory cleaned")


def copy_lambda_code():
    """Copy Lambda code"""
    print_step(2, "Copying Lambda code")
    
    # Copy handler
    shutil.copy(LAMBDA_DIR / 'handler.py', BUILD_DIR / 'handler.py')
    
    # Copy requirements if exists
    if (LAMBDA_DIR / 'requirements.txt').exists():
        shutil.copy(LAMBDA_DIR / 'requirements.txt', BUILD_DIR / 'requirements.txt')
    
    print("[OK] Lambda code copied")


def copy_shared_dependencies():
    """Copy shared dependencies"""
    print_step(3, "Copying shared dependencies")
    
    shared_dir = Path('lambda/shared')
    if shared_dir.exists():
        for py_file in shared_dir.glob('*.py'):
            if py_file.name != '__init__.py':
                shutil.copy(py_file, BUILD_DIR / py_file.name)
        print("[OK] Shared dependencies copied")
    else:
        print("[WARN] No shared dependencies found")


def install_dependencies():
    """Install Python dependencies"""
    print_step(4, "Installing Python dependencies")
    
    requirements_file = BUILD_DIR / 'requirements.txt'
    if requirements_file.exists():
        try:
            # Read requirements and filter out test dependencies
            with open(requirements_file, 'r') as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            # Only install production dependencies
            prod_requirements = [req for req in requirements if not any(test_pkg in req for test_pkg in ['pytest', 'moto', 'mock'])]
            
            if prod_requirements:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install'] + prod_requirements + ['-t', str(BUILD_DIR), '--quiet'],
                    check=True
                )
                print(f"[OK] Dependencies installed ({len(prod_requirements)} packages)")
            else:
                print("[WARN] No production dependencies to install")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install dependencies: {e}")
            sys.exit(1)
    else:
        print("[WARN] No requirements.txt found, skipping dependency installation")


def create_deployment_package():
    """Create ZIP deployment package"""
    print_step(5, "Creating deployment package")
    
    try:
        with zipfile.ZipFile(ZIP_FILE, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(BUILD_DIR):
                # Skip __pycache__ and .pyc files
                dirs[:] = [d for d in dirs if d != '__pycache__']
                
                for file in files:
                    if file.endswith('.pyc'):
                        continue
                    
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(BUILD_DIR)
                    zipf.write(file_path, arcname)
        
        # Verify ZIP was created
        if not Path(ZIP_FILE).exists():
            raise Exception("ZIP file was not created")
        
        zip_size = Path(ZIP_FILE).stat().st_size / (1024 * 1024)  # MB
        print(f"[OK] Deployment package created ({zip_size:.2f} MB)")
        
    except Exception as e:
        print(f"[ERROR] Failed to create ZIP file: {e}")
        sys.exit(1)


def check_lambda_exists():
    """Check if Lambda function exists"""
    print_step(6, "Checking if Lambda function exists")
    
    try:
        lambda_client.get_function(FunctionName=FUNCTION_NAME)
        print(f"[OK] Lambda function exists: {FUNCTION_NAME}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"[WARN] Lambda function does not exist: {FUNCTION_NAME}")
            return False
        raise


def get_execution_role_arn():
    """Get Lambda execution role ARN"""
    # Try multiple role names
    role_names = [
        'AquaChainLambdaExecutionRole',
        'aquachain-lambda-execution-role',
        'AquaChain-DataProcessing-Lambda-Role'
    ]
    
    for role_name in role_names:
        try:
            response = iam_client.get_role(RoleName=role_name)
            print(f"[OK] Using execution role: {role_name}")
            return response['Role']['Arn']
        except ClientError:
            continue
    
    print("[ERROR] No suitable Lambda execution role found")
    print("Tried roles:", ', '.join(role_names))
    print("Please create a Lambda execution role first")
    sys.exit(1)


def create_lambda_function(role_arn):
    """Create new Lambda function"""
    print("Creating Lambda function...")
    
    with open(ZIP_FILE, 'rb') as f:
        zip_content = f.read()
    
    try:
        response = lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.11',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Code={'ZipFile': zip_content},
            Timeout=30,
            MemorySize=512,
            Environment={
                'Variables': {
                    'DEVICES_TABLE': 'AquaChain-Devices',
                    'USERS_TABLE': 'AquaChain-Users',
                    'ENVIRONMENT': ENVIRONMENT
                }
            }
        )
        print(f"[OK] Lambda function created: {response['FunctionArn']}")
        return True
    except ClientError as e:
        print(f"[ERROR] Failed to create Lambda function: {e}")
        return False


def update_lambda_function():
    """Update existing Lambda function"""
    print("Updating Lambda function code...")
    
    with open(ZIP_FILE, 'rb') as f:
        zip_content = f.read()
    
    try:
        # Update code
        lambda_client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=zip_content
        )
        print("[OK] Lambda code updated")
        
        # Wait for update to complete
        print("Waiting for update to complete...")
        waiter = lambda_client.get_waiter('function_updated')
        waiter.wait(FunctionName=FUNCTION_NAME)
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=FUNCTION_NAME,
            Environment={
                'Variables': {
                    'DEVICES_TABLE': 'AquaChain-Devices',
                    'USERS_TABLE': 'AquaChain-Users',
                    'ENVIRONMENT': ENVIRONMENT
                }
            }
        )
        print("[OK] Lambda configuration updated")
        return True
        
    except ClientError as e:
        print(f"[ERROR] Failed to update Lambda function: {e}")
        return False


def verify_deployment():
    """Verify deployment"""
    print_step(7, "Verifying deployment")
    
    try:
        response = lambda_client.get_function(FunctionName=FUNCTION_NAME)
        config = response['Configuration']
        
        print(f"[OK] Function Name: {config['FunctionName']}")
        print(f"[OK] Runtime: {config['Runtime']}")
        print(f"[OK] Last Modified: {config['LastModified']}")
        print(f"[OK] Memory: {config['MemorySize']} MB")
        print(f"[OK] Timeout: {config['Timeout']} seconds")
        
        return True
    except ClientError as e:
        print(f"[ERROR] Verification failed: {e}")
        return False


def test_lambda():
    """Test Lambda function"""
    print_step(8, "Testing Lambda function")
    
    test_event = {
        'httpMethod': 'GET',
        'path': '/devices',
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-123'
                }
            }
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        payload = json.loads(response['Payload'].read())
        print(f"[OK] Lambda invocation successful")
        print(f"Response: {json.dumps(payload, indent=2)}")
        
        return True
    except Exception as e:
        print(f"[WARN] Lambda invocation failed: {e}")
        return False


def cleanup():
    """Cleanup temporary files"""
    print("\nCleaning up temporary files...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    print("[OK] Cleanup complete")


def main():
    """Main deployment function"""
    print_header("Device Management Lambda Deployment")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Function Name: {FUNCTION_NAME}")
    print(f"Region: {REGION}\n")
    
    try:
        # Build package
        clean_build()
        copy_lambda_code()
        copy_shared_dependencies()
        install_dependencies()
        create_deployment_package()
        
        # Deploy
        exists = check_lambda_exists()
        
        if exists:
            success = update_lambda_function()
        else:
            role_arn = get_execution_role_arn()
            success = create_lambda_function(role_arn)
        
        if not success:
            print("\n[ERROR] Deployment failed")
            sys.exit(1)
        
        # Verify
        verify_deployment()
        test_lambda()
        
        # Success
        print_header("Deployment Complete!")
        print(f"Function Name: {FUNCTION_NAME}")
        print(f"Region: {REGION}")
        print(f"Environment: {ENVIRONMENT}\n")
        
        print("Next Steps:")
        print("1. Configure API Gateway routes:")
        print(f"   python scripts/deployment/configure-api-gateway-devices.py {ENVIRONMENT}")
        print("2. Test endpoints via API Gateway")
        print("3. Monitor CloudWatch logs\n")
        
        print("API Gateway Routes needed:")
        print("  POST   /api/devices/register")
        print("  GET    /api/devices")
        print("  GET    /api/devices/{deviceId}")
        print("  DELETE /api/devices/{deviceId}\n")
        
    except KeyboardInterrupt:
        print("\n\n[ERROR] Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cleanup()


if __name__ == '__main__':
    main()

