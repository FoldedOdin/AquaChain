#!/usr/bin/env python3
"""
Check and fix CORS for /api/shipments endpoint.
Same issue as /api/v1/technician/orders - missing OPTIONS method.
"""
import boto3
import json

REGION = 'ap-south-1'
API_ID = 'vtqjfznspc'
STAGE = 'dev'

apigw = boto3.client('apigateway', region_name=REGION)

# Get all resources
resources = apigw.get_resources(restApiId=API_ID, limit=500)['items']
resource_map = {r.get('path', ''): r for r in resources}

# Find all shipment-related paths
shipment_paths = {p: r for p, r in resource_map.items() if 'shipment' in p.lower()}
print("Shipment-related paths:")
for path, r in shipment_paths.items():
    methods = list(r.get('resourceMethods', {}).keys())
    print(f"  {path} -> methods: {methods}")

# Fix OPTIONS on each shipment resource that's missing it
fixed = []
for path, resource in shipment_paths.items():
    rid = resource['id']
    methods = list(resource.get('resourceMethods', {}).keys())
    
    if 'OPTIONS' not in methods:
        print(f"\nAdding OPTIONS to {path}...")
        
        apigw.put_method(
            restApiId=API_ID,
            resourceId=rid,
            httpMethod='OPTIONS',
            authorizationType='NONE',
            apiKeyRequired=False
        )
        
        apigw.put_integration(
            restApiId=API_ID,
            resourceId=rid,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={'application/json': '{"statusCode": 200}'}
        )
        
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
        
        # Determine allowed methods for this resource
        allowed_methods = ','.join(sorted(set(methods + ['OPTIONS'])))
        
        apigw.put_integration_response(
            restApiId=API_ID,
            resourceId=rid,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With'",
                'method.response.header.Access-Control-Allow-Methods': f"'{allowed_methods}'",
                'method.response.header.Access-Control-Allow-Origin': "'*'",
            },
            responseTemplates={'application/json': ''}
        )
        
        print(f"  Added OPTIONS to {path} (allowed: {allowed_methods})")
        fixed.append(path)
    else:
        print(f"\n  {path} already has OPTIONS")

if fixed:
    print(f"\nDeploying to {STAGE}...")
    apigw.create_deployment(
        restApiId=API_ID,
        stageName=STAGE,
        description=f'Fix CORS OPTIONS for shipment endpoints: {", ".join(fixed)}'
    )
    print("Deployed.")
else:
    print("\nNo changes needed.")
