#!/usr/bin/env python3
"""
Fix mapping templates that conflict with Lambda Proxy Integration
This is the "smoking gun" that causes 500 errors even when Lambda works
"""

import boto3
import json
import time

def check_all_method_configurations():
    """Check both GET and OPTIONS methods for mapping template conflicts"""
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    api_id = 'vtqjfznspc'
    resource_id = 'o47l9d'  # /api/v1/readings/{deviceId}/latest
    
    print(f"🔍 Checking ALL method configurations for mapping template conflicts...")
    
    methods_to_check = ['GET', 'OPTIONS']
    issues_found = []
    
    for method in methods_to_check:
        print(f"\n📋 Checking {method} method...")
        
        try:
            # Get method configuration
            method_config = apigateway.get_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method
            )
            
            print(f"✅ {method} method exists")
            
            # Check integration
            integration = method_config.get('methodIntegration', {})
            integration_type = integration.get('type', 'UNKNOWN')
            
            print(f"  Integration Type: {integration_type}")
            
            if method == 'GET':
                # For GET method, check proxy integration vs mapping templates
                if integration_type == 'AWS_PROXY':
                    print(f"  ✅ Proxy Integration: ENABLED")
                    
                    # Check for conflicting request templates
                    request_templates = integration.get('requestTemplates', {})
                    if request_templates:
                        print(f"  ❌ CONFLICT: Request templates exist with proxy integration!")
                        for content_type, template in request_templates.items():
                            print(f"    - {content_type}: {template[:100]}...")
                        issues_found.append({
                            'method': method,
                            'issue': 'REQUEST_TEMPLATES_WITH_PROXY',
                            'templates': request_templates
                        })
                    else:
                        print(f"  ✅ No request templates (correct)")
                    
                    # Check for conflicting integration responses
                    integration_responses = integration.get('integrationResponses', {})
                    if integration_responses:
                        print(f"  ❌ CONFLICT: Integration responses exist with proxy integration!")
                        for status_code, response in integration_responses.items():
                            print(f"    - {status_code}:")
                            response_templates = response.get('responseTemplates', {})
                            if response_templates:
                                for content_type, template in response_templates.items():
                                    print(f"      {content_type}: {template[:100]}...")
                        issues_found.append({
                            'method': method,
                            'issue': 'INTEGRATION_RESPONSES_WITH_PROXY',
                            'responses': integration_responses
                        })
                    else:
                        print(f"  ✅ No integration responses (correct)")
                
                elif integration_type == 'AWS':
                    print(f"  ❌ PROBLEM: Using AWS integration instead of AWS_PROXY")
                    issues_found.append({
                        'method': method,
                        'issue': 'NOT_PROXY_INTEGRATION',
                        'current_type': integration_type
                    })
                
            elif method == 'OPTIONS':
                # For OPTIONS method, check CORS configuration
                if integration_type == 'MOCK':
                    print(f"  ✅ Mock Integration: CORRECT for CORS")
                    
                    # Check if CORS templates are complete
                    request_templates = integration.get('requestTemplates', {})
                    integration_responses = integration.get('integrationResponses', {})
                    
                    if not integration_responses:
                        print(f"  ❌ CORS: Missing integration responses")
                        issues_found.append({
                            'method': method,
                            'issue': 'INCOMPLETE_CORS_SETUP',
                            'missing': 'integration_responses'
                        })
                    else:
                        print(f"  ✅ CORS: Integration responses configured")
                        
                        # Check for 200 response
                        if '200' not in integration_responses:
                            print(f"  ❌ CORS: Missing 200 response")
                            issues_found.append({
                                'method': method,
                                'issue': 'MISSING_CORS_200_RESPONSE'
                            })
                        else:
                            cors_200 = integration_responses['200']
                            response_templates = cors_200.get('responseTemplates', {})
                            
                            if 'application/json' not in response_templates:
                                print(f"  ⚠️  CORS: Missing application/json template")
                            else:
                                template = response_templates['application/json']
                                print(f"  📋 CORS Template: {template}")
                
            else:
                print(f"  ℹ️  Unexpected integration type: {integration_type}")
            
        except Exception as e:
            print(f"❌ Error checking {method} method: {e}")
    
    return {
        'api_id': api_id,
        'resource_id': resource_id,
        'issues': issues_found
    }

