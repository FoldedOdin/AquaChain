#!/usr/bin/env python3
"""Final test: invoke Lambda with realistic Cognito claims"""
import boto3
import json

REGION = 'ap-south-1'
FUNCTION_NAME = 'aquachain-function-service-request-dev'

lambda_client = boto3.client('lambda', region_name=REGION)

# Simulate real API Gateway event with Cognito authorizer claims
test_event = {
    "httpMethod": "GET",
    "resource": "/api/v1/technician/orders",
    "path": "/api/v1/technician/orders",
    "pathParameters": None,
    "queryStringParameters": None,
    "requestContext": {
        "authorizer": {
            "claims": {
                "sub": "real-technician-user-id",
                "email": "sidharth@example.com",
                "cognito:groups": "technicians",   # comma-separated string from Cognito authorizer
                "cognito:username": "sidharth"
            }
        }
    },
    "body": None
}

import base64
response = lambda_client.invoke(
    FunctionName=FUNCTION_NAME,
    InvocationType='RequestResponse',
    LogType='Tail',
    Payload=json.dumps(test_event)
)

log = base64.b64decode(response.get('LogResult', '')).decode('utf-8')
payload = json.loads(response['Payload'].read())

print(f"Status: {payload.get('statusCode')}")
body = json.loads(payload.get('body', '{}'))
print(f"Orders count: {body.get('count', 'N/A')}")
print(f"Keys in response: {list(body.keys())}")
print(f"\nLambda log (last lines):")
for line in log.strip().split('\n')[-8:]:
    print(f"  {line}")
