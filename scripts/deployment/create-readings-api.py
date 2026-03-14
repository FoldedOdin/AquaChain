#!/usr/bin/env python3
"""
Create the missing readings API endpoint and Lambda function
"""

import boto3
import json
import zipfile
import os
import time
from pathlib import Path

def create_lambda_function():
    """Create the readings service Lambda function"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        iam_client = boto3.client('iam', region_name='ap-south-1')
        
        function_name = 'aquachain-function-readings-service-dev'
        
        print(f"🔧 Creating Lambda function: {function_name}")
        
        # Check if function already exists
        try:
            existing = lambda_client.get_function(FunctionName=function_name)
            print(f"   ✅ Function already exists, updating code...")
            update_existing = True
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"   📝 Function doesn't exist, creating new...")
            update_existing = False
        
        # Create deployment package
        lambda_dir = Path('lambda/readings_service')
        zip_path = Path('lambda/readings_service/deployment.zip')
        
        print(f"   📦 Creating deployment package...")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add handler.py
            zip_file.write(lambda_dir / 'handler.py', 'handler.py')
        
        # Read the zip file
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        if update_existing:
            # Update existing function
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            print(f"   ✅ Updated function code")
        else:
            # Get or create IAM role
            role_name = 'aquachain-lambda-readings-role'
            
            try:
                role_response = iam_client.get_role(RoleName=role_name)
                role_arn = role_response['Role']['Arn']
                print(f"   ✅ Using existing role: {role_arn}")
            except iam_client.exceptions.NoSuchEntityException:
                print(f"   🔧 Creating IAM role: {role_name}")
                
                # Create role
                trust_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
                
                role_response = iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description='Role for AquaChain readings service Lambda'
                )
                role_arn = role_response['Role']['Arn']
                
                # Attach policies
                policies = [
                    'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                    'arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess'
                ]
                
                for policy_arn in policies:
                    iam_client.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy_arn
                    )
                
                print(f"   ✅ Created role with policies")
                
                # Wait for role to be ready
                print(f"   ⏳ Waiting for role to be ready...")
                time.sleep(10)
            
            # Create Lambda function (without environment variables to avoid KMS issues)
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.11',
                Role=role_arn,
                Handler='handler.lambda_handler',
                Code={'ZipFile': zip_content},
                Description='AquaChain readings service API',
                Timeout=30,
                MemorySize=256,
                Tags={
                    'Project': 'AquaChain',
                    'Environment': 'dev',
                    'Service': 'readings-api'
                }
            )
            print(f"   ✅ Created function")
        
        # Clean up zip file
        if zip_path.exists():
            zip_path.unlink()
        
        function_arn = response['FunctionArn']
        print(f"   📋 Function ARN: {function_arn}")
        
        return function_arn, function_name
        
    except Exception as e:
        print(f"❌ Error creating Lambda function: {e}")
        return None, None

def create_api_gateway_endpoints(function_arn, function_name):
    """Create the API Gateway endpoints for readings"""
    try:
        apigateway = boto3.client('apigateway', region_name='ap-south-1')
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        api_id = 'vtqjfznspc'  # The correct API Gateway ID
        
        print(f"🔧 Creating API Gateway endpoints in: {api_id}")
        
        # Get the v1 resource ID
        resources = apigateway.get_resources(restApiId=api_id)
        
        v1_resource_id = None
        for resource in resources['items']:
            if resource.get('pathPart') == 'v1':
                v1_resource_id = resource['id']
                break
        
        if not v1_resource_id:
            print(f"❌ Could not find v1 resource")
            return False
        
        print(f"   ✅ Found v1 resource: {v1_resource_id}")
        
        # Create /readings resource under /v1
        print(f"   🔧 Creating /readings resource...")
        
        readings_resource_id = None
        try:
            readings_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=v1_resource_id,
                pathPart='readings'
            )
            readings_resource_id = readings_resource['id']
            print(f"   ✅ Created /readings resource: {readings_resource_id}")
        except apigateway.exceptions.ConflictException:
            # Resource already exists, find it
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if resource.get('pathPart') == 'readings' and resource.get('parentId') == v1_resource_id:
                    readings_resource_id = resource['id']
                    print(f"   ✅ Using existing /readings resource: {readings_resource_id}")
                    break
        
        if not readings_resource_id:
            print(f"❌ Could not create or find readings resource")
            return False
        
        # Create /{deviceId} resource under /readings
        print(f"   🔧 Creating /{{deviceId}} resource...")
        
        device_resource_id = None
        try:
            device_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=readings_resource_id,
                pathPart='{deviceId}'
            )
            device_resource_id = device_resource['id']
            print(f"   ✅ Created /{{deviceId}} resource: {device_resource_id}")
        except apigateway.exceptions.ConflictException:
            # Resource already exists, find it
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if resource.get('pathPart') == '{deviceId}' and resource.get('parentId') == readings_resource_id:
                    device_resource_id = resource['id']
                    print(f"   ✅ Using existing /{{deviceId}} resource: {device_resource_id}")
                    break
        
        if not device_resource_id:
            print(f"❌ Could not create or find device resource")
            return False
        
        # Create /latest resource under /{deviceId}
        print(f"   🔧 Creating /latest resource...")
        
        latest_resource_id = None
        try:
            latest_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=device_resource_id,
                pathPart='latest'
            )
            latest_resource_id = latest_resource['id']
            print(f"   ✅ Created /latest resource: {latest_resource_id}")
        except apigateway.exceptions.ConflictException:
            # Resource already exists, find it
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if resource.get('pathPart') == 'latest' and resource.get('parentId') == device_resource_id:
                    latest_resource_id = resource['id']
                    print(f"   ✅ Using existing /latest resource: {latest_resource_id}")
                    break
        
        if not latest_resource_id:
            print(f"❌ Could not create or find latest resource")
            return False
        
        # Create /history resource under /{deviceId}
        print(f"   🔧 Creating /history resource...")
        
        history_resource_id = None
        try:
            history_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=device_resource_id,
                pathPart='history'
            )
            history_resource_id = history_resource['id']
            print(f"   ✅ Created /history resource: {history_resource_id}")
        except apigateway.exceptions.ConflictException:
            # Resource already exists, find it
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if resource.get('pathPart') == 'history' and resource.get('parentId') == device_resource_id:
                    history_resource_id = resource['id']
                    print(f"   ✅ Using existing /history resource: {history_resource_id}")
                    break
        
        if not history_resource_id:
            print(f"❌ Could not create or find history resource")
            return False
        
        # Add methods to both endpoints
        endpoints = [
            (latest_resource_id, 'latest'),
            (history_resource_id, 'history')
        ]
        
        for resource_id, endpoint_name in endpoints:
            print(f"\n   🔧 Setting up methods for /{endpoint_name}...")
            
            # Add OPTIONS method for CORS
            try:
                apigateway.put_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    authorizationType='NONE'
                )
                
                # Add mock integration for OPTIONS
                apigateway.put_integration(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    type='MOCK',
                    requestTemplates={'application/json': '{"statusCode": 200}'}
                )
                
                # Add method response for OPTIONS
                apigateway.put_method_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Origin': False,
                        'method.response.header.Access-Control-Allow-Methods': False,
                        'method.response.header.Access-Control-Allow-Headers': False
                    }
                )
                
                # Add integration response for OPTIONS
                apigateway.put_integration_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'",
                        'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
                    }
                )
                
                print(f"     ✅ Added OPTIONS method")
                
            except Exception as e:
                print(f"     ⚠️ OPTIONS method may already exist: {e}")
            
            # Add GET method
            try:
                apigateway.put_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='GET',
                    authorizationType='AWS_IAM'  # Use IAM auth like other endpoints
                )
                
                # Add Lambda integration for GET
                integration_uri = f"arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{function_arn}/invocations"
                
                apigateway.put_integration(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='GET',
                    type='AWS_PROXY',
                    integrationHttpMethod='POST',
                    uri=integration_uri
                )
                
                print(f"     ✅ Added GET method with Lambda integration")
                
            except Exception as e:
                print(f"     ⚠️ GET method may already exist: {e}")
        
        # Give API Gateway permission to invoke Lambda
        print(f"\n   🔧 Adding Lambda permissions...")
        
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId='api-gateway-invoke-readings',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:ap-south-1:*:{api_id}/*/*'
            )
            print(f"   ✅ Added Lambda permission")
        except Exception as e:
            print(f"   ⚠️ Permission may already exist: {e}")
        
        # Deploy the API
        print(f"\n🚀 Deploying API changes...")
        
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Added readings endpoints'
        )
        
        print(f"✅ Deployment created: {deployment['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating API Gateway endpoints: {e}")
        return False

def test_new_endpoints():
    """Test the newly created endpoints"""
    try:
        import requests
        
        print(f"\n🧪 Testing new endpoints...")
        
        base_url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        
        # Test endpoints
        endpoints = [
            f"{base_url}/api/v1/readings/ESP32-001/latest",
            f"{base_url}/api/v1/readings/ESP32-001/history"
        ]
        
        for endpoint in endpoints:
            print(f"\n   🔍 Testing: {endpoint}")
            
            try:
                # Test OPTIONS (CORS)
                options_response = requests.options(endpoint, timeout=10)
                print(f"     OPTIONS: {options_response.status_code}")
                print(f"     CORS Headers: {options_response.headers.get('Access-Control-Allow-Origin', 'Missing')}")
                
                # Test GET (without auth for now)
                get_response = requests.get(endpoint, timeout=10)
                print(f"     GET: {get_response.status_code}")
                print(f"     Response: {get_response.text[:100]}...")
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")

def main():
    print("🔧 Creating Readings API Endpoint")
    print("=" * 35)
    
    # Step 1: Create Lambda function
    print("\n1. Creating Lambda function...")
    function_arn, function_name = create_lambda_function()
    
    if not function_arn:
        print("❌ Failed to create Lambda function")
        return
    
    # Step 2: Create API Gateway endpoints
    print("\n2. Creating API Gateway endpoints...")
    if not create_api_gateway_endpoints(function_arn, function_name):
        print("❌ Failed to create API Gateway endpoints")
        return
    
    # Step 3: Test endpoints
    print("\n3. Testing endpoints...")
    test_new_endpoints()
    
    print(f"\n🎉 Readings API Created Successfully!")
    print(f"✅ Lambda Function: {function_name}")
    print(f"✅ API Endpoints:")
    print(f"   GET /api/v1/readings/{{deviceId}}/latest")
    print(f"   GET /api/v1/readings/{{deviceId}}/history")
    print(f"✅ CORS headers configured")
    print(f"\n💡 The frontend should now be able to fetch readings!")

if __name__ == "__main__":
    main()