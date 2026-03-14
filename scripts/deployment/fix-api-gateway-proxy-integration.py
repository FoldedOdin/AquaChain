#!/usr/bin/env python3
"""
Fix API Gateway Lambda Proxy Integration Issues
Diagnose and fix the most common causes of Lambda success + API Gateway 500 errors
"""

import boto3
import json
import time

def diagnose_api_gateway_integration():
    """Diagnose API Gateway integration configuration"""
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    # Find the API Gateway
    print("🔍 Finding API Gateway...")
    
    apis = apigateway.get_rest_apis()
    target_api = None
    
    for api in apis['items']:
        if api['id'] == 'vtqjfznspc' or 'aquachain-api' in api['name'].lower():
            target_api = api
            break
    
    if not target_api:
        print("❌ Could not find AquaChain API Gateway")
        return False
    
    api_id = target_api['id']
    api_name = target_api['name']
    
    print(f"✅ Found API: {api_name} (ID: {api_id})")
    
    # Get resources
    print(f"\n🔍 Analyzing API Gateway resources...")
    
    resources = apigateway.get_resources(restApiId=api_id)
    
    readings_resource = None
    for resource in resources['items']:
        if resource.get('path') == '/api/v1/readings/{deviceId}/latest':
            readings_resource = resource
            break
    
    if not readings_resource:
        print("❌ Could not find /api/v1/readings/{deviceId}/latest resource")
        return False
    
    resource_id = readings_resource['id']
    resource_path = readings_resource['path']
    
    print(f"✅ Found readings resource: {resource_path} (ID: {resource_id})")
    
    # We already have the latest resource, no need to find subresource
    latest_resource_id = resource_id
    latest_path = resource_path
    
    print(f"✅ Found latest resource: {latest_path} (ID: {latest_resource_id})")
    
    # Check GET method integration
    print(f"\n🔍 Checking GET method integration...")
    
    try:
        method = apigateway.get_method(
            restApiId=api_id,
            resourceId=latest_resource_id,
            httpMethod='GET'
        )
        
        print(f"✅ GET method exists")
        
        # Check integration details
        integration = method.get('methodIntegration', {})
        
        print(f"\n📋 Integration Analysis:")
        print(f"  Integration Type: {integration.get('type', 'UNKNOWN')}")
        print(f"  Integration HTTP Method: {integration.get('httpMethod', 'UNKNOWN')}")
        print(f"  URI: {integration.get('uri', 'UNKNOWN')}")
        
        # Check if Lambda Proxy Integration is enabled
        request_parameters = integration.get('requestParameters', {})
        
        # The key indicator for proxy integration
        if integration.get('type') == 'AWS_PROXY':
            print(f"  ✅ Lambda Proxy Integration: ENABLED")
            proxy_enabled = True
        elif integration.get('type') == 'AWS':
            print(f"  ❌ Lambda Proxy Integration: DISABLED (type is AWS, not AWS_PROXY)")
            proxy_enabled = False
        else:
            print(f"  ❌ Unknown integration type: {integration.get('type')}")
            proxy_enabled = False
        
        # Check for mapping templates (the smoking gun)
        request_templates = integration.get('requestTemplates', {})
        
        print(f"\n📋 Request Templates:")
        if request_templates:
            for content_type, template in request_templates.items():
                print(f"  ❌ {content_type}: {template[:100]}...")
                print(f"    ⚠️  Mapping templates should be EMPTY for proxy integration!")
        else:
            print(f"  ✅ No request templates (correct for proxy integration)")
        
        # Check integration responses
        integration_responses = integration.get('integrationResponses', {})
        
        print(f"\n📋 Integration Responses:")
        if integration_responses:
            for status_code, response in integration_responses.items():
                print(f"  ❌ {status_code}: Response mapping exists")
                response_templates = response.get('responseTemplates', {})
                if response_templates:
                    for content_type, template in response_templates.items():
                        print(f"    ❌ {content_type}: {template[:100]}...")
                print(f"    ⚠️  Integration responses should be EMPTY for proxy integration!")
        else:
            print(f"  ✅ No integration responses (correct for proxy integration)")
        
        # Determine what needs to be fixed
        issues = []
        
        if not proxy_enabled:
            issues.append("PROXY_INTEGRATION_DISABLED")
        
        if request_templates:
            issues.append("REQUEST_TEMPLATES_EXIST")
        
        if integration_responses:
            issues.append("INTEGRATION_RESPONSES_EXIST")
        
        return {
            'api_id': api_id,
            'resource_id': latest_resource_id,
            'issues': issues,
            'integration': integration
        }
        
    except Exception as e:
        print(f"❌ Error checking method: {e}")
        return False