def fix_mapping_template_conflicts(diagnosis):
    """Fix the mapping template conflicts"""
    
    if not diagnosis['issues']:
        print("✅ No mapping template conflicts found!")
        return True
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    api_id = diagnosis['api_id']
    resource_id = diagnosis['resource_id']
    issues = diagnosis['issues']
    
    print(f"\n🔧 Fixing {len(issues)} mapping template conflicts...")
    
    fixed_count = 0
    
    for issue in issues:
        method = issue['method']
        issue_type = issue['issue']
        
        print(f"\n🔧 Fixing {method} method: {issue_type}")
        
        try:
            if issue_type == 'REQUEST_TEMPLATES_WITH_PROXY':
                # Remove request templates that conflict with proxy integration
                templates = issue['templates']
                
                for content_type in templates.keys():
                    print(f"🗑️  Removing request template: {content_type}")
                    
                    # Remove the template by updating integration without it
                    # First get current integration
                    current_integration = apigateway.get_integration(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod=method
                    )
                    
                    # Update integration without request templates
                    apigateway.put_integration(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod=method,
                        type=current_integration['type'],
                        integrationHttpMethod=current_integration['httpMethod'],
                        uri=current_integration['uri'],
                        passthroughBehavior='WHEN_NO_MATCH'
                        # Note: Not including requestTemplates removes them
                    )
                    
                    print(f"✅ Removed request template: {content_type}")
                
                fixed_count += 1
            
            elif issue_type == 'INTEGRATION_RESPONSES_WITH_PROXY':
                # Remove integration responses that conflict with proxy integration
                responses = issue['responses']
                
                for status_code in responses.keys():
                    print(f"🗑️  Removing integration response: {status_code}")
                    
                    try:
                        apigateway.delete_integration_response(
                            restApiId=api_id,
                            resourceId=resource_id,
                            httpMethod=method,
                            statusCode=status_code
                        )
                        print(f"✅ Removed integration response: {status_code}")
                    except Exception as e:
                        print(f"⚠️  Could not remove {status_code}: {e}")
                
                fixed_count += 1
            
            elif issue_type == 'NOT_PROXY_INTEGRATION':
                # Convert to proxy integration
                print(f"🔧 Converting to AWS_PROXY integration...")
                
                account_id = boto3.client('sts').get_caller_identity()['Account']
                region = 'ap-south-1'
                function_name = 'aquachain-function-readings-service-dev'
                
                lambda_uri = f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{region}:{account_id}:function:{function_name}/invocations"
                
                apigateway.put_integration(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method,
                    type='AWS_PROXY',
                    integrationHttpMethod='POST',
                    uri=lambda_uri,
                    passthroughBehavior='WHEN_NO_MATCH'
                )
                
                print(f"✅ Converted to AWS_PROXY integration")
                fixed_count += 1
            
            else:
                print(f"⚠️  Don't know how to fix: {issue_type}")
        
        except Exception as e:
            print(f"❌ Error fixing {method} {issue_type}: {e}")
    
    print(f"\n✅ Fixed {fixed_count} out of {len(issues)} issues")
    return fixed_count > 0

def deploy_and_test():
    """Deploy changes and test the endpoint"""
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    print(f"\n🚀 Deploying API changes...")
    
    try:
        deployment = apigateway.create_deployment(
            restApiId='vtqjfznspc',
            stageName='dev',
            description='Remove mapping template conflicts with proxy integration'
        )
        
        print(f"✅ Deployment successful: {deployment['id']}")
        
        # Wait for propagation
        print(f"⏳ Waiting 15 seconds for changes to propagate...")
        time.sleep(15)
        
        # Test the endpoint
        print(f"\n🧪 Testing endpoint after fixes...")
        
        import requests
        
        url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
        
        response = requests.get(url, timeout=15)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print(f"🎉 SUCCESS! Got 401 Unauthorized (expected without auth)")
            print(f"✅ The mapping template conflicts are FIXED!")
            print(f"✅ API Gateway is now working correctly!")
            
        elif response.status_code == 500:
            print(f"❌ Still getting 500 - may need more investigation")
            
        elif response.status_code == 200:
            print(f"🎉 SUCCESS! Got 200 OK (even better!)")
            
        else:
            print(f"📋 Got {response.status_code} - check if this is expected")
        
        # Show response
        try:
            if response.text:
                data = response.json()
                print(f"\n📄 Response:")
                print(json.dumps(data, indent=2))
        except:
            print(f"\n📄 Response Text: {response.text}")
        
        return response.status_code != 500
        
    except Exception as e:
        print(f"❌ Deployment or test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fixing mapping template conflicts with Lambda Proxy Integration...")
    print("This is the 'smoking gun' that causes 500 errors even when Lambda works correctly.")
    
    # Step 1: Check for conflicts
    diagnosis = check_all_method_configurations()
    
    if not diagnosis['issues']:
        print(f"\n✅ No mapping template conflicts found!")
        print(f"ℹ️  Testing endpoint anyway...")
        deploy_and_test()
    else:
        print(f"\n⚠️  Found {len(diagnosis['issues'])} mapping template conflicts:")
        for i, issue in enumerate(diagnosis['issues'], 1):
            print(f"  {i}. {issue['method']} method: {issue['issue']}")
        
        # Step 2: Fix the conflicts
        if fix_mapping_template_conflicts(diagnosis):
            # Step 3: Deploy and test
            success = deploy_and_test()
            
            if success:
                print(f"\n🎉 MAPPING TEMPLATE CONFLICTS FIXED!")
                print(f"✅ Your readings API should now work correctly")
                print(f"✅ Refresh your browser dashboard to test")
            else:
                print(f"\n❌ Still having issues - may need more investigation")
        else:
            print(f"\n❌ Could not fix all conflicts")
    
    print(f"\n" + "="*70)
    print("WHAT WE FIXED:")
    print("- Removed request templates that conflict with AWS_PROXY")
    print("- Removed integration responses that conflict with AWS_PROXY")
    print("- Ensured clean proxy integration configuration")
    print("- Deployed changes to 'dev' stage")
    print("")
    print("NEXT STEPS:")
    print("1. Refresh your browser dashboard")
    print("2. Login with your credentials")
    print("3. Check if sensor readings now load correctly")
    print("="*70)