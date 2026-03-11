#!/usr/bin/env python3
"""
Deploy Technician Dashboard Updates
This script deploys the updated API Gateway routes and Lambda function for technician dashboard
"""

import os
import sys
import zipfile
import subprocess
import time
from pathlib import Path

def print_header(message):
    """Print formatted header"""
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50 + "\n")

def print_step(step_num, total_steps, message):
    """Print formatted step"""
    print(f"[{step_num}/{total_steps}] {message}...")

def create_lambda_package():
    """Create Lambda deployment package"""
    print_step(1, 3, "Packaging technician service Lambda")
    
    # Change to Lambda directory
    lambda_dir = Path("lambda/technician_service")
    if not lambda_dir.exists():
        print(f"ERROR: Lambda directory not found: {lambda_dir}")
        return False
    
    os.chdir(lambda_dir)
    
    # Remove old package
    if Path("deployment.zip").exists():
        os.remove("deployment.zip")
    
    # Files to include
    files_to_include = [
        "handler.py",
        "assignment_algorithm.py",
        "audit_logger.py",
        "availability_manager.py",
        "cors_utils.py",
        "location_service.py",
        "service_request_manager.py",
        "structured_logger.py",
        "requirements.txt"
    ]
    
    # Create zip file
    try:
        with zipfile.ZipFile("deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in files_to_include:
                if Path(file).exists():
                    zipf.write(file)
                    print(f"  Added: {file}")
                else:
                    print(f"  WARNING: File not found: {file}")
        
        print("Lambda package created successfully")
        return True
    except Exception as e:
        print(f"ERROR: Failed to create deployment package: {e}")
        return False

def update_lambda_function(environment):
    """Update Lambda function code"""
    print_step(2, 3, "Updating Lambda function")
    
    function_name = f"AquaChain-Function-ServiceRequest-{environment}"
    
    try:
        result = subprocess.run([
            "aws", "lambda", "update-function-code",
            "--function-name", function_name,
            "--zip-file", "fileb://deployment.zip",
            "--region", "ap-south-1"
        ], capture_output=True, text=True, check=True)
        
        print(f"Lambda function {function_name} updated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to update Lambda function")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print("ERROR: AWS CLI not found. Please install AWS CLI.")
        return False

def deploy_cdk_stacks(environment):
    """Deploy CDK stacks"""
    print_step(3, 3, "Deploying CDK stacks")
    
    # Change to CDK directory (use absolute path)
    cdk_dir = Path("infrastructure/cdk")
    if not cdk_dir.exists():
        print(f"ERROR: CDK directory not found: {cdk_dir}")
        return False
    
    os.chdir(cdk_dir)
    
    # Deploy Compute stack first (creates Lambda)
    compute_stack = f"AquaChain-Compute-{environment}"
    print(f"\n  Deploying {compute_stack}...")
    
    try:
        subprocess.run([
            "cdk", "deploy", compute_stack,
            "--require-approval", "never"
        ], check=True)
        
        print(f"  {compute_stack} deployed successfully")
    except subprocess.CalledProcessError:
        print(f"  ERROR: Failed to deploy {compute_stack}")
        return False
    except FileNotFoundError:
        print("  ERROR: CDK CLI not found. Please install AWS CDK.")
        return False
    
    # Wait for Lambda to be ready
    print("\n  Waiting for Lambda to be ready...")
    time.sleep(10)
    
    # Deploy API stack (creates routes)
    api_stack = f"AquaChain-API-{environment}"
    print(f"\n  Deploying {api_stack}...")
    
    try:
        subprocess.run([
            "cdk", "deploy", api_stack,
            "--require-approval", "never"
        ], check=True)
        
        print(f"  {api_stack} deployed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"  ERROR: Failed to deploy {api_stack}")
        return False

def main():
    """Main deployment function"""
    print_header("Deploying Technician Dashboard Updates")
    
    # Get environment from command line
    environment = sys.argv[1] if len(sys.argv) > 1 else "dev"
    print(f"Environment: {environment}\n")
    
    # Save current directory
    original_dir = os.getcwd()
    
    try:
        # Step 1: Create Lambda package
        if not create_lambda_package():
            print("\nDeployment failed at step 1")
            return 1
        
        print()
        
        # Step 2: Deploy CDK stacks (this will create/update the Lambda)
        os.chdir(original_dir)
        if not deploy_cdk_stacks(environment):
            print("\nDeployment failed at step 2")
            return 1
        
        # Success message
        print_header("Deployment Complete!")
        print("\nNew API routes available:")
        print("  - GET  /api/v1/technician/tasks")
        print("  - POST /api/v1/technician/tasks/{taskId}/accept")
        print("  - PUT  /api/v1/technician/tasks/{taskId}/status")
        print("  - POST /api/v1/technician/tasks/{taskId}/notes")
        print("  - POST /api/v1/technician/tasks/{taskId}/complete")
        print("  - GET  /api/v1/technician/tasks/history")
        print("  - GET  /api/v1/technician/tasks/{taskId}/route")
        print("  - PUT  /api/v1/technician/location")
        print("\nThe technician dashboard should now display real data from DynamoDB.\n")
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        return 1
    finally:
        # Return to original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    sys.exit(main())