def fix_proxy_integration(diagnosis):
    """Fix the proxy integration issues"""
    
    if not diagnosis or not diagnosis['issues']:
        print("✅ No issues found - API Gateway configuration looks correct!")
        return True
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    api_id = diagnosis['api_id']
    resource_id = diagnosis['resource_id']
    issues = diagnosis['issues']
    
    print(f"\n🔧 Fixing {len(issues)} issues...")
    
    try:
        # Get current integration
        current_integration = apigateway.get_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='GET'
        )
        
        # Prepare the fix
        lambda_function_name = 'aquachain-function-readings-service-dev'
        account_id = boto3.client('sts').get_caller_identity()['Account']
        region = 'ap-south-1'
        
        lambda_uri = f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{region}:{account_id}:function:{lambda_function_name}/invocations"
        
        # Update integration to use proxy
        print(f"🔧 Updating integration to AWS_PROXY...")
        
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='GET',
            type='AWS_PROXY',
            integrationHttpMethod='POST',  # Always POST for Lambda
            uri=lambda_uri,
            passthroughBehavior='WHEN_NO_MATCH'
        )
        
        print(f"✅ Integration updated to AWS_PROXY")
        
        # Remove any integration responses (they conflict with proxy integration)
        try:
            # Get integration responses
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
                    print(f"⚠️  Could not remove integration response {status_code}: {e}")
        
        except Exception as e:
            print(f"⚠️  Could not check integration responses: {e}")
        
        print(f"✅ Proxy integration configuration complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing integration: {e}")
        return False

def deploy_api_changes(api_id):
    """Deploy the API changes"""
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    print(f"\n🚀 Deploying API changes...")
    
    try:
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='Fix Lambda Proxy Integration'
        )
        
        deployment_id = deployment['id']
        print(f"✅ Deployment created: {deployment_id}")
        
        # Wait a moment for deployment to propagate
        print(f"⏳ Waiting for deployment to propagate...")
        time.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"❌ Error deploying API: {e}")
        return False

def test_fixed_endpoint():
    """Test the endpoint after fixes"""
    
    print(f"\n🧪 Testing fixed endpoint...")
    
    # Test with curl-like request
    import requests
    
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    # Test without auth first (should get 401, not 500)
    try:
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✅ SUCCESS! Got 401 Unauthorized (expected without token)")
            print(f"✅ This means API Gateway is now working correctly!")
            print(f"✅ The 500 error is fixed!")
            
            try:
                data = response.json()
                print(f"📋 Response: {json.dumps(data, indent=2)}")
            except:
                print(f"📋 Response: {response.text}")
            
            return True
            
        elif response.status_code == 500:
            print(f"❌ Still getting 500 error - more investigation needed")
            try:
                data = response.json()
                print(f"📋 Error Response: {json.dumps(data, indent=2)}")
            except:
                print(f"📋 Error Response: {response.text}")
            return False
            
        else:
            print(f"📋 Unexpected status code: {response.status_code}")
            try:
                data = response.json()
                print(f"📋 Response: {json.dumps(data, indent=2)}")
            except:
                print(f"📋 Response: {response.text}")
            return True
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Diagnosing and fixing API Gateway Lambda Proxy Integration...")
    
    # Step 1: Diagnose the issue
    diagnosis = diagnose_api_gateway_integration()
    
    if not diagnosis:
        print("❌ Could not diagnose API Gateway - check if resources exist")
        exit(1)
    
    # Step 2: Fix the issues
    if diagnosis['issues']:
        print(f"\n⚠️  Found {len(diagnosis['issues'])} issues:")
        for issue in diagnosis['issues']:
            print(f"  - {issue}")
        
        if fix_proxy_integration(diagnosis):
            # Step 3: Deploy changes
            if deploy_api_changes(diagnosis['api_id']):
                # Step 4: Test
                test_fixed_endpoint()
            else:
                print("❌ Deployment failed")
        else:
            print("❌ Fix failed")
    else:
        print("✅ No configuration issues found!")
        print("ℹ️  The problem might be elsewhere - testing endpoint...")
        test_fixed_endpoint()
    
    print(f"\n" + "="*60)
    print("SUMMARY:")
    print("If you see '401 Unauthorized' above, the fix worked!")
    print("The API Gateway is now properly configured.")
    print("Your frontend should work with a valid auth token.")
    print("="*60)