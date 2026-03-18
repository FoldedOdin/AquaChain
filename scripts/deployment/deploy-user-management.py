#!/usr/bin/env python3
"""
Deploy user management Lambda with profile 500 fixes:
- Removed hard crash on missing Cognito env vars
- Fixed error handler class mismatch (errors.py vs error_handler.py)
- Fixed Decimal serialization in cors_utils
- Fixed duplicate has_nested_profile + profile map init
- Fixed audit_logger.log_data_access AttributeError
"""

import boto3
import zipfile
import os
import shutil
from pathlib import Path

FUNCTION_NAME = 'aquachain-function-user-management-dev'
LAMBDA_DIR = Path('lambda/user_management')
ZIP_PATH = LAMBDA_DIR / 'user_management_deploy.zip'

FILES_TO_PACKAGE = [
    'handler.py',
    'cors_utils.py',
    'error_handler.py',
    'errors.py',
    'audit_logger.py',
    'cache_service.py',
    'structured_logger.py',
    'user_utils.py',
    'profile_update_simple.py',
]


def create_package():
    print('📦 Creating deployment package...')
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in FILES_TO_PACKAGE:
            filepath = LAMBDA_DIR / filename
            if filepath.exists():
                zf.write(filepath, filename)
                print(f'   + {filename}')
            else:
                print(f'   - SKIP (not found): {filename}')

    size_kb = ZIP_PATH.stat().st_size / 1024
    print(f'   ✅ Package ready: {ZIP_PATH} ({size_kb:.1f} KB)')


def deploy():
    print(f'\n🚀 Deploying to {FUNCTION_NAME}...')
    client = boto3.client('lambda', region_name='ap-south-1')

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
    client = boto3.client('lambda', region_name='ap-south-1')
    try:
        resp = client.get_function_configuration(FunctionName=FUNCTION_NAME)
        print(f'   State: {resp.get("State")}')
        print(f'   Last update: {resp.get("LastModified")}')
        env_vars = resp.get('Environment', {}).get('Variables', {})
        cognito_pool = env_vars.get('COGNITO_USER_POOL_ID', '⚠️  NOT SET')
        cognito_client = env_vars.get('COGNITO_CLIENT_ID', '⚠️  NOT SET')
        users_table = env_vars.get('USERS_TABLE', '⚠️  NOT SET (will default to AquaChain-Users)')
        print(f'   COGNITO_USER_POOL_ID: {cognito_pool}')
        print(f'   COGNITO_CLIENT_ID:    {cognito_client}')
        print(f'   USERS_TABLE:          {users_table}')
        return True
    except Exception as e:
        print(f'   ❌ Verify failed: {e}')
        return False


def cleanup():
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    print('\n🧹 Cleaned up zip')


if __name__ == '__main__':
    print('=' * 55)
    print('Deploy: user-management Lambda (profile 500 fix)')
    print('=' * 55)

    if not LAMBDA_DIR.exists():
        print('❌ Run from project root')
        raise SystemExit(1)

    create_package()
    ok = deploy()
    verify()
    cleanup()

    if ok:
        print('\n✅ Done. Test: GET /api/profile/update')
    else:
        raise SystemExit(1)
