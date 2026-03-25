#!/usr/bin/env python3
"""Debug: show exact API Gateway state for alert resources"""
import boto3, json

API_ID = 'vtqjfznspc'
REGION = 'ap-south-1'

client = boto3.client('apigateway', region_name=REGION)

# List all resources
resources = client.get_resources(restApiId=API_ID, limit=500)
alert_resources = [r for r in resources['items'] if 'alert' in r['path'].lower()]
alert_resources.sort(key=lambda x: x['path'])

print("=== Alert resources in API Gateway ===")
for r in alert_resources:
    methods = list(r.get('resourceMethods', {}).keys())
    print(f"  {r['id']:12s}  {r['path']:65s}  {methods}")

# For the acknowledge resource specifically, show full method detail
print("\n=== OPTIONS method detail on /api/alerts/{alertId}/acknowledge ===")
ack_resource = next((r for r in alert_resources if r['path'].endswith('/acknowledge')), None)
if ack_resource:
    rid = ack_resource['id']
    try:
        m = client.get_method(restApiId=API_ID, resourceId=rid, httpMethod='OPTIONS')
        print(json.dumps(m, indent=2, default=str))
    except Exception as e:
        print(f"  No OPTIONS method: {e}")

    # Check integration response
    try:
        ir = client.get_integration_response(
            restApiId=API_ID, resourceId=rid, httpMethod='OPTIONS', statusCode='200'
        )
        print("\n=== OPTIONS integration response ===")
        print(json.dumps(ir, indent=2, default=str))
    except Exception as e:
        print(f"  No integration response: {e}")
else:
    print("  /acknowledge resource not found!")

# Check gateway responses (these affect 403 before Lambda runs)
print("\n=== Gateway Responses (affect pre-Lambda 4xx) ===")
try:
    grs = client.get_gateway_responses(restApiId=API_ID)
    for gr in grs['items']:
        if gr.get('responseType') in ('DEFAULT_4XX', 'DEFAULT_5XX', 'UNAUTHORIZED', 'ACCESS_DENIED', 'MISSING_AUTHENTICATION_TOKEN'):
            print(f"  {gr['responseType']:40s}  headers={gr.get('responseParameters', {})}")
except Exception as e:
    print(f"  Error: {e}")

# Check current stage
print("\n=== Current stage deployment ===")
try:
    stage = client.get_stage(restApiId=API_ID, stageName='dev')
    print(f"  Last deployed: {stage.get('lastUpdatedDate')}")
    print(f"  Deployment ID: {stage.get('deploymentId')}")
except Exception as e:
    print(f"  Error: {e}")
