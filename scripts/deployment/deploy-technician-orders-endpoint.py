#!/usr/bin/env python3
"""
Deploy the /api/v1/technician/orders endpoint fix:
1. Updates the technician_service Lambda with the new get_technician_orders function
2. Adds the API Gateway route GET /api/v1/technician/orders
3. Grants the Lambda permission to scan the orders table
"""

import boto3
import zipfile
import json
import os
import sys
from pathlib import Path

REGION = 'ap-south-1'
FUNCTION_NAME = 'aquachain-function-service-request-dev'
ORDERS_TABLE = 'aquachain-orders'

# Files to include in the Lambda package
TECHNICIAN_SERVICE_FILES = [
    'handler.py',
    'service_request_manager.py',
    'assignment_algorithm.py',
    'availability_manager.py',
    'location_service.py',
    'audit_logger.py',
    'cors_utils.py',
    'structured_logger.py',
]

SHARED_FILES = [
    'structured_logger.py',
    'input_validator.py',
    'error_handler.py',
    'errors.py',
]

ZIP_PATH = Path('lambda/technician_service/technician_service_deploy.zip')


def create_package():
    print('📦 Creating deployment package...')
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in TECHNICIAN_SERVICE_FILES:
            filepath = Path('lambda/technician_service') / filename
            if filepath.exists():
                zf.write(filepath, filename)
                print(f'   + technician_service/{filename}')
            else:
                print(f'   - SKIP (not found): {filename}')

        for filename in SHARED_FILES:
            filepath = Path('lambda/shared') / filename
            if filepath.exists():
                zf.write(filepath, filename)
                print(f'   + shared/{filename}')

    print(f'✅ Package created: {ZIP_PATH} ({ZIP_PATH.stat().st_size / 1024:.1f} KB)')
    return ZIP_PATH


def deploy_lambda(zip_path: Path):
    print(f'\n🚀 Deploying Lambda: {FUNCTION_NAME}')
    client = boto3.client('lambda', region_name=REGION)

    with open(zip_path, 'rb') as f:
        zip_bytes = f.read()

    try:
        response = client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=zip_bytes,
            Publish=True
        )
        print(f'✅ Lambda updated: {response["FunctionArn"]}')
        print(f'   Version: {response["Version"]}')

        # Wait for the function update to complete before modifying config
        import time
        print('   Waiting for Lambda update to complete...')
        for _ in range(30):
            state = client.get_function_configuration(FunctionName=FUNCTION_NAME)
            if state.get('LastUpdateStatus') != 'InProgress':
                break
            time.sleep(3)

        # Add ORDERS_TABLE env var if not present
        config = client.get_function_configuration(FunctionName=FUNCTION_NAME)
        env_vars = config.get('Environment', {}).get('Variables', {})
        if 'ORDERS_TABLE' not in env_vars:
            env_vars['ORDERS_TABLE'] = ORDERS_TABLE
            client.update_function_configuration(
                FunctionName=FUNCTION_NAME,
                Environment={'Variables': env_vars}
            )
            print(f'✅ Added ORDERS_TABLE={ORDERS_TABLE} env var')
        else:
            print(f'   ORDERS_TABLE already set to {env_vars["ORDERS_TABLE"]}')

        return response['FunctionArn']
    except client.exceptions.ResourceNotFoundException:
        print(f'❌ Lambda function not found: {FUNCTION_NAME}')
        print('   Check the function name and region.')
        sys.exit(1)


def add_api_gateway_route(lambda_arn: str):
    """Add GET /api/v1/technician/orders route to API Gateway"""
    print('\n🔗 Adding API Gateway route...')
    apigw = boto3.client('apigateway', region_name=REGION)
    iam_client = boto3.client('iam', region_name=REGION)
    lambda_client = boto3.client('lambda', region_name=REGION)
    sts = boto3.client('sts', region_name=REGION)

    account_id = sts.get_caller_identity()['Account']

    # Find the API
    apis = apigw.get_rest_apis()['items']
    api = next((a for a in apis if 'aquachain' in a['name'].lower() and 'rest' in a['name'].lower()), None)
    if not api:
        # Try broader search
        api = next((a for a in apis if 'aquachain' in a['name'].lower()), None)
    if not api:
        print(f'❌ Could not find AquaChain REST API. Available APIs:')
        for a in apis:
            print(f'   - {a["name"]} ({a["id"]})')
        sys.exit(1)

    api_id = api['id']
    print(f'   Found API: {api["name"]} ({api_id})')

    # Find /api/v1/technician resource
    resources = apigw.get_resources(restApiId=api_id, limit=500)['items']
    resource_map = {r['path']: r for r in resources if 'path' in r}

    technician_resource = resource_map.get('/api/v1/technician')
    if not technician_resource:
        print('❌ Could not find /api/v1/technician resource')
        print('   Available paths:', [r for r in resource_map.keys() if 'technician' in r])
        sys.exit(1)

    technician_resource_id = technician_resource['id']

    # Check if /api/v1/technician/orders already exists
    orders_path = '/api/v1/technician/orders'
    if orders_path in resource_map:
        orders_resource = resource_map[orders_path]
        print(f'   Route {orders_path} already exists (id: {orders_resource["id"]})')
        orders_resource_id = orders_resource['id']
    else:
        # Create the resource
        orders_resource = apigw.create_resource(
            restApiId=api_id,
            parentId=technician_resource_id,
            pathPart='orders'
        )
        orders_resource_id = orders_resource['id']
        print(f'   Created resource: {orders_path} (id: {orders_resource_id})')

    # Check if GET method already exists
    try:
        apigw.get_method(restApiId=api_id, resourceId=orders_resource_id, httpMethod='GET')
        print(f'   GET method already exists on {orders_path}')
    except apigw.exceptions.NotFoundException:
        # Find the Cognito authorizer
        authorizers = apigw.get_authorizers(restApiId=api_id)['items']
        cognito_authorizer = next((a for a in authorizers if a['type'] == 'COGNITO_USER_POOLS'), None)

        method_kwargs = {
            'restApiId': api_id,
            'resourceId': orders_resource_id,
            'httpMethod': 'GET',
            'authorizationType': 'COGNITO_USER_POOLS' if cognito_authorizer else 'NONE',
        }
        if cognito_authorizer:
            method_kwargs['authorizerId'] = cognito_authorizer['id']

        apigw.put_method(**method_kwargs)

        # Add Lambda integration
        lambda_uri = f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        apigw.put_integration(
            restApiId=api_id,
            resourceId=orders_resource_id,
            httpMethod='GET',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=lambda_uri
        )

        # Add method response
        apigw.put_method_response(
            restApiId=api_id,
            resourceId=orders_resource_id,
            httpMethod='GET',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': False,
                'method.response.header.Access-Control-Allow-Headers': False,
                'method.response.header.Access-Control-Allow-Methods': False,
            }
        )

        print(f'   ✅ Added GET method to {orders_path}')

    # Grant Lambda permission for API Gateway to invoke it
    try:
        lambda_client.add_permission(
            FunctionName=FUNCTION_NAME,
            StatementId=f'apigateway-technician-orders-{api_id}',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f'arn:aws:execute-api:{REGION}:{account_id}:{api_id}/*/GET/api/v1/technician/orders'
        )
        print('   ✅ Lambda invoke permission granted')
    except lambda_client.exceptions.ResourceConflictException:
        print('   Lambda invoke permission already exists')

    # Deploy to stage
    stage = 'dev'
    apigw.create_deployment(
        restApiId=api_id,
        stageName=stage,
        description='Add /api/v1/technician/orders endpoint'
    )
    print(f'   ✅ Deployed to stage: {stage}')
    print(f'\n🎉 Route available at:')
    print(f'   GET https://{api_id}.execute-api.{REGION}.amazonaws.com/{stage}/api/v1/technician/orders')


def grant_dynamodb_permissions(lambda_arn: str):
    """Grant the Lambda permission to scan the orders table"""
    print('\n🔐 Granting DynamoDB permissions...')
    iam = boto3.client('iam', region_name=REGION)
    sts = boto3.client('sts', region_name=REGION)

    account_id = sts.get_caller_identity()['Account']

    # Get the Lambda execution role
    lambda_client = boto3.client('lambda', region_name=REGION)
    config = lambda_client.get_function_configuration(FunctionName=FUNCTION_NAME)
    role_arn = config['Role']
    role_name = role_arn.split('/')[-1]

    policy_name = 'AquaChainTechnicianOrdersAccess'
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan"],
                "Resource": [
                    f"arn:aws:dynamodb:{REGION}:{account_id}:table/{ORDERS_TABLE}",
                    f"arn:aws:dynamodb:{REGION}:{account_id}:table/{ORDERS_TABLE}/index/*"
                ]
            }
        ]
    }

    try:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        print(f'   ✅ Inline policy {policy_name} added to role {role_name}')
    except Exception as e:
        print(f'   ⚠️  Could not add IAM policy: {e}')
        print('   You may need to add DynamoDB Scan permission manually.')


if __name__ == '__main__':
    print('🔧 Deploying Technician Orders Endpoint Fix\n')

    zip_path = create_package()
    lambda_arn = deploy_lambda(zip_path)
    grant_dynamodb_permissions(lambda_arn)
    add_api_gateway_route(lambda_arn)

    print('\n✅ Deployment complete!')
    print('\nNext steps:')
    print('1. Test: curl -H "Authorization: Bearer <token>" \\')
    print(f'         https://vtqjfznspc.execute-api.{REGION}.amazonaws.com/dev/api/v1/technician/orders')
    print('2. Refresh the Technician Dashboard - tasks should now appear')
