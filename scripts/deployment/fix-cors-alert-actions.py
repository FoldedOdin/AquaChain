#!/usr/bin/env python3
"""
Fix CORS for /api/alerts/{alertId}/acknowledge and /api/alerts/{alertId}/mute
Creates the missing API Gateway resources, adds OPTIONS + PUT methods, and deploys.
"""

import boto3
import json
import sys

API_ID    = 'vtqjfznspc'
REGION    = 'ap-south-1'
STAGE     = 'dev'

# Sub-paths to create under /api/alerts/{alertId}
ACTION_PATHS = ['acknowledge', 'mute', 'resolve']

CORS_HEADERS = {
    'method.response.header.Access-Control-Allow-Headers': (
        "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    ),
    'method.response.header.Access-Control-Allow-Methods': "'GET,PUT,OPTIONS'",
    'method.response.header.Access-Control-Allow-Origin':  "'*'",
}


def get_resources(client):
    """Return all resources as a dict keyed by path."""
    paginator_result = client.get_resources(restApiId=API_ID, limit=500)
    return {r['path']: r for r in paginator_result['items']}


def ensure_resource(client, parent_id, path_part, existing_by_path, full_path):
    """Create resource if it doesn't exist; return its id."""
    if full_path in existing_by_path:
        rid = existing_by_path[full_path]['id']
        print(f"  ✅ Resource already exists: {full_path} ({rid})")
        return rid

    resp = client.create_resource(
        restApiId=API_ID,
        parentId=parent_id,
        pathPart=path_part,
    )
    rid = resp['id']
    print(f"  ✨ Created resource: {full_path} ({rid})")
    return rid


def add_options(client, resource_id, path):
    """Add OPTIONS mock method for CORS preflight."""
    try:
        client.get_method(restApiId=API_ID, resourceId=resource_id, httpMethod='OPTIONS')
        print(f"  ✅ OPTIONS already exists on {path}")
        return
    except client.exceptions.NotFoundException:
        pass

    client.put_method(
        restApiId=API_ID, resourceId=resource_id,
        httpMethod='OPTIONS', authorizationType='NONE',
    )
    client.put_integration(
        restApiId=API_ID, resourceId=resource_id,
        httpMethod='OPTIONS', type='MOCK',
        requestTemplates={'application/json': '{"statusCode": 200}'},
    )
    client.put_method_response(
        restApiId=API_ID, resourceId=resource_id,
        httpMethod='OPTIONS', statusCode='200',
        responseParameters={k: False for k in CORS_HEADERS},
    )
    client.put_integration_response(
        restApiId=API_ID, resourceId=resource_id,
        httpMethod='OPTIONS', statusCode='200',
        responseParameters=CORS_HEADERS,
        responseTemplates={'application/json': ''},
    )
    print(f"  ✨ Added OPTIONS to {path}")


def add_put(client, resource_id, path, lambda_arn, authorizer_id):
    """Add PUT method with Lambda proxy integration and Cognito auth."""
    try:
        client.get_method(restApiId=API_ID, resourceId=resource_id, httpMethod='PUT')
        print(f"  ✅ PUT already exists on {path}")
        return
    except client.exceptions.NotFoundException:
        pass

    uri = (
        f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/"
        f"{lambda_arn}/invocations"
    )

    client.put_method(
        restApiId=API_ID, resourceId=resource_id,
        httpMethod='PUT',
        authorizationType='COGNITO_USER_POOLS',
        authorizerId=authorizer_id,
        apiKeyRequired=False,
    )
    client.put_integration(
        restApiId=API_ID, resourceId=resource_id,
        httpMethod='PUT', type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=uri,
    )
    client.put_method_response(
        restApiId=API_ID, resourceId=resource_id,
        httpMethod='PUT', statusCode='200',
        responseParameters={
            'method.response.header.Access-Control-Allow-Origin': False,
        },
    )
    print(f"  ✨ Added PUT to {path}")


def ensure_lambda_permission(lambda_client, function_name):
    """Ensure API Gateway can invoke the Lambda (wildcard source ARN)."""
    statement_id = 'AllowAPIGatewayAlertActions'
    try:
        policy = lambda_client.get_policy(FunctionName=function_name)
        if statement_id in policy['Policy']:
            print(f"  ✅ Lambda invoke permission already exists")
            return
    except lambda_client.exceptions.ResourceNotFoundException:
        pass
    except Exception:
        pass  # policy may not exist yet

    sts = boto3.client('sts', region_name=REGION)
    account_id = sts.get_caller_identity()['Account']

    lambda_client.add_permission(
        FunctionName=function_name,
        StatementId=statement_id,
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f'arn:aws:execute-api:{REGION}:{account_id}:{API_ID}/*/*',
    )
    print(f"  ✨ Added Lambda invoke permission")


def main():
    print("🔧 Fixing CORS for alert action endpoints...\n")

    client        = boto3.client('apigateway', region_name=REGION)
    lambda_client = boto3.client('lambda',     region_name=REGION)

    # ── 1. Discover existing resources ──────────────────────────────────────
    by_path = get_resources(client)

    # ── 2. Find /api/alerts ──────────────────────────────────────────────────
    if '/api/alerts' not in by_path:
        print("❌ /api/alerts resource not found — run fix-cors-alerts-endpoint.py first")
        sys.exit(1)
    alerts_id = by_path['/api/alerts']['id']
    print(f"📍 /api/alerts → {alerts_id}")

    # ── 3. Ensure /api/alerts/{alertId} ─────────────────────────────────────
    alert_id_path = '/api/alerts/{alertId}'
    alert_id_rid  = ensure_resource(client, alerts_id, '{alertId}', by_path, alert_id_path)
    # Refresh after potential creation
    by_path = get_resources(client)

    # ── 4. Find the alert_detection Lambda ARN ───────────────────────────────
    lf = lambda_client.list_functions()
    alert_fn = next(
        (f for f in lf['Functions'] if 'alert' in f['FunctionName'].lower() and 'detection' in f['FunctionName'].lower()),
        None
    )
    if not alert_fn:
        # Fallback: any function with 'alert' in name
        alert_fn = next(
            (f for f in lf['Functions'] if 'alert' in f['FunctionName'].lower()),
            None
        )
    if not alert_fn:
        print("❌ Could not find alert_detection Lambda function")
        sys.exit(1)
    lambda_arn = alert_fn['FunctionArn']
    print(f"📍 Lambda: {alert_fn['FunctionName']}")

    # ── 5. Find Cognito authorizer ───────────────────────────────────────────
    authorizers = client.get_authorizers(restApiId=API_ID)['items']
    cognito_auth = next(
        (a for a in authorizers if a.get('type') == 'COGNITO_USER_POOLS'),
        None
    )
    if not cognito_auth:
        print("❌ No Cognito authorizer found")
        sys.exit(1)
    authorizer_id = cognito_auth['id']
    print(f"📍 Cognito authorizer: {authorizer_id}\n")

    # ── 6. Ensure Lambda invoke permission ───────────────────────────────────
    ensure_lambda_permission(lambda_client, alert_fn['FunctionName'])

    # ── 7. Add OPTIONS + PUT for each action path ────────────────────────────
    for action in ACTION_PATHS:
        full_path = f'{alert_id_path}/{action}'
        print(f"\n🔨 {full_path}")
        action_rid = ensure_resource(client, alert_id_rid, action, by_path, full_path)
        add_options(client, action_rid, full_path)
        add_put(client, action_rid, full_path, lambda_arn, authorizer_id)

    # ── 8. Also ensure OPTIONS on {alertId} itself ───────────────────────────
    print(f"\n🔨 {alert_id_path}")
    add_options(client, alert_id_rid, alert_id_path)

    # ── 9. Deploy ────────────────────────────────────────────────────────────
    print(f"\n🚀 Deploying to stage '{STAGE}'...")
    client.create_deployment(
        restApiId=API_ID,
        stageName=STAGE,
        description='Add CORS + PUT for alert acknowledge/mute/resolve endpoints',
    )
    print("✅ Deployed!\n")
    print("Endpoints now available:")
    for action in ACTION_PATHS:
        print(f"  PUT  https://{API_ID}.execute-api.{REGION}.amazonaws.com/{STAGE}/api/alerts/{{alertId}}/{action}")
    print("\nDone.")


if __name__ == '__main__':
    main()
