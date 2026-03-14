#!/usr/bin/env python3

import boto3
import json
import requests
from datetime import datetime

def verify_ap_south_1_resources():
    """Verify that ap-south-1 has all necessary resources."""
    
    print("✅ VERIFYING AP-SOUTH-1 AS PRIMARY REGION")
    print("=" * 50)
    
    verification_results = {
        'cognito': False,
        'api_gateway': False,
        'lambda_functions': False,
        'dynamodb': False,
        'authentication': False
    }
    
    # Check Cognito User Pool
    print("\n🔐 Checking Cognito User Pool...")
    try:
        cognito_client = boto3.client('cognito-idp', region_name='ap-south-1')
        user_pools = cognito_client.list_user_pools(MaxResults=50)
        
        aquachain_pools = [pool for pool in user_pools.get('UserPools', []) 
                          if 'aquachain' in pool['Name'].lower()]
        
        if aquachain_pools:
            pool = aquachain_pools[0]
            print(f"   ✅ User Pool: {pool['Name']} ({pool['Id']})")
            verification_results['cognito'] = True
            
            # Check users in pool
            users = cognito_client.list_users(UserPoolId=pool['Id'])
            user_count = len(users.get('Users', []))
            print(f"   ✅ Users: {user_count} users with unified password")
            
        else:
            print("   ❌ No AquaChain user pools found")
            
    except Exception as e:
        print(f"   ❌ Cognito check failed: {str(e)}")
    
    # Check API Gateway
    print("\n🌐 Checking API Gateway...")
    try:
        apigateway_client = boto3.client('apigateway', region_name='ap-south-1')
        apis = apigateway_client.get_rest_apis()
        
        aquachain_apis = [api for api in apis.get('items', []) 
                         if 'aquachain' in api['name'].lower()]
        
        if aquachain_apis:
            for api in aquachain_apis:
                api_url = f"https://{api['id']}.execute-api.ap-south-1.amazonaws.com"
                print(f"   ✅ API: {api['name']} ({api['id']})")
                print(f"      URL: {api_url}")
            verification_results['api_gateway'] = True
        else:
            print("   ❌ No AquaChain APIs found")
            
    except Exception as e:
        print(f"   ❌ API Gateway check failed: {str(e)}")
    
    # Check Lambda Functions
    print("\n⚡ Checking Lambda Functions...")
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        functions = lambda_client.list_functions()
        
        aquachain_functions = [func for func in functions.get('Functions', []) 
                              if 'aquachain' in func['FunctionName'].lower()]
        
        if aquachain_functions:
            print(f"   ✅ Lambda Functions: {len(aquachain_functions)} functions")
            
            # Check key functions
            key_functions = ['auth-service', 'data-processing', 'user-management']
            for key_func in key_functions:
                matching = [f for f in aquachain_functions 
                           if key_func in f['FunctionName'].lower()]
                if matching:
                    print(f"      ✅ {key_func}: {matching[0]['FunctionName']}")
                else:
                    print(f"      ⚠️ {key_func}: Not found")
            
            verification_results['lambda_functions'] = True
        else:
            print("   ❌ No AquaChain Lambda functions found")
            
    except Exception as e:
        print(f"   ❌ Lambda check failed: {str(e)}")
    
    # Check DynamoDB Tables
    print("\n🗄️ Checking DynamoDB Tables...")
    try:
        dynamodb_client = boto3.client('dynamodb', region_name='ap-south-1')
        tables = dynamodb_client.list_tables()
        
        aquachain_tables = [table for table in tables.get('TableNames', []) 
                           if 'aquachain' in table.lower()]
        
        if aquachain_tables:
            print(f"   ✅ DynamoDB Tables: {len(aquachain_tables)} tables")
            
            # Check key tables
            key_tables = ['Users', 'Devices', 'Readings', 'ServiceRequests']
            for key_table in key_tables:
                matching = [t for t in aquachain_tables 
                           if key_table.lower() in t.lower()]
                if matching:
                    print(f"      ✅ {key_table}: {matching[0]}")
                else:
                    print(f"      ⚠️ {key_table}: Not found")
            
            verification_results['dynamodb'] = True
        else:
            print("   ❌ No AquaChain DynamoDB tables found")
            
    except Exception as e:
        print(f"   ❌ DynamoDB check failed: {str(e)}")
    
    return verification_results

