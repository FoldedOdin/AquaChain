#!/usr/bin/env python3
"""
Deploy Notifications Service
Creates DynamoDB table, deploys Lambda function, and configures API Gateway
"""
import boto3
import json
import zipfile
import os
import sys
from pathlib import Path
from datetime import datetime

# Configuration
REGION = 'ap-south-1'
TABLE_NAME = 'aquachain-notifications'
LAMBDA_FUNCTION_NAME = 'aquachain-notification-api'
STAGE_NAME = 'dev'

# Colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(message):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def create_dynamodb_table():
    """Create DynamoDB table for notifications"""
    print_step("Step 1: Creating DynamoDB Table")
    
    dynamodb = boto3.client('dynamodb', region_name=REGION)
    
    try:
        # Check if table already exists
        try:
            response = dynamodb.describe_table(TableName=TABLE_NAME)
            print_warning(f"Table {TABLE_NAME} already exists")
            return True
        except dynamodb.exceptions.ResourceNotFoundException:
            pass
        
        # Create table
        print(f"Creating table: {TABLE_NAME}")
        response = dynamodb.create_table(
            TableName=TABLE_NAME,
            AttributeDefinitions=[
                {'AttributeName': 'notificationId', 'AttributeType': 'S'},
                {'AttributeName': 'userId', 'AttributeType': 'S'},
                {'AttributeName': 'createdAt', 'AttributeType': 'S'}
            ],
            KeySchema=[
                {'AttributeName': 'notificationId', 'KeyType': 'HASH'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'userId-createdAt-index',
                    'KeySchema': [
                        {'AttributeName': 'userId', 'KeyType': 'HASH'},
                        {'AttributeName': 'createdAt', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
            StreamSpecification={
                'StreamEnabled': False
            },
            SSESpecification={
                'Enabled': True,
                'SSEType': 'KMS'
            },
            Tags=[
                {'Key': 'Project', 'Value': 'AquaChain'},
                {'Key': 'Service', 'Value': 'Notifications'},
                {'Key': 'Environment', 'Value': 'dev'}
            ]
        )
        
        print("Waiting for table to be created...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        
        print_success(f"Table {TABLE_NAME} created successfully")
        return True
        
    except Exception as e:
        print_error(f"Failed to create table: {e}")
        return False

def create_lambda_deployment_package():
    """Create Lambda deployment package"""
    print_step("Step 2: Creating Lambda Deployment Package")
    
    lambda_dir = Path('lambda/notification_service')
    if not lambda_dir.exists():
        print_error(f"Lambda directory not found: {lambda_dir}")
        return None
    
    zip_path = Path('lambda/notification_service/function.zip')
    
    try:
        print("Creating deployment package...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add Python files
            for py_file in lambda_dir.glob('*.py'):
                if py_file.name != 'test_handler.py':  # Exclude test files
                    zipf.write(py_file, py_file.name)
                    print(f"  Added: {py_file.name}")
            
            # Add shared utilities if they exist
            shared_dir = lambda_dir / 'shared'
            if shared_dir.exists():
                for py_file in shared_dir.glob('*.py'):
                    zipf.write(py_file, f"shared/{py_file.name}")
                    print(f"  Added: shared/{py_file.name}")
        
        print_success(f"Deployment package created: {zip_path}")
        return zip_path
        
    except Exception as e:
        print_error(f"Failed to create deployment package: {e}")
        return None

def deploy_lambda_function(zip_path):
    """Deploy or update Lambda function"""
    print_step("Step 3: Deploying Lambda Function")
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    iam_client = boto3.client('iam', region_name=REGION)
    
    try:
        # Get or create IAM role
        role_name = 'aquachain-notification-lambda-role'
        role_arn = None
        
        try:
            role = iam_client.get_role(RoleName=role_name)
            role_arn = role['Role']['Arn']
            print(f"Using existing IAM role: {role_name}")
        except iam_client.exceptions.NoSuchEntityException:
            print(f"Creating IAM role: {role_name}")
            
            # Create role
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }
            
            role = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description='Role for AquaChain notification Lambda function'
            )
            role_arn = role['Role']['Arn']
            
            # Attach policies
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            # Create inline policy for DynamoDB access
            dynamodb_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    "Resource": [
                        f"arn:aws:dynamodb:{REGION}:*:table/{TABLE_NAME}",
                        f"arn:aws:dynamodb:{REGION}:*:table/{TABLE_NAME}/index/*"
                    ]
                }]
            }
            
            iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName='DynamoDBAccess',
                PolicyDocument=json.dumps(dynamodb_policy)
            )
            
            print("Waiting for IAM role to propagate...")
            import time
            time.sleep(10)
        
        # Read deployment package
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        # Check if function exists
        function_exists = False
        try:
            lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
            function_exists = True
        except lambda_client.exceptions.ResourceNotFoundException:
            pass
        
        if function_exists:
            print(f"Updating existing function: {LAMBDA_FUNCTION_NAME}")
            
            # Wait for any in-progress updates to complete
            print("Checking if function is ready for update...")
            import time
            max_wait = 60  # Wait up to 60 seconds
            wait_time = 0
            while wait_time < max_wait:
                try:
                    func_config = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
                    state = func_config['Configuration'].get('State')
                    last_update_status = func_config['Configuration'].get('LastUpdateStatus')
                    
                    if state == 'Active' and last_update_status in ['Successful', 'Failed']:
                        print("Function is ready for update")
                        break
                    
                    print(f"Function state: {state}, status: {last_update_status}. Waiting...")
                    time.sleep(5)
                    wait_time += 5
                except Exception as e:
                    print(f"Error checking function state: {e}")
                    break
            
            # Update function code
            response = lambda_client.update_function_code(
                FunctionName=LAMBDA_FUNCTION_NAME,
                ZipFile=zip_content
            )
            
            # Wait for code update to complete before updating configuration
            print("Waiting for code update to complete...")
            time.sleep(5)
            
            # Update configuration
            lambda_client.update_function_configuration(
                FunctionName=LAMBDA_FUNCTION_NAME,
                Environment={
                    'Variables': {
                        'NOTIFICATIONS_TABLE': TABLE_NAME,
                        'LOG_LEVEL': 'INFO'
                    }
                }
            )
        else:
            print(f"Creating new function: {LAMBDA_FUNCTION_NAME}")
            response = lambda_client.create_function(
                FunctionName=LAMBDA_FUNCTION_NAME,
                Runtime='python3.11',
                Role=role_arn,
                Handler='api_handler.lambda_handler',
                Code={'ZipFile': zip_content},
                Description='AquaChain Notification API Handler',
                Timeout=30,
                MemorySize=512,
                Environment={
                    'Variables': {
                        'NOTIFICATIONS_TABLE': TABLE_NAME,
                        'LOG_LEVEL': 'INFO'
                    }
                },
                Tags={
                    'Project': 'AquaChain',
                    'Service': 'Notifications',
                    'Environment': 'dev'
                }
            )
        
        print_success(f"Lambda function deployed: {LAMBDA_FUNCTION_NAME}")
        return True
        
    except Exception as e:
        print_error(f"Failed to deploy Lambda function: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_api_gateway_id():
    """Get the correct REST API Gateway ID"""
    print("Looking up REST API Gateway...")
    
    # Use REST API Gateway client (v1), not HTTP API Gateway (v2)
    apigateway = boto3.client('apigateway', region_name=REGION)
    
    try:
        # List all REST APIs
        response = apigateway.get_rest_apis()
        
        # Find AquaChain API
        for api in response.get('items', []):
            if 'aquachain' in api.get('name', '').lower():
                api_id = api['id']
                print_success(f"Found REST API Gateway: {api['name']} ({api_id})")
                return api_id
        
        # If not found, ask user
        print_warning("Could not auto-detect REST API Gateway")
        print("\nAvailable REST APIs:")
        for api in response.get('items', []):
            print(f"  - {api['name']}: {api['id']}")
        
        api_id = input("\nEnter REST API Gateway ID: ").strip()
        return api_id
        
    except Exception as e:
        print_error(f"Failed to get REST API Gateway ID: {e}")
        # Fallback: ask user
        api_id = input("\nEnter REST API Gateway ID manually: ").strip()
        return api_id


def configure_api_gateway():
    """Configure REST API Gateway integration"""
    print_step("Step 4: Configuring REST API Gateway")
    
    # Get the correct API ID
    api_id = get_api_gateway_id()
    if not api_id:
        print_error("No REST API Gateway ID provided")
        return False
    
    # Use REST API Gateway client (v1)
    apigateway = boto3.client('apigateway', region_name=REGION)
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    try:
        # Get Lambda function ARN
        lambda_response = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        lambda_arn = lambda_response['Configuration']['FunctionArn']
        account_id = lambda_arn.split(':')[4]
        
        print(f"Lambda ARN: {lambda_arn}")
        print(f"REST API Gateway ID: {api_id}")
        
        # Get all resources
        resources = apigateway.get_resources(restApiId=api_id, limit=500)
        root_id = None
        api_resource_id = None
        notifications_resource_id = None
        
        # Find resources by path
        for resource in resources['items']:
            path = resource.get('path', '')
            if path == '/':
                root_id = resource['id']
            elif path == '/api':
                api_resource_id = resource['id']
            elif path == '/api/notifications':
                notifications_resource_id = resource['id']
        
        if not root_id:
            raise Exception("Could not find root resource")
        
        print(f"Root resource ID: {root_id}")
        
        # /api resource should exist
        if not api_resource_id:
            raise Exception("Could not find /api resource - API Gateway structure unexpected")
        
        print(f"Using existing /api resource: {api_resource_id}")
        
        # /api/notifications resource already exists!
        if notifications_resource_id:
            print(f"Using existing /api/notifications resource: {notifications_resource_id}")
        else:
            # Create /api/notifications resource
            print("Creating /api/notifications resource...")
            notifications_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=api_resource_id,
                pathPart='notifications'
            )
            notifications_resource_id = notifications_resource['id']
            print_success(f"Created /api/notifications resource: {notifications_resource_id}")
        
        # Create GET method
        try:
            print("Creating GET method...")
            authorizer_id = _get_cognito_authorizer_id(apigateway, api_id)
            
            method_params = {
                'restApiId': api_id,
                'resourceId': notifications_resource_id,
                'httpMethod': 'GET',
                'authorizationType': 'COGNITO_USER_POOLS' if authorizer_id else 'NONE'
            }
            
            if authorizer_id:
                method_params['authorizerId'] = authorizer_id
            
            apigateway.put_method(**method_params)
            print_success("Created GET method")
        except apigateway.exceptions.ConflictException:
            print_warning("GET method already exists")
        
        # Create Lambda integration
        try:
            print("Creating Lambda integration...")
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=notifications_resource_id,
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            )
            print_success("Created Lambda integration")
        except apigateway.exceptions.ConflictException:
            print_warning("Integration already exists")
        
        # Grant API Gateway permission to invoke Lambda
        print("Granting API Gateway invoke permission...")
        try:
            lambda_client.add_permission(
                FunctionName=LAMBDA_FUNCTION_NAME,
                StatementId='apigateway-invoke-notifications',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f"arn:aws:execute-api:{REGION}:{account_id}:{api_id}/*/{STAGE_NAME}/api/notifications"
            )
            print_success("Permission granted")
        except lambda_client.exceptions.ResourceConflictException:
            print_warning("Permission already exists")
        
        # Deploy to stage
        print(f"Deploying to {STAGE_NAME} stage...")
        try:
            apigateway.create_deployment(
                restApiId=api_id,
                stageName=STAGE_NAME,
                description='Deploy notifications endpoint'
            )
            print_success(f"Deployed to {STAGE_NAME} stage")
        except Exception as e:
            print_warning(f"Deployment warning: {e}")
        
        print_success("REST API Gateway configured successfully")
        return True
        
    except Exception as e:
        print_error(f"Failed to configure REST API Gateway: {e}")
        import traceback
        traceback.print_exc()
        return False


