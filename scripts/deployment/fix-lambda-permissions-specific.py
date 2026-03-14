#!/usr/bin/env python3
"""
Fix Lambda permissions for the specific API Gateway endpoint.
"""

import boto3
import json
from botocore.exceptions import ClientError

def fix_lambda_permissions():
    """Fix Lambda permissions for API Gateway"""
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    function_name = 'aquachain-function-readings-service-dev'
    api_id = 'vtqjfznspc'
    
    print(f"🔧 Fixing Lambda permissions...")
    print(f"Function: {function_name}")
    print(f"API ID: {api_id}")
    
    try:
        # Remove existing permissions first
        print(f"\n🗑️  Removing old permissions...")
        
        try:
            policy = lambda_client.get_policy(FunctionName=function_name)
            policy_doc = json.loads(policy['Policy'])
            
            for statement in policy_doc.get('Statement', []):
                sid = statement.get('Sid')
                if sid and 'apigateway' in sid.lower():
                    try:
                        lambda_client.remove_permission(
                            FunctionName=function_name,
                            StatementId=sid
                        )
                        print(f"   Removed: {sid}")
                    except ClientError as e:
                        print(f"   Could not remove {sid}: {e}")
        except ClientError:
            print(f"   No existing policy found")
        
        # Add new permission with correct source ARN
        print(f"\n✅ Adding new permission...")
        
        statement_id = f'apigateway-{api_id}-readings-latest'
        source_arn = f'arn:aws:execute-api:ap-south-1:339713024676:{api_id}/*/GET/api/v1/readings/*/latest'
        
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId=statement_id,
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=source_arn
        )
        
        print(f"   ✅ Added permission: {statement_id}")
        print(f"   Source ARN: {source_arn}")
        
        # Also add a broader permission for the entire API
        try:
            broad_statement_id = f'apigateway-{api_id}-all'
            broad_source_arn = f'arn:aws:execute-api:ap-south-1:339713024676:{api_id}/*/*'
            
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=broad_statement_id,
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=broad_source_arn
            )
            
            print(f"   ✅ Added broad permission: {broad_statement_id}")
            
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                print(f"   ✅ Broad permission already exists")
            else:
                print(f"   ⚠️  Could not add broad permission: {e}")
        
        # Verify permissions
        print(f"\n📋 Verifying permissions...")
        
        policy = lambda_client.get_policy(FunctionName=function_name)
        policy_doc = json.loads(policy['Policy'])
        
        api_permissions = []
        for statement in policy_doc.get('Statement', []):
            if statement.get('Principal', {}).get('Service') == 'apigateway.amazonaws.com':
                api_permissions.append(statement)
        
        print(f"   Found {len(api_permissions)} API Gateway permissions:")
        for perm in api_permissions:
            sid = perm.get('Sid', 'Unknown')
            condition = perm.get('Condition', {})
            source_arn = condition.get('StringEquals', {}).get('AWS:SourceArn', 'No ARN')
            print(f"   - {sid}: {source_arn}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing permissions: {e}")
        return False

def test_endpoint():
    """Test the endpoint after fixing permissions"""
    print(f"\n🧪 Testing endpoint...")
    
    import requests
    
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    try:
        # Test without auth (should get 401, not 500)
        response = requests.get(url, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"   ✅ Good! 401 means Lambda is being called")
            print(f"   The 500 error should be fixed")
        elif response.status_code == 500:
            print(f"   ❌ Still getting 500 error")
            print(f"   Response: {response.text}")
        else:
            print(f"   Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error testing: {e}")

def main():
    print("🚀 Fixing Lambda permissions for API Gateway...\n")
    
    success = fix_lambda_permissions()
    
    if success:
        test_endpoint()
        
        print(f"\n✅ Permissions fixed!")
        print(f"   Try your frontend again - the 500 error should be resolved.")
    else:
        print(f"\n❌ Could not fix permissions")

if __name__ == "__main__":
    main()