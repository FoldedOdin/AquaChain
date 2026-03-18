#!/usr/bin/env python3
"""
Fix the Lambda integration URI to use $LATEST instead of a pinned version.
The integration was set to :2 (published version) but the permission covers
the unqualified ARN. Easiest fix: update integration to use unqualified ARN.
"""
import boto3
import json

REGION = 'ap-south-1'
API_ID = 'vtqjfznspc'
STAGE = 'dev'
FUNCTION_NAME = 'aquachain-function-service-request-dev'

apigw = boto3.client('apigateway', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
sts = boto3.client('sts', region_name=REGION)

account_id = sts.get_caller_identity()['Account']

# Correct integration URI using unqualified function ARN (no version suffix)
correct_uri = (
    f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/'
    f'arn:aws:lambda:{REGION}:{account_id}:function:{FUNCTION_NAME}/invocations'
)

# Find the orders resource
resources = apigw.get_resources(restApiId=API_ID, limit=500)['items']
orders_resource = next((r for r in resources if r.get('path') == '/api/v1/technician/orders'), None)

if not orders_resource:
    print('ERROR: /api/v1/technician/orders not found')
    exit(1)

rid = orders_resource['id']
print(f'Resource id: {rid}')

# Update the GET integration URI
print(f'Updating integration URI to:\n  {correct_uri}')
apigw.update_integration(
    restApiId=API_ID,
    resourceId=rid,
    httpMethod='GET',
    patchOperations=[
        {
            'op': 'replace',
            'path': '/uri',
            'value': correct_uri
        }
    ]
)
print('Integration URI updated')

# Deploy
print(f'\nDeploying to {STAGE}...')
apigw.create_deployment(
    restApiId=API_ID,
    stageName=STAGE,
    description='Fix integration URI to use unqualified Lambda ARN'
)
print('Deployed')

# Quick test invoke
print('\nTest invoking...')
result = apigw.test_invoke_method(
    restApiId=API_ID,
    resourceId=rid,
    httpMethod='GET',
    headers={'Authorization': 'Bearer test'},
    pathWithQueryString='/api/v1/technician/orders'
)
print(f'Status: {result.get("status")}')
print(f'Body: {result.get("body", "")[:300]}')
if result.get('status') != 200:
    log = result.get('log', '')
    # Show last relevant lines
    lines = [l for l in log.split('\n') if 'error' in l.lower() or 'fail' in l.lower() or 'permission' in l.lower()]
    for l in lines[-5:]:
        print(f'  LOG: {l}')
