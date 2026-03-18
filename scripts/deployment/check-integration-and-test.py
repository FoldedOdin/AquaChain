#!/usr/bin/env python3
"""Check the GET integration URI and test the endpoint via API Gateway test invoke"""
import boto3
import json

REGION = 'ap-south-1'
API_ID = 'vtqjfznspc'
STAGE = 'dev'

apigw = boto3.client('apigateway', region_name=REGION)

resources = apigw.get_resources(restApiId=API_ID, limit=500)['items']
for r in resources:
    if r.get('path') == '/api/v1/technician/orders':
        rid = r['id']
        integration = apigw.get_integration(
            restApiId=API_ID,
            resourceId=rid,
            httpMethod='GET'
        )
        uri = integration.get('uri', '')
        print(f"Full integration URI:\n  {uri}")
        print(f"Integration type: {integration.get('type')}")
        print(f"Integration HTTP method: {integration.get('httpMethod')}")
        break

# Test invoke via API Gateway test console
print("\nTest invoking via API Gateway test...")
try:
    result = apigw.test_invoke_method(
        restApiId=API_ID,
        resourceId=rid,
        httpMethod='GET',
        headers={'Authorization': 'Bearer test'},
        pathWithQueryString='/api/v1/technician/orders'
    )
    print(f"Status: {result.get('status')}")
    print(f"Body: {result.get('body', '')[:500]}")
    print(f"Log:\n{result.get('log', '')[-2000:]}")
except Exception as e:
    print(f"Test invoke error: {e}")
