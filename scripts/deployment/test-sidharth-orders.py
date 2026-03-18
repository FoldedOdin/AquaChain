#!/usr/bin/env python3
"""Test with Sidharth Lenin's real Cognito sub"""
import boto3
import json
import base64

REGION = 'ap-south-1'
FUNCTION_NAME = 'aquachain-function-service-request-dev'
SIDHARTH_SUB = '31333d7a-7031-703b-2e21-966a49444222'

lambda_client = boto3.client('lambda', region_name=REGION)

test_event = {
    "httpMethod": "GET",
    "resource": "/api/v1/technician/orders",
    "path": "/api/v1/technician/orders",
    "pathParameters": None,
    "queryStringParameters": None,
    "requestContext": {
        "authorizer": {
            "claims": {
                "sub": SIDHARTH_SUB,
                "email": "leninat259@gmail.com",
                "cognito:groups": "technicians",
                "cognito:username": "sidharth"
            }
        }
    },
    "body": None
}

response = lambda_client.invoke(
    FunctionName=FUNCTION_NAME,
    InvocationType='RequestResponse',
    LogType='Tail',
    Payload=json.dumps(test_event)
)

log = base64.b64decode(response.get('LogResult', '')).decode('utf-8')
payload = json.loads(response['Payload'].read())
body = json.loads(payload.get('body', '{}'))

print(f"Status: {payload.get('statusCode')}")
print(f"Orders count: {body.get('count')}")
for o in body.get('orders', []):
    print(f"\n  orderId: {o.get('orderId')}")
    print(f"  status: {o.get('status')}")
    print(f"  assignedTechnician: {o.get('assignedTechnician')}")
    tech = o.get('technicianAssignment', {})
    print(f"  technicianAssignment.technicianName: {tech.get('technicianName')}")

print(f"\nRelevant log lines:")
for line in log.split('\n'):
    if 'Searching' in line or 'Found' in line or 'ERROR' in line or 'error' in line.lower():
        print(f"  {line.strip()}")
