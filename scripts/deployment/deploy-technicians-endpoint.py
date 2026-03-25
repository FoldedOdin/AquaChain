#!/usr/bin/env python3
"""
Deploy /api/technicians endpoint directly via boto3.
- Updates admin_service Lambda with latest code
- Creates /api/technicians GET route in API Gateway with CORS
- No full CDK deploy required
"""

import boto3
import json
import os
import sys
import zipfile
import io
import subprocess
from pathlib import Path

REGION = 'ap-south-1'
API_ID = 'vtqjfznspc'
STAGE = 'dev'
LAMBDA_NAME_PATTERN = 'admin-service'  # partial match

apigw = boto3.client('apigateway', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)


def find_lambda_function():
    """Find the admin service Lambda function name."""
    paginator = lambda_client.get_paginator('list_functions')
    for page in paginator.paginate():
        for fn in page['Functions']:
            if LAMBDA_NAME_PATTERN in fn['FunctionName'].lower():
                print(f"  Found Lambda: {fn['FunctionName']}")
                return fn['FunctionName']
    return None


def update_lambda_code(function_name):
    """Zip and upload the admin_service Lambda code."""
    print(f"\n📦 Packaging admin_service Lambda...")
    lambda_dir = Path(__file__).parent.parent.parent / 'lambda' / 'admin_service'

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fpath in lambda_dir.rglob('*'):
            if fpath.is_file() and '__pycache__' not in str(fpath) and '.pyc' not in str(fpath):
                arcname = fpath.relative_to(lambda_dir)
                zf.write(fpath, arcname)
    buf.seek(0)
    zip_bytes = buf.read()
    print(f"  Package size: {len(zip_bytes) / 1024:.1f} KB")

    print(f"  Uploading to Lambda: {function_name}")
    lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_bytes,
        Publish=True
    )
    # Wait for update to complete
    waiter = lambda_client.get_waiter('function_updated')
    waiter.wait(FunctionName=function_name)
    print(f"  ✅ Lambda code updated")


def get_api_root_resource():
    """Get the /api resource ID."""
    resources = apigw.get_resources(restApiId=API_ID, limit=500)
    for r in resources['items']:
        if r.get('path') == '/api':
            return r['id']
    raise RuntimeError("Could not find /api resource in API Gateway")


def get_or_create_technicians_resource(api_resource_id):
    """Get or create /api/technicians resource."""
    resources = apigw.get_resources(restApiId=API_ID, limit=500)
    for r in resources['items']:
        if r.get('pathPart') == 'technicians' and r.get('parentId') == api_resource_id:
            print(f"  /api/technicians resource already exists: {r['id']}")
            return r['id']

    print("  Creating /api/technicians resource...")
    resp = apigw.create_resource(
        restApiId=API_ID,
        parentId=api_resource_id,
        pathPart='technicians'
    )
    resource_id = resp['id']
    print(f"  Created resource: {resource_id}")
    return resource_id


def get_lambda_arn(function_name):
    fn = lambda_client.get_function(FunctionName=function_name)
    return fn['Configuration']['FunctionArn']


def add_get_method(resource_id, lambda_arn):
    """Add GET method with Cognito authorizer."""
    # Find Cognito authorizer
    authorizers = apigw.get_authorizers(restApiId=API_ID)
    authorizer_id = None
    for a in authorizers['items']:
        if a.get('type') == 'COGNITO_USER_POOLS':
            authorizer_id = a['id']
            print(f"  Using Cognito authorizer: {authorizer_id} ({a['name']})")
            break

    # Check if GET already exists
    try:
        apigw.get_method(restApiId=API_ID, resourceId=resource_id, httpMethod='GET')
        print("  GET method already exists, deleting to recreate...")
        apigw.delete_method(restApiId=API_ID, resourceId=resource_id, httpMethod='GET')
    except apigw.exceptions.NotFoundException:
        pass

    print("  Creating GET method...")
    method_kwargs = dict(
        restApiId=API_ID,
        resourceId=resource_id,
        httpMethod='GET',
        authorizationType='COGNITO_USER_POOLS' if authorizer_id else 'NONE',
        apiKeyRequired=False,
    )
    if authorizer_id:
        method_kwargs['authorizerId'] = authorizer_id

    apigw.put_method(**method_kwargs)

    # Lambda proxy integration
    region = REGION
    account_id = boto3.client('sts').get_caller_identity()['Account']
    uri = f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"

    apigw.put_integration(
        restApiId=API_ID,
        resourceId=resource_id,
        httpMethod='GET',
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=uri,
    )

    # Method response
    apigw.put_method_response(
        restApiId=API_ID,
        resourceId=resource_id,
        httpMethod='GET',
        statusCode='200',
        responseParameters={
            'method.response.header.Access-Control-Allow-Origin': False,
        }
    )
    print("  ✅ GET method created")


