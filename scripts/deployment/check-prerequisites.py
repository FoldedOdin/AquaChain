#!/usr/bin/env python3
"""
Check Prerequisites for SageMaker Deployment

This script checks all prerequisites before running the main deployment.
"""

import boto3
import subprocess
import sys
import os
from botocore.exceptions import ClientError, NoCredentialsError

def check_python():
    """Check Python version"""
    print("🐍 Checking Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.8+")
        return False

def check_aws_credentials():
    """Check AWS credentials"""
    print("🔑 Checking AWS credentials...")
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Account: {identity['Account']}")
        print(f"✅ User/Role: {identity['Arn']}")
        return True, identity['Account']
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("   Run: aws configure")
        return False, None
    except ClientError as e:
        print(f"❌ AWS credentials error: {e}")
        return False, None

def check_aws_cli():
    """Check AWS CLI"""
    print("⚡ Checking AWS CLI...")
    try:
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ AWS CLI: {result.stdout.strip()}")
            return True
        else:
            print("❌ AWS CLI not found")
            return False
    except FileNotFoundError:
        print("❌ AWS CLI not installed")
        return False

def check_cdk():
    """Check AWS CDK"""
    print("🏗️  Checking AWS CDK...")
    try:
        # Try multiple ways to detect CDK
        result = subprocess.run(['cdk', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ AWS CDK: {result.stdout.strip()}")
            return True
        else:
            # Try with .cmd extension on Windows
            result = subprocess.run(['cdk.cmd', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ AWS CDK: {result.stdout.strip()}")
                return True
            else:
                print("❌ AWS CDK not found")
                return False
    except FileNotFoundError:
        # Try npx as fallback
        try:
            result = subprocess.run(['npx', 'cdk', '--version'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print(f"✅ AWS CDK (via npx): {result.stdout.strip()}")
                return True
            else:
                print("❌ AWS CDK not installed")
                print("   Install: npm install -g aws-cdk")
                return False
        except FileNotFoundError:
            print("❌ AWS CDK not installed")
            print("   Install: npm install -g aws-cdk")
            return False

def check_sagemaker_permissions(account_id):
    """Check SageMaker permissions"""
    print("🤖 Checking SageMaker permissions...")
    try:
        sagemaker = boto3.client('sagemaker')
        
        # Try to list endpoints (basic permission check)
        sagemaker.list_endpoints(MaxResults=1)
        print("✅ SageMaker permissions - OK")
        
        # Check if execution role exists or can be created
        iam = boto3.client('iam')
        role_name = f'AquaChain-SageMaker-ExecutionRole-dev'
        
        try:
            iam.get_role(RoleName=role_name)
            print(f"✅ SageMaker execution role exists: {role_name}")
        except iam.exceptions.NoSuchEntityException:
            print(f"ℹ️  SageMaker execution role will be created: {role_name}")
        
        return True
    except ClientError as e:
        print(f"❌ SageMaker permissions error: {e}")
        print("   Ensure your AWS user/role has SageMaker permissions")
        return False

def check_s3_permissions(account_id):
    """Check S3 permissions"""
    print("📦 Checking S3 permissions...")
    try:
        s3 = boto3.client('s3')
        
        # Try to list buckets
        s3.list_buckets()
        print("✅ S3 permissions - OK")
        
        # Check if model bucket exists
        bucket_name = f'aquachain-ml-models-dev-{account_id}'
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"✅ Model bucket exists: {bucket_name}")
        except ClientError:
            print(f"ℹ️  Model bucket will be created: {bucket_name}")
        
        return True
    except ClientError as e:
        print(f"❌ S3 permissions error: {e}")
        return False

def check_existing_models():
    """Check if pre-trained models exist"""
    print("🧠 Checking existing ML models...")
    
    models_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'ml_models_backup')
    
    required_files = [
        'WQI-model-v1.0.pkl',
        'Anomaly-model-v1.0.pkl',
        'feature-scaler-v1.0.pkl',
        'model-metadata-v1.0.json'
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(models_dir, file)
        if os.path.exists(file_path):
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing {len(missing_files)} required model files")
        print("   Run: python lambda/ml_inference/create_initial_models.py")
        return False
    else:
        print("✅ All required model files found")
        return True

def check_lambda_functions():
    """Check if required Lambda functions exist"""
    print("⚡ Checking Lambda functions...")
    
    lambda_client = boto3.client('lambda')
    required_functions = [
        'aquachain-function-data-processing-dev'
    ]
    
    missing_functions = []
    for func_name in required_functions:
        try:
            lambda_client.get_function(FunctionName=func_name)
            print(f"✅ Found Lambda: {func_name}")
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"❌ Missing Lambda: {func_name}")
            missing_functions.append(func_name)
        except ClientError as e:
            print(f"⚠️  Error checking Lambda {func_name}: {e}")
    
    if missing_functions:
        print(f"❌ Missing {len(missing_functions)} required Lambda functions")
        print("   Deploy core infrastructure first")
        return False
    else:
        print("✅ All required Lambda functions found")
        return True

def main():
    """Run all prerequisite checks"""
    print("🔍 AquaChain SageMaker Prerequisites Check")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python),
        ("AWS CLI", check_aws_cli),
        ("AWS CDK", check_cdk),
        ("AWS Credentials", check_aws_credentials),
    ]
    
    results = []
    account_id = None
    
    # Run basic checks first
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)
        
        if check_name == "AWS Credentials":
            success, account_id = check_func()
        else:
            success = check_func()
        
        results.append((check_name, success))
        
        if not success:
            print(f"\n❌ {check_name} failed - fix this before continuing")
            break
    
    # If basic checks pass, run AWS-specific checks
    if all(result[1] for result in results) and account_id:
        print(f"\n🎯 AWS-Specific Checks (Account: {account_id})")
        print("=" * 50)
        
        aws_checks = [
            ("SageMaker Permissions", lambda: check_sagemaker_permissions(account_id)),
            ("S3 Permissions", lambda: check_s3_permissions(account_id)),
            ("Existing ML Models", check_existing_models),
            ("Lambda Functions", check_lambda_functions),
        ]
        
        for check_name, check_func in aws_checks:
            print(f"\n📋 {check_name}")
            print("-" * 30)
            success = check_func()
            results.append((check_name, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 PREREQUISITES SUMMARY")
    print("=" * 50)
    
    for check_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{check_name:<25} {status}")
    
    passed_checks = sum(1 for _, success in results if success)
    total_checks = len(results)
    
    print(f"\nResult: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("\n🎉 All prerequisites met! Ready for SageMaker deployment.")
        print("\nNext step:")
        print("  python scripts/deployment/deploy-sagemaker-infrastructure.py")
    else:
        print(f"\n⚠️  {total_checks - passed_checks} issues need to be resolved before deployment.")
        print("\nCommon fixes:")
        print("  - AWS credentials: aws configure")
        print("  - AWS CDK: npm install -g aws-cdk")
        print("  - ML models: python lambda/ml_inference/create_initial_models.py")
        print("  - Core infrastructure: cdk deploy AquaChain-Core-dev")

if __name__ == "__main__":
    main()