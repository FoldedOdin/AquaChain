#!/usr/bin/env python3
"""
Fix CORS for /api/v1/technician/orders by adding OPTIONS method with mock integration.
API Gateway's default_cors_preflight_options only applies to CDK-created resources;
manually created resources need OPTIONS added explicitly.
"""

import boto3
import json

REGION = 'ap-south-1'
API_ID = 'vtqjfznspc'
STAGE = 'dev'
ORDERS_PATH = '/api/v1/technician/orders'

apigw = boto3.client('apigateway', region_name=REGION)

# Find the resource
resources = apigw.get_resources(restApiId=API_ID, limit=500)['items']
resource_map = {r.get('path', ''): r for r in resources}

orders_resource = resource_map.get(ORDERS_PATH)
if not orders_resource:
    print(f'ERROR: {ORDERS_PATH} not found')
    print('Technician paths:', [p for p in resource_map if 'technician' in p])
    exit(1)

rid = orders_resource['id']
existing_methods = list(orders_resource.get('resourceMethods', {}).keys())
print(f'Resource id: {rid}')
print(f'Existing methods: {existing_methods}')

# Add OPTIONS method if missing
if 'OPTIONS' in existing_methods:
    print('OPTIONS method already exists')
else:
    print('Adding OPTIONS method...')

    # 1. Create OPTIONS method (no auth needed for preflight)
    apigw.put_method(
        restApiId=API_ID,
        resourceId=rid,
        httpMethod='OPTIONS',
        authorizationType='NONE',
        apiKeyRequired=False
    )

    # 2. Mock integration (standard CORS pattern for API Gateway)
    apigw.put_integration(
        restApiId=API_ID,
        resourceId=rid,
        httpMethod='OPTIONS',
        type='MOCK',
        requestTemplates={'application/json': '{"statusCode": 200}'}
    )

    # 3. Method response with CORS headers
    apigw.put_method_response(
        restApiId=API_ID,
        resourceId=rid,
        httpMethod='OPTIONS',
        statusCode='200',
        responseParameters={
            'method.response.header.Access-Control-Allow-Headers': False,
            'method.response.header.Access-Control-Allow-Methods': False,
            'method.response.header.Access-Control-Allow-Origin': False,
        },
        responseModels={'application/json': 'Empty'}
    )

    # 4. Integration response that sets the actual header values
    apigw.put_integration_response(
        restApiId=API_ID,
        resourceId=rid,
        httpMethod='OPTIONS',
        statusCode='200',
        responseParameters={
            'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With'",
            'method.response.header.Access-Control-Allow-Methods': "'GET,OPTIONS'",
            'method.response.header.Access-Control-Allow-Origin': "'*'",
        },
        responseTemplates={'application/json': ''}
    )

    print('OPTIONS method added successfully')

# Also ensure GET method response has CORS headers
print('Checking GET method response headers...')
try:
    get_method = apigw.get_method(restApiId=API_ID, resourceId=rid, httpMethod='GET')
    method_responses = get_method.get('methodResponses', {})
    response_200 = method_responses.get('200', {})
    response_params = response_200.get('responseParameters', {})

    cors_header = 'method.response.header.Access-Control-Allow-Origin'
    if cors_header not in response_params:
        print('Adding CORS header to GET 200 response...')
        # Need to update the method response to include CORS header
        apigw.update_method_response(
            restApiId=API_ID,
            resourceId=rid,
            httpMethod='GET',
            statusCode='200',
            patchOperations=[
                {
                    'op': 'add',
                    'path': '/responseParameters/method.response.header.Access-Control-Allow-Origin',
                    'value': 'false'
                }
            ]
        )
        print('Added Access-Control-Allow-Origin to GET response')
    else:
        print('GET response already has CORS header')
except Exception as e:
    print(f'Note: Could not update GET method response: {e}')

# Deploy to stage
print(f'\nDeploying to stage: {STAGE}...')
apigw.create_deployment(
    restApiId=API_ID,
    stageName=STAGE,
    description='Fix CORS for /api/v1/technician/orders - add OPTIONS method'
)

print(f'\nDone! CORS preflight should now work for:')
print(f'  OPTIONS https://{API_ID}.execute-api.{REGION}.amazonaws.com/{STAGE}{ORDERS_PATH}')