def add_options_method(resource_id):
    """Add OPTIONS method for CORS preflight."""
    try:
        apigw.get_method(restApiId=API_ID, resourceId=resource_id, httpMethod='OPTIONS')
        print("  OPTIONS method already exists, deleting to recreate...")
        apigw.delete_method(restApiId=API_ID, resourceId=resource_id, httpMethod='OPTIONS')
    except apigw.exceptions.NotFoundException:
        pass

    print("  Creating OPTIONS method for CORS...")
    apigw.put_method(
        restApiId=API_ID,
        resourceId=resource_id,
        httpMethod='OPTIONS',
        authorizationType='NONE',
        apiKeyRequired=False,
    )

    apigw.put_integration(
        restApiId=API_ID,
        resourceId=resource_id,
        httpMethod='OPTIONS',
        type='MOCK',
        requestTemplates={'application/json': '{"statusCode": 200}'},
    )

    apigw.put_method_response(
        restApiId=API_ID,
        resourceId=resource_id,
        httpMethod='OPTIONS',
        statusCode='200',
        responseParameters={
            'method.response.header.Access-Control-Allow-Headers': False,
            'method.response.header.Access-Control-Allow-Methods': False,
            'method.response.header.Access-Control-Allow-Origin': False,
        }
    )

    apigw.put_integration_response(
        restApiId=API_ID,
        resourceId=resource_id,
        httpMethod='OPTIONS',
        statusCode='200',
        responseParameters={
            'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
            'method.response.header.Access-Control-Allow-Methods': "'GET,OPTIONS'",
            'method.response.header.Access-Control-Allow-Origin': "'*'",
        }
    )
    print("  ✅ OPTIONS method created")


def add_lambda_permission(function_name):
    """Grant API Gateway permission to invoke the Lambda."""
    account_id = boto3.client('sts').get_caller_identity()['Account']
    source_arn = f"arn:aws:execute-api:{REGION}:{account_id}:{API_ID}/*/*/technicians"
    statement_id = "AllowAPIGatewayTechnicians"

    try:
        lambda_client.remove_permission(FunctionName=function_name, StatementId=statement_id)
    except Exception:
        pass

    lambda_client.add_permission(
        FunctionName=function_name,
        StatementId=statement_id,
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=source_arn,
    )
    print("  ✅ Lambda invoke permission granted")


def deploy_api():
    """Deploy the API Gateway stage."""
    print("\n🚀 Deploying API Gateway stage...")
    apigw.create_deployment(
        restApiId=API_ID,
        stageName=STAGE,
        description='Added /api/technicians endpoint'
    )
    print(f"  ✅ Deployed to stage: {STAGE}")


def main():
    print("=" * 55)
    print("  Deploy /api/technicians endpoint")
    print("=" * 55)

    # 1. Find Lambda
    print("\n🔍 Finding admin_service Lambda...")
    function_name = find_lambda_function()
    if not function_name:
        print("❌ Could not find admin_service Lambda. Exiting.")
        sys.exit(1)

    # 2. Update Lambda code
    update_lambda_code(function_name)

    # 3. Get Lambda ARN
    lambda_arn = get_lambda_arn(function_name)

    # 4. Get /api resource
    print("\n🔍 Finding /api resource...")
    api_resource_id = get_api_root_resource()
    print(f"  /api resource ID: {api_resource_id}")

    # 5. Get or create /api/technicians
    print("\n🔧 Setting up /api/technicians resource...")
    tech_resource_id = get_or_create_technicians_resource(api_resource_id)

    # 6. Add GET method
    print("\n🔧 Adding GET method...")
    add_get_method(tech_resource_id, lambda_arn)

    # 7. Add OPTIONS for CORS
    print("\n🔧 Adding OPTIONS method (CORS)...")
    add_options_method(tech_resource_id)

    # 8. Lambda permission
    print("\n🔧 Granting Lambda invoke permission...")
    add_lambda_permission(function_name)

    # 9. Deploy
    deploy_api()

    print("\n" + "=" * 55)
    print("✅ Done!")
    print(f"\nEndpoint: GET https://{API_ID}.execute-api.{REGION}.amazonaws.com/{STAGE}/api/technicians")
    print("=" * 55)


if __name__ == '__main__':
    main()