def _get_cognito_authorizer_id(apigateway, api_id):
    """Get Cognito authorizer ID for the API"""
    try:
        authorizers = apigateway.get_authorizers(restApiId=api_id)
        for authorizer in authorizers.get('items', []):
            if authorizer.get('type') == 'COGNITO_USER_POOLS':
                print(f"Using Cognito authorizer: {authorizer['name']} ({authorizer['id']})")
                return authorizer['id']
        
        print_warning("No Cognito authorizer found, using NONE authorization")
        return None
    except Exception as e:
        print_warning(f"Could not get authorizer: {e}")
        return None

def verify_deployment(api_id=None):
    """Verify the deployment"""
    print_step("Step 5: Verifying Deployment")
    
    try:
        # Check DynamoDB table
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        table = dynamodb.describe_table(TableName=TABLE_NAME)
        print_success(f"✓ DynamoDB table exists: {TABLE_NAME}")
        print(f"  Status: {table['Table']['TableStatus']}")
        
        # Check Lambda function
        lambda_client = boto3.client('lambda', region_name=REGION)
        function = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        print_success(f"✓ Lambda function exists: {LAMBDA_FUNCTION_NAME}")
        print(f"  Runtime: {function['Configuration']['Runtime']}")
        print(f"  Memory: {function['Configuration']['MemorySize']} MB")
        
        # Test endpoint
        print("\n" + "="*60)
        print("Deployment Complete!")
        print("="*60)
        if api_id:
            print(f"\nAPI Endpoint:")
            print(f"  https://{api_id}.execute-api.{REGION}.amazonaws.com/{STAGE_NAME}/api/notifications")
            print(f"\nTest with:")
            print(f"  curl -H 'Authorization: Bearer YOUR_TOKEN' \\")
            print(f"    https://{api_id}.execute-api.{REGION}.amazonaws.com/{STAGE_NAME}/api/notifications")
        
        return True
        
    except Exception as e:
        print_error(f"Verification failed: {e}")
        return False

