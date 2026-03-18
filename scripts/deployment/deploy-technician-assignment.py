#!/usr/bin/env python3
"""
Deploy auto-technician-assignment Lambda with fixes:
- _get_available_technicians() now scans AquaChain-Users (not a non-existent technicians table)
- _mark_technician_busy() now updates AquaChain-Users with correct key (userId)
- _create_service_request_for_assignment() creates record in aquachain-service-requests
  so the technician dashboard can see assigned tasks
Also adds SERVICE_REQUESTS_TABLE env var to the Lambda.
"""

import boto3
import zipfile
import os
from pathlib import Path

FUNCTION_NAME = 'aquachain-function-auto-technician-assignment-dev'
REGION = 'ap-south-1'
ZIP_PATH = Path('lambda/orders/auto_technician_assignment_deploy.zip')

# Files from lambda/orders/
ORDERS_FILES = [
    'auto_technician_assignment.py',
]

# Files from lambda/technician_assignment/
TECHNICIAN_ASSIGNMENT_FILES = [
    'technician_assignment_service.py',
]

# Files from lambda/shared/
SHARED_FILES = [
    'structured_logger.py',
    'input_validator.py',
    'error_handler.py',
    'errors.py',
    'audit_logger.py',
    'cache_service.py',
]


def create_package():
    print('📦 Creating deployment package...')
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in ORDERS_FILES:
            filepath = Path('lambda/orders') / filename
            if filepath.exists():
                zf.write(filepath, filename)
                print(f'   + orders/{filename}')
            else:
                print(f'   - SKIP (not found): orders/{filename}')

        for filename in TECHNICIAN_ASSIGNMENT_FILES:
            filepath = Path('lambda/technician_assignment') / filename
            if filepath.exists():
                zf.write(filepath, filename)
                print(f'   + technician_assignment/{filename}')
            else:
                print(f'   - SKIP (not found): technician_assignment/{filename}')

        for filename in SHARED_FILES:
            filepath = Path('lambda/shared') / filename
            if filepath.exists():
                zf.write(filepath, filename)
                print(f'   + shared/{filename}')
            else:
                print(f'   - SKIP (not found): shared/{filename}')

    size_kb = ZIP_PATH.stat().st_size / 1024
    print(f'   ✅ Package ready: {ZIP_PATH} ({size_kb:.1f} KB)')


def add_env_var():
    """Add SERVICE_REQUESTS_TABLE env var if missing"""
    print('\n🔧 Checking env vars...')
    client = boto3.client('lambda', region_name=REGION)
    config = client.get_function_configuration(FunctionName=FUNCTION_NAME)
    env_vars = config.get('Environment', {}).get('Variables', {})

    if 'SERVICE_REQUESTS_TABLE' not in env_vars:
        env_vars['SERVICE_REQUESTS_TABLE'] = 'aquachain-service-requests'
        client.update_function_configuration(
            FunctionName=FUNCTION_NAME,
            Environment={'Variables': env_vars}
        )
        print('   ✅ Added SERVICE_REQUESTS_TABLE=aquachain-service-requests')
    else:
        print(f'   ✓ SERVICE_REQUESTS_TABLE already set: {env_vars["SERVICE_REQUESTS_TABLE"]}')


def deploy():
    print(f'\n🚀 Deploying to {FUNCTION_NAME}...')
    client = boto3.client('lambda', region_name=REGION)

    with open(ZIP_PATH, 'rb') as f:
        zip_bytes = f.read()

    try:
        resp = client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=zip_bytes,
        )
        print(f'   ✅ Deployed: {resp["FunctionArn"]}')
        print(f'   Last modified: {resp["LastModified"]}')
        return True
    except client.exceptions.ResourceNotFoundException:
        print(f'   ❌ Function not found: {FUNCTION_NAME}')
        return False
    except Exception as e:
        print(f'   ❌ Deploy failed: {e}')
        return False


def verify():
    print('\n🔍 Verifying...')
    client = boto3.client('lambda', region_name=REGION)
    try:
        resp = client.get_function_configuration(FunctionName=FUNCTION_NAME)
        print(f'   State: {resp.get("State")}')
        print(f'   Last update: {resp.get("LastModified")}')
        env_vars = resp.get('Environment', {}).get('Variables', {})
        print(f'   USERS_TABLE:             {env_vars.get("USERS_TABLE", "⚠️  NOT SET")}')
        print(f'   SERVICE_REQUESTS_TABLE:  {env_vars.get("SERVICE_REQUESTS_TABLE", "⚠️  NOT SET")}')
        print(f'   ENHANCED_ORDERS_TABLE:   {env_vars.get("ENHANCED_ORDERS_TABLE", "⚠️  NOT SET")}')
        return True
    except Exception as e:
        print(f'   ❌ Verify failed: {e}')
        return False


def cleanup():
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    print('\n🧹 Cleaned up zip')


if __name__ == '__main__':
    print('=' * 60)
    print('Deploy: auto-technician-assignment Lambda')
    print('=' * 60)

    if not Path('lambda/orders').exists():
        print('❌ Run from project root')
        raise SystemExit(1)

    create_package()
    add_env_var()
    ok = deploy()
    verify()
    cleanup()

    if ok:
        print('\n✅ Done.')
    else:
        raise SystemExit(1)
