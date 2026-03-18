#!/usr/bin/env python3
"""
Directly invoke the Lambda with a simulated technician orders request
to capture the actual error causing the 500.
"""
import boto3
import json
from datetime import datetime, timedelta, timezone
import time

REGION = 'ap-south-1'
FUNCTION_NAME = 'aquachain-function-service-request-dev'

lambda_client = boto3.client('lambda', region_name=REGION)
logs_client = boto3.client('logs', region_name=REGION)

# Simulate the API Gateway event for GET /api/v1/technician/orders
test_event = {
    "httpMethod": "GET",
    "resource": "/api/v1/technician/orders",
    "path": "/api/v1/technician/orders",
    "pathParameters": None,
    "queryStringParameters": None,
    "headers": {
        "Authorization": "Bearer test-token"
    },
    "requestContext": {
        "authorizer": {
            "claims": {
                "sub": "test-technician-id",
                "email": "tech@test.com",
                "cognito:groups": "technicians"
            }
        }
    },
    "body": None
}

print(f"Invoking {FUNCTION_NAME} with GET /api/v1/technician/orders...")
response = lambda_client.invoke(
    FunctionName=FUNCTION_NAME,
    InvocationType='RequestResponse',
    LogType='Tail',
    Payload=json.dumps(test_event)
)

import base64
log_result = base64.b64decode(response.get('LogResult', '')).decode('utf-8')
payload = json.loads(response['Payload'].read())

print(f"\nStatus Code: {payload.get('statusCode')}")
print(f"Response body: {payload.get('body', '')[:2000]}")
print(f"\n--- Lambda Logs ---")
print(log_result)

# Also check for new log streams
print("\n--- Checking for new log streams ---")
time.sleep(3)
group = f'/aws/lambda/{FUNCTION_NAME}'
streams = logs_client.describe_log_streams(
    logGroupName=group,
    orderBy='LastEventTime',
    descending=True,
    limit=3
)['logStreams']

for s in streams:
    last = s.get('lastEventTimestamp', 0)
    dt = datetime.fromtimestamp(last / 1000, tz=timezone.utc)
    print(f"  {dt.isoformat()} - {s['logStreamName']}")
