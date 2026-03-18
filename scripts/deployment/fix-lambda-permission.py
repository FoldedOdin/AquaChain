#!/usr/bin/env python3
"""
Fix Lambda invoke permission for API Gateway.
The source ARN must match what API Gateway actually uses when invoking.
"""
import boto3
import json

REGION = 'ap-south-1'
FUNCTION_NAME = 'aquachain-function-service-request-dev'
API_ID = 'vtqjfznspc'
STAGE = 'dev'

lambda_client = boto3.client('lambda', region_name=REGION)
sts = boto3.client('sts', region_name=REGION)
apigw = boto3.client('apigateway', region_name=REGION)

account_id = sts.get_caller_identity()['Account']

# Show current policy
print("Current Lambda resource policy:")
try:
    policy = lambda_client.get_policy(FunctionName=FUNCTION_NAME)
    doc = json.loads(policy['Policy'])
    for stmt in doc.get('Statement', []):
        print(f"  SID: {stmt.get('Sid')}")
        print(f"  Principal: {stmt.get('Principal')}")
        print(f"  Condition: {stmt.get('Condition')}")
        print()
except lambda_client.exceptions.ResourceNotFoundException:
    print("  No policy found")

# The correct source ARN pattern for API Gateway invoking Lambda:
# arn:aws:execute-api:{region}:{account}:{api-id}/{stage}/{method}/{resource-path}
# For a wildcard that covers all methods/stages:
# arn:aws:execute-api:{region}:{account}:{api-id}/*

# Remove old specific permission and add a wildcard one
old_sid = f'apigateway-technician-orders-{API_ID}'
try:
    lambda_client.remove_permission(
        FunctionName=FUNCTION_NAME,
        StatementId=old_sid
    )
    print(f"Removed old permission: {old_sid}")
except lambda_client.exceptions.ResourceNotFoundException:
    print(f"Old permission {old_sid} not found (already removed or never added)")

# Add wildcard permission covering all API Gateway invocations for this API
new_sid = f'apigateway-{API_ID}-all'
try:
    lambda_client.remove_permission(
        FunctionName=FUNCTION_NAME,
        StatementId=new_sid
    )
    print(f"Removed existing wildcard permission: {new_sid}")
except lambda_client.exceptions.ResourceNotFoundException:
    pass

lambda_client.add_permission(
    FunctionName=FUNCTION_NAME,
    StatementId=new_sid,
    Action='lambda:InvokeFunction',
    Principal='apigateway.amazonaws.com',
    SourceArn=f'arn:aws:execute-api:{REGION}:{account_id}:{API_ID}/*'
)
print(f"Added wildcard permission: arn:aws:execute-api:{REGION}:{account_id}:{API_ID}/*")

# Verify
print("\nUpdated Lambda resource policy:")
policy = lambda_client.get_policy(FunctionName=FUNCTION_NAME)
doc = json.loads(policy['Policy'])
for stmt in doc.get('Statement', []):
    print(f"  SID: {stmt.get('Sid')}")
    cond = stmt.get('Condition', {})
    arn_like = cond.get('ArnLike', {})
    print(f"  SourceArn: {arn_like.get('AWS:SourceArn', 'N/A')}")
    print()

# Test invoke via API Gateway URL using boto3 (simulate what APIGW does)
print("Testing the route exists in API Gateway...")
resources = apigw.get_resources(restApiId=API_ID, limit=500)['items']
for r in resources:
    if r.get('path') == '/api/v1/technician/orders':
        methods = list(r.get('resourceMethods', {}).keys())
        print(f"  /api/v1/technician/orders - methods: {methods}")
        
        # Check integration for GET
        if 'GET' in methods:
            try:
                integration = apigw.get_integration(
                    restApiId=API_ID,
                    resourceId=r['id'],
                    httpMethod='GET'
                )
                print(f"  GET integration type: {integration.get('type')}")
                print(f"  GET integration URI: {integration.get('uri', '')[:80]}")
            except Exception as e:
                print(f"  Could not get GET integration: {e}")
        break
