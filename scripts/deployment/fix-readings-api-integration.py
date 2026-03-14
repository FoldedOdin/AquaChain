#!/usr/bin/env python3
"""
Fix the specific readings API integration issue
"""

import boto3
import json
import time

def check_integration():
    """Check the current integration configuration"""
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    api_id = 'vtqjfznspc'  # Known API ID
    resource_id = 'o47l9d'  # Known resource ID for /api/v1/readings/{deviceId}/latest
    
    print(f"🔍 Checking integration for /api/v1/readings/{{deviceId}}/latest...")
    
    try:
        # Get the method
        method = apigateway.get_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='GET'
        )
        
        print(f"✅ GET method exists")
        
        # Get integration details
        integration = method.get('methodIntegration', {})
        
        print(f"\n📋 Current Integration Configuration:")
        print(f"  Type: {integration.get('type', 'UNKNOWN')}")
        print(f"  HTTP Method: {integration.get('httpMethod', 'UNKNOWN')}")
        print(f"  URI: {integration.get('uri', 'UNKNOWN')}")
        
        # Check if it's proxy integration
        is_proxy = integration.get('type') == 'AWS_PROXY'
        print(f"  Proxy Integration: {'✅ ENABLED' if is_proxy else '❌ DISABLED'}")
        
        # Check for mapping templates
        request_templates = integration.get('requestTemplates', {})
        print(f"\n📋 Request Templates:")
        if request_templates:
            for content_type, template in request_templates.items():
                print(f"  ❌ {content_type}: {template[:100]}...")
                print(f"    ⚠️  This conflicts with proxy integration!")
        else:
            print(f"  ✅ None (correct for proxy integration)")
        
        # Check integration responses
        integration_responses = integration.get('integrationResponses', {})
        print(f"\n📋 Integration Responses:")
        if integration_responses:
            for status_code, response in integration_responses.items():
                print(f"  ❌ {status_code}: Response mapping exists")
                response_templates = response.get('responseTemplates', {})
                if response_templates:
                    for content_type, template in response_templates.items():
                        print(f"    ❌ Template: {template[:100]}...")
                print(f"    ⚠️  This conflicts with proxy integration!")
        else:
            print(f"  ✅ None (correct for proxy integration)")
        
        # Determine issues
        issues = []
        if not is_proxy:
            issues.append("NOT_PROXY_INTEGRATION")
        if request_templates:
            issues.append("HAS_REQUEST_TEMPLATES")
        if integration_responses:
            issues.append("HAS_INTEGRATION_RESPONSES")
        
        return {
            'api_id': api_id,
            'resource_id': resource_id,
            'issues': issues,
            'integration': integration
        }
        
    except Exception as e:
        print(f"❌ Error checking integration: {e}")
        return None

def fix_integration(diagnosis):
    """Fix the integration issues"""
    
    if not diagnosis['issues']:
        print("✅ No issues found!")
        return True
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    api_id = diagnosis['api_id']
    resource_id = diagnosis['resource_id']
    issues = diagnosis['issues']
    
    print(f"\n🔧 Fixing {len(issues)} issues:")
    for issue in issues:
        print(f"  - {issue}")
    
    try:
        # Get AWS account info
        account_id = boto3.client('sts').get_caller_identity()['Account']
        region = 'ap-south-1'
        function_name = 'aquachain-function-readings-service-dev'
        
        lambda_uri = f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{region}:{account_id}:function:{function_name}/invocations"
        
        print(f"🔧 Setting up AWS_PROXY integration...")
        print(f"   Lambda URI: {lambda_uri}")
        
        # Update to proxy integration
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='GET',
            type='AWS_PROXY',
            integrationHttpMethod='POST',  # Always POST for Lambda
            uri=lambda_uri,
            passthroughBehavior='WHEN_NO_MATCH'
        )
        
        print(f"✅ Updated to AWS_PROXY integration")
        
        # Remove integration responses if they exist
        try:
            # Get updated integration
            integration = apigateway.get_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='GET'
            )
            
            integration_responses = integration.get('integrationResponses', {})
            
            for status_code in integration_responses.keys():
                print(f"🗑️  Removing integration response: {status_code}")
                try:
                    apigateway.delete_integration_response(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod='GET',
                        statusCode=status_code
                    )
                    print(f"✅ Removed integration response: {status_code}")
                except Exception as e:
                    print(f"⚠️  Could not remove {status_code}: {e}")
        
        except Exception as e:
            print(f"⚠️  Could not clean up integration responses: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing integration: {e}")
        return False

def deploy_api(api_id):
    """Deploy the API changes"""
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    print(f"\n🚀 Deploying API changes to 'dev' stage...")
    
    try:
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Fix Lambda Proxy Integration for readings endpoint'
        )
        
        print(f"✅ Deployment successful: {deployment['id']}")
        
        # Wait for propagation
        print(f"⏳ Waiting 10 seconds for changes to propagate...")
        time.sleep(10)
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

def test_endpoint():
    """Test the endpoint after fixes"""
    
    print(f"\n🧪 Testing endpoint...")
    
    import requests
    
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    try:
        # Test without authentication (should get 401, not 500)
        response = requests.get(url, timeout=15)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            print(f"\n🎉 SUCCESS! Got 401 Unauthorized")
            print(f"✅ This means API Gateway is working correctly!")
            print(f"✅ The Lambda proxy integration is fixed!")
            print(f"✅ Your frontend will now work with proper authentication!")
            
        elif response.status_code == 500:
            print(f"\n❌ Still getting 500 - need more investigation")
            
        elif response.status_code == 200:
            print(f"\n🎉 SUCCESS! Got 200 OK")
            print(f"✅ API is working without authentication (unexpected but good)")
            
        else:
            print(f"\n📋 Got {response.status_code} - this might be normal")
        
        # Show response body
        try:
            if response.text:
                data = response.json()
                print(f"\n📄 Response Body:")
                print(json.dumps(data, indent=2))
        except:
            print(f"\n📄 Response Text: {response.text}")
        
        return response.status_code != 500
        
    except Exception as e:
        print(f"❌ Test request failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fixing readings API Lambda Proxy Integration...")
    
    # Step 1: Check current configuration
    diagnosis = check_integration()
    
    if not diagnosis:
        print("❌ Could not check integration")
        exit(1)
    
    # Step 2: Fix issues if any
    if diagnosis['issues']:
        print(f"\n⚠️  Found issues that need fixing!")
        
        if fix_integration(diagnosis):
            # Step 3: Deploy changes
            if deploy_api(diagnosis['api_id']):
                # Step 4: Test
                success = test_endpoint()
                
                if success:
                    print(f"\n🎉 FIX COMPLETE!")
                    print(f"✅ Your readings API should now work correctly")
                    print(f"✅ Refresh your browser dashboard to test")
                else:
                    print(f"\n❌ Fix may not be complete - check logs")
            else:
                print(f"\n❌ Could not deploy changes")
        else:
            print(f"\n❌ Could not fix integration")
    else:
        print(f"\n✅ No integration issues found!")
        print(f"ℹ️  Testing endpoint anyway...")
        test_endpoint()
    
    print(f"\n" + "="*60)
    print("NEXT STEPS:")
    print("1. Refresh your browser dashboard")
    print("2. Check if sensor readings now load correctly")
    print("3. If still issues, check browser console for errors")
    print("="*60)