def main():
    """Main deployment function"""
    print("\n" + "="*60)
    print("AquaChain Notifications Service Deployment")
    print("="*60)
    print(f"Region: {REGION}")
    print(f"Table: {TABLE_NAME}")
    print(f"Lambda: {LAMBDA_FUNCTION_NAME}")
    print("="*60)
    
    # Confirm deployment
    confirm = input("\n⚠️  Deploy notifications service? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Deployment cancelled")
        return
    
    # Execute deployment steps
    success = True
    api_id = None
    
    # Step 1: Create DynamoDB table
    if not create_dynamodb_table():
        success = False
    
    # Step 2: Create deployment package
    if success:
        zip_path = create_lambda_deployment_package()
        if not zip_path:
            success = False
    
    # Step 3: Deploy Lambda function
    if success:
        if not deploy_lambda_function(zip_path):
            success = False
    
    # Step 4: Configure API Gateway
    if success:
        if not configure_api_gateway():
            success = False
    
    # Step 5: Verify deployment
    if success:
        # Try to get API ID for verification
        try:
            apigateway = boto3.client('apigateway', region_name=REGION)
            response = apigateway.get_rest_apis()
            for api in response.get('items', []):
                if 'aquachain' in api.get('name', '').lower():
                    api_id = api['id']
                    break
        except:
            pass
        
        verify_deployment(api_id)
    
    if success:
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}✅ Deployment completed successfully!{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
    else:
        print(f"\n{Colors.RED}{'='*60}{Colors.END}")
        print(f"{Colors.RED}❌ Deployment failed. Check errors above.{Colors.END}")
        print(f"{Colors.RED}{'='*60}{Colors.END}\n")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
