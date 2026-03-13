#!/usr/bin/env python3
"""
Deploy Issues Service
Creates the Lambda function and DynamoDB table for issue reporting
"""

import boto3
import json
import os
import sys
import zipfile
import tempfile
from pathlib import Path

def deploy_issues_service():
    """Deploy the issues service Lambda and DynamoDB table"""
    
    print("🔧 Deploying Issues Service...")
    
    # Initialize AWS clients
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    dynamodb_client = boto3.client('dynamodb', region_name='ap-south-1')
    iam_client = boto3.client('iam', region_name='ap-south-1')
    
    try:
        # Step 1: Create DynamoDB table for issues
        print("📋 Step 1: Creating DynamoDB table...")
        
        table_name = 'aquachain-issues'
        
        try:
            dynamodb_client.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'issue_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'issue_id',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'AquaChain'
                    },
                    {
                        'Key': 'Environment',
                        'Value': 'dev'
                    }
                ]
            )
            print(f"✅ Created DynamoDB table: {table_name}")
        except dynamodb_client.exceptions.ResourceInUseException:
            print(f"✅ DynamoDB table {table_name} already exists")
        
        # Step 2: Create IAM role for Lambda
        print("📋 Step 2: Creating IAM role...")
        
        role_name = 'AquaChain-IssuesService-Role'
        
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
            iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='IAM role for AquaChain Issues Service Lambda'
            )
            print(f"✅ Created IAM role: {role_name}")
        except iam_client.exceptions.EntityAlreadyExistsException:
            print(f"✅ IAM role {role_name} already exists")
        
        # Attach policies to the role
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
            'arn:aws:iam::aws:policy/AmazonSESFullAccess'
        ]
        
        for policy_arn in policies:
            try:
                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
                print(f"✅ Attached policy: {policy_arn}")
            except Exception as e:
                print(f"⚠️ Policy may already be attached: {e}")
        
        # Step 3: Package Lambda function
        print("📋 Step 3: Packaging Lambda function...")
        
        lambda_dir = Path('lambda/issues_service')
        if not lambda_dir.exists():
            print(f"❌ Lambda directory not found: {lambda_dir}")
            return False
        
        # Create deployment package
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add handler.py
                handler_path = lambda_dir / 'handler.py'
                if handler_path.exists():
                    zip_file.write(handler_path, 'handler.py')
                    print("✅ Added handler.py to package")
                else:
                    print("❌ handler.py not found")
                    return False
            
            # Step 4: Deploy Lambda function
            print("📋 Step 4: Deploying Lambda function...")
            
            function_name = 'AquaChain-Function-IssuesService-dev'
            
            with open(temp_zip.name, 'rb') as zip_data:
                try:
                    lambda_client.create_function(
                        FunctionName=function_name,
                        Runtime='python3.11',
                        Role=f'arn:aws:iam::{boto3.client("sts").get_caller_identity()["Account"]}:role/{role_name}',
                        Handler='handler.lambda_handler',
                        Code={'ZipFile': zip_data.read()},
                        Description='AquaChain Issues Service',
                        Timeout=30,
                        Environment={
                            'Variables': {
                                'ISSUES_TABLE_NAME': table_name,
                                'ADMIN_EMAIL': 'admin@aquachain.io',
                                'FROM_EMAIL': 'noreply@aquachain.io',
                                'AWS_REGION': 'ap-south-1'
                            }
                        },
                        Tags={
                            'Project': 'AquaChain',
                            'Environment': 'dev'
                        }
                    )
                    print(f"✅ Created Lambda function: {function_name}")
                except lambda_client.exceptions.ResourceConflictException:
                    # Update existing function
                    lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=zip_data.read()
                    )
                    print(f"✅ Updated Lambda function: {function_name}")
        
        # Clean up temp file
        os.unlink(temp_zip.name)
        
        print("🎉 Issues Service deployed successfully!")
        print("🔧 Next steps:")
        print("1. Deploy the API Gateway changes: cdk deploy AquaChain-API-dev")
        print("2. Test the endpoint: POST /api/issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = deploy_issues_service()
    sys.exit(0 if success else 1)