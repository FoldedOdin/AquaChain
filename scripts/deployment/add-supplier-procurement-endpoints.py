#!/usr/bin/env python3
"""
Add /api/suppliers, /api/inventory/reorder-alerts, and /api/procurement/orders
endpoints to API Gateway and update admin_service Lambda code.

Run: python scripts/deployment/add-supplier-procurement-endpoints.py
"""

import boto3
import io
import os
import sys
import zipfile
from pathlib import Path

REGION   = os.environ.get('AWS_REGION', 'ap-south-1')
API_ID   = os.environ.get('AQUACHAIN_API_ID')   # Required: export AQUACHAIN_API_ID=<id>
STAGE    = os.environ.get('AQUACHAIN_STAGE', 'dev')
LAMBDA_PATTERN = 'admin-service'

if not API_ID:
    print("❌ AQUACHAIN_API_ID environment variable is required")
    print("   export AQUACHAIN_API_ID=<your-api-gateway-id>")
    sys.exit(1)

apigw  = boto3.client('apigateway', region_name=REGION)
lam    = boto3.client('lambda',     region_name=REGION)
sts    = boto3.client('sts',        region_name=REGION)

CORS_HEADERS = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-Admin-Password'"
# Restrict CORS to known origins — override via env var for staging/prod
CORS_ORIGIN  = os.environ.get('AQUACHAIN_CORS_ORIGIN', 'https://app.aquachain.example.com')


# ── Helpers ───────────────────────────────────────────────────────────────────

def find_lambda():
    paginator = lam.get_paginator('list_functions')
    for page in paginator.paginate():
        for fn in page['Functions']:
            if LAMBDA_PATTERN in fn['FunctionName'].lower():
                print(f"  Found Lambda: {fn['FunctionName']}")
                return fn['FunctionName']
    return None


def update_lambda_code(name):
    print(f"\n📦 Packaging lambda/admin_service ...")
    src = Path(__file__).parent.parent.parent / 'lambda' / 'admin_service'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in src.rglob('*'):
            if p.is_file() and '__pycache__' not in str(p) and '.pyc' not in str(p):
                zf.write(p, p.relative_to(src))
    buf.seek(0)
    data = buf.read()
    print(f"  Size: {len(data)/1024:.1f} KB")
    lam.update_function_code(FunctionName=name, ZipFile=data, Publish=True)
    lam.get_waiter('function_updated').wait(FunctionName=name)
    print("  ✅ Lambda updated")


def get_lambda_arn(name):
    return lam.get_function(FunctionName=name)['Configuration']['FunctionArn']


def get_authorizer_id():
    for a in apigw.get_authorizers(restApiId=API_ID)['items']:
        if a.get('type') == 'COGNITO_USER_POOLS':
            print(f"  Authorizer: {a['id']} ({a['name']})")
            return a['id']
    return None


def all_resources():
    """Return dict of path → resource_id for the whole API."""
    result = {}
    paginator = apigw.get_paginator('get_resources')
    for page in paginator.paginate(restApiId=API_ID):
        for r in page['items']:
            result[r.get('path', '')] = r['id']
    return result


def get_or_create(parent_id, path_part, existing):
    """Return resource_id for pathPart under parent, creating if needed."""
    # Build expected full path from existing map
    for path, rid in existing.items():
        if path.endswith('/' + path_part):
            # Verify parent matches
            try:
                r = apigw.get_resource(restApiId=API_ID, resourceId=rid)
                if r.get('parentId') == parent_id:
                    print(f"  Exists: {path} → {rid}")
                    return rid
            except Exception:
                pass
    print(f"  Creating /{path_part} ...")
    resp = apigw.create_resource(restApiId=API_ID, parentId=parent_id, pathPart=path_part)
    return resp['id']