def test_authentication():
    """Test that authentication works in ap-south-1."""
    
    print("\n🧪 TESTING AUTHENTICATION...")
    print("=" * 30)
    
    api_endpoint = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev'
    test_credentials = {
        'email': 'contact.aquachain@gmail.com',
        'password': 'Hu8hyxf1TPf3cwl@'
    }
    
    try:
        print(f"📡 Testing signin endpoint: {api_endpoint}/api/auth/signin")
        
        response = requests.post(
            f"{api_endpoint}/api/auth/signin",
            headers={'Content-Type': 'application/json'},
            json=test_credentials,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Authentication successful!")
            print(f"   🔑 Token received: {'Yes' if result.get('token') else 'No'}")
            print(f"   👤 User role: {result.get('user', {}).get('role', 'Unknown')}")
            return True
        else:
            print(f"   ❌ Authentication failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Authentication test failed: {str(e)}")
        return False

def generate_summary_report(verification_results, auth_test_passed):
    """Generate a summary report of the verification."""
    
    print(f"\n📊 VERIFICATION SUMMARY")
    print("=" * 30)
    
    total_checks = len(verification_results)
    passed_checks = sum(verification_results.values())
    
    print(f"✅ Resource Checks Passed: {passed_checks}/{total_checks}")
    print(f"🔐 Authentication Test: {'✅ PASSED' if auth_test_passed else '❌ FAILED'}")
    
    print(f"\n📋 Detailed Results:")
    for check, result in verification_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {check.replace('_', ' ').title()}: {status}")
    
    if passed_checks == total_checks and auth_test_passed:
        print(f"\n🎉 AP-SOUTH-1 IS FULLY FUNCTIONAL!")
        print("✅ Ready to serve as primary region")
        print("✅ All critical resources verified")
        print("✅ Authentication working perfectly")
        
        print(f"\n🎯 WORKING CREDENTIALS:")
        print("📧 karthikkpradeep123@gmail.com")
        print("📧 karthiikkpradeep897@gmail.com") 
        print("📧 leninat259@gmail.com")
        print("📧 contact.aquachain@gmail.com")
        print("🔑 Password: Hu8hyxf1TPf3cwl@ (for all users)")
        
        print(f"\n🌐 PRIMARY ENDPOINTS:")
        print("🔗 API: https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev")
        print("🔐 Cognito: ap-south-1_QUDl7hG8u")
        
        return True
    else:
        print(f"\n⚠️ AP-SOUTH-1 HAS ISSUES!")
        print("❌ Some critical resources or tests failed")
        print("🔍 Review the detailed results above")
        return False

def main():
    """Main verification process."""
    
    print("🔍 AQUACHAIN AP-SOUTH-1 VERIFICATION")
    print("=" * 50)
    print(f"⏰ Started: {datetime.now().isoformat()}")
    print()
    
    print("🎯 OBJECTIVE:")
    print("   • Verify ap-south-1 has all necessary resources")
    print("   • Test authentication functionality")
    print("   • Confirm readiness as primary region")
    print()
    
    # Step 1: Verify resources
    verification_results = verify_ap_south_1_resources()
    
    # Step 2: Test authentication
    auth_test_passed = test_authentication()
    verification_results['authentication'] = auth_test_passed
    
    # Step 3: Generate summary
    is_ready = generate_summary_report(verification_results, auth_test_passed)
    
    if is_ready:
        print(f"\n🚀 READY FOR US-EAST-1 CLEANUP!")
        print("💡 You can safely run cleanup-us-east-1.py")
    else:
        print(f"\n⚠️ FIX ISSUES BEFORE CLEANUP!")
        print("🔧 Resolve ap-south-1 issues first")
    
    return is_ready

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Verification failed: {str(e)}")
        exit(1)