def add_options(resource_id, methods='GET,POST,OPTIONS'):
    try:
        apigw.get_method(restApiId=API_ID, resourceId=resource_id, httpMethod='OPTIONS')
        apigw.delete_method(restApiId=API_ID, resourceId=resource_id, httpMethod='OPTIONS')
    except apigw.exceptions.NotFoundException:
        pass

    apigw.put_method(restApiId=API_ID, resourceId=resource_id,
                     httpMethod='OPTIONS', authorizationType='NONE', apiKeyRequired=False)
    apigw.put_integration(restApiId=API_ID, resourceId=resource_id,
                          httpMethod='OPTIONS', type='MOCK',
                          requestTemplates={'application/json': '{"statusCode": 200}'})
    apigw.put_method_response(
        restApiId=API_ID, resourceId=resource_id, httpMethod='OPTIONS', statusCode='200',
        responseParameters={
            'method.response.header.Access-Control-Allow-Headers': False,
            'method.response.header.Access-Control-Allow-Methods': False,
            'method.response.header.Access-Control-Allow-Origin':  False,
        }
    )
    apigw.put_integration_response(
        restApiId=API_ID, resourceId=resource_id, httpMethod='OPTIONS', statusCode='200',
        responseParameters={
            'method.response.header.Access-Control-Allow-Headers': CORS_HEADERS,
            'method.response.header.Access-Control-Allow-Methods': f"'{methods}'",
            'method.response.header.Access-Control-Allow-Origin':  f"'{CORS_ORIGIN}'",
        }
    )
    print(f"  ✅ OPTIONS added (methods: {methods})")


def add_method(resource_id, http_method, lambda_arn, authorizer_id):
    try:
        apigw.get_method(restApiId=API_ID, resourceId=resource_id, httpMethod=http_method)
        apigw.delete_method(restApiId=API_ID, resourceId=resource_id, httpMethod=http_method)
    except apigw.exceptions.NotFoundException:
        pass

    kwargs = dict(
        restApiId=API_ID, resourceId=resource_id, httpMethod=http_method,
        authorizationType='COGNITO_USER_POOLS' if authorizer_id else 'NONE',
        apiKeyRequired=False,
    )
    if authorizer_id:
        kwargs['authorizerId'] = authorizer_id
    apigw.put_method(**kwargs)

    uri = (f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31"
           f"/functions/{lambda_arn}/invocations")
    apigw.put_integration(restApiId=API_ID, resourceId=resource_id,
                          httpMethod=http_method, type='AWS_PROXY',
                          integrationHttpMethod='POST', uri=uri)
    apigw.put_method_response(
        restApiId=API_ID, resourceId=resource_id,
        httpMethod=http_method, statusCode='200',
        responseParameters={'method.response.header.Access-Control-Allow-Origin': False}
    )
    print(f"  ✅ {http_method} added")


def ensure_lambda_permission(function_name, path_suffix, sid_suffix):
    account = sts.get_caller_identity()['Account']
    source_arn = f"arn:aws:execute-api:{REGION}:{account}:{API_ID}/*/*/{path_suffix}"
    sid = f"AllowAPIGW{sid_suffix}"
    try:
        lam.remove_permission(FunctionName=function_name, StatementId=sid)
    except Exception:
        pass
    lam.add_permission(
        FunctionName=function_name, StatementId=sid,
        Action='lambda:InvokeFunction', Principal='apigateway.amazonaws.com',
        SourceArn=source_arn,
    )
    print(f"  ✅ Lambda permission granted for {path_suffix}")


def deploy():
    print("\n🚀 Deploying API Gateway stage ...")
    apigw.create_deployment(restApiId=API_ID, stageName=STAGE,
                            description='Add suppliers/inventory/procurement endpoints')
    print(f"  ✅ Deployed to stage: {STAGE}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Add supplier / inventory / procurement endpoints")
    print("=" * 60)

    # 1. Find Lambda
    print("\n🔍 Finding admin_service Lambda ...")
    fn_name = find_lambda()
    if not fn_name:
        print("❌ admin_service Lambda not found"); sys.exit(1)

    # 2. Update Lambda code (picks up new routing in handler.py)
    update_lambda_code(fn_name)
    lambda_arn   = get_lambda_arn(fn_name)
    authorizer_id = get_authorizer_id()

    # 3. Map existing resources
    print("\n🔍 Mapping API Gateway resources ...")
    existing = all_resources()
    api_id   = existing.get('/api')
    if not api_id:
        print("❌ /api resource not found"); sys.exit(1)
    print(f"  /api → {api_id}")

    # ── /api/suppliers ────────────────────────────────────────────────────────
    print("\n🔧 /api/suppliers")
    sup_id = get_or_create(api_id, 'suppliers', existing)
    add_options(sup_id, 'GET,POST,OPTIONS')
    add_method(sup_id, 'GET',  lambda_arn, authorizer_id)
    add_method(sup_id, 'POST', lambda_arn, authorizer_id)
    ensure_lambda_permission(fn_name, 'api/suppliers', 'Suppliers')

    # /api/suppliers/{supplierId}
    sup_item_id = get_or_create(sup_id, '{supplierId}', existing)
    add_options(sup_item_id, 'GET,PUT,OPTIONS')
    add_method(sup_item_id, 'GET', lambda_arn, authorizer_id)
    add_method(sup_item_id, 'PUT', lambda_arn, authorizer_id)

    # /api/suppliers/{supplierId}/performance
    sup_perf_id = get_or_create(sup_item_id, 'performance', existing)
    add_options(sup_perf_id, 'GET,OPTIONS')
    add_method(sup_perf_id, 'GET', lambda_arn, authorizer_id)

    # /api/suppliers/{supplierId}/contracts
    sup_contracts_id = get_or_create(sup_item_id, 'contracts', existing)
    add_options(sup_contracts_id, 'GET,OPTIONS')
    add_method(sup_contracts_id, 'GET', lambda_arn, authorizer_id)

    # ── /api/inventory/reorder-alerts ─────────────────────────────────────────
    print("\n🔧 /api/inventory/reorder-alerts")
    inv_id = existing.get('/api/inventory') or get_or_create(api_id, 'inventory', existing)
    print(f"  /api/inventory → {inv_id}")
    reorder_id = get_or_create(inv_id, 'reorder-alerts', existing)
    add_options(reorder_id, 'GET,OPTIONS')
    add_method(reorder_id, 'GET', lambda_arn, authorizer_id)
    ensure_lambda_permission(fn_name, 'api/inventory/reorder-alerts', 'ReorderAlerts')

    # ── /api/procurement/orders ───────────────────────────────────────────────
    print("\n🔧 /api/procurement/orders")
    proc_id = get_or_create(api_id, 'procurement', existing)
    orders_id = get_or_create(proc_id, 'orders', existing)
    add_options(orders_id, 'GET,POST,OPTIONS')
    add_method(orders_id, 'GET',  lambda_arn, authorizer_id)
    add_method(orders_id, 'POST', lambda_arn, authorizer_id)
    ensure_lambda_permission(fn_name, 'api/procurement/orders', 'ProcurementOrders')

    # /api/procurement/orders/{orderId}
    order_item_id = get_or_create(orders_id, '{orderId}', existing)
    for action in ('approve', 'reject'):
        action_id = get_or_create(order_item_id, action, existing)
        add_options(action_id, 'POST,OPTIONS')
        add_method(action_id, 'POST', lambda_arn, authorizer_id)

    # 4. Deploy
    deploy()

    base = f"https://{API_ID}.execute-api.{REGION}.amazonaws.com/{STAGE}"
    print("\n" + "=" * 60)
    print("✅ Done! New endpoints:")
    print(f"  GET  {base}/api/suppliers")
    print(f"  GET  {base}/api/suppliers/{{id}}/performance")
    print(f"  GET  {base}/api/inventory/reorder-alerts")
    print(f"  GET  {base}/api/procurement/orders")
    print("=" * 60)


if __name__ == '__main__':
    main()
