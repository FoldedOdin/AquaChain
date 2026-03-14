#!/usr/bin/env python3
"""
Debug browser login issue by testing different scenarios
"""

import requests
import json
import time

def test_login_scenarios():
    """Test different login scenarios to identify the issue"""
    print("🔍 Testing Login Scenarios")
    print("=" * 60)
    
    url = 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/auth/signin'
    
    # Test credentials
    test_cases = [
        {
            'name': 'Exact Frontend Payload',
            'payload': {
                'email': 'leninat259@gmail.com',
                'password': 'AquaChain123!',
                'rememberMe': True,
                'csrfToken': 'mock-csrf-token-12345',
                'recaptchaToken': 'dev-recaptcha-token-' + str(int(time.time() * 1000))
            },
            'headers': {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        },
        {
            'name': 'Minimal Payload',
            'payload': {
                'email': 'leninat259@gmail.com',
                'password': 'AquaChain123!'
            },
            'headers': {
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'Case Sensitive Email',
            'payload': {
                'email': 'Leninat259@gmail.com',  # Capital L
                'password': 'AquaChain123!'
            },
            'headers': {
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'Email with Spaces',
            'payload': {
                'email': ' leninat259@gmail.com ',  # Spaces around
                'password': 'AquaChain123!'
            },
            'headers': {
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'Wrong Password',
            'payload': {
                'email': 'leninat259@gmail.com',
                'password': 'WrongPassword123!'
            },
            'headers': {
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'Other Technician',
            'payload': {
                'email': 'karthiikkpradeep897@gmail.com',
                'password': 'AquaChain123!'
            },
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"   Email: {test_case['payload']['email']}")
        
        try:
            response = requests.post(url, json=test_case['payload'], headers=test_case['headers'], timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS (200)")
                data = response.json()
                if 'user' in data:
                    user = data['user']
                    print(f"   👤 User: {user.get('email')} ({user.get('role')})")
                    print(f"   🔑 Token: {'✓' if data.get('token') else '✗'}")
                results.append({'test': test_case['name'], 'status': 'SUCCESS', 'code': 200})
            else:
                print(f"   ❌ FAILED ({response.status_code})")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Raw: {response.text[:100]}...")
                results.append({'test': test_case['name'], 'status': 'FAILED', 'code': response.status_code})
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            results.append({'test': test_case['name'], 'status': 'EXCEPTION', 'error': str(e)})
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    for result in results:
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    print(f"\n🎯 Success Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")

def check_cognito_users():
    """Check if the Cognito users exist and are properly configured"""
    print("\n🔍 Checking Cognito Users")
    print("=" * 60)
    
    import boto3
    
    try:
        cognito_client = boto3.client('cognito-idp', region_name='ap-south-1')
        user_pool_id = 'ap-south-1_example'  # This should be from environment
        
        # Try to get user pool info
        try:
            response = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
            print(f"✅ User Pool found: {response['UserPool']['Name']}")
        except Exception as e:
            print(f"❌ User Pool error: {e}")
            return
        
        # Check specific users
        test_emails = ['leninat259@gmail.com', 'karthiikkpradeep897@gmail.com']
        
        for email in test_emails:
            try:
                response = cognito_client.admin_get_user(
                    UserPoolId=user_pool_id,
                    Username=email
                )
                
                user_status = response['UserStatus']
                enabled = response['Enabled']
                groups = []
                
                # Get user groups
                try:
                    groups_response = cognito_client.admin_list_groups_for_user(
                        UserPoolId=user_pool_id,
                        Username=email
                    )
                    groups = [g['GroupName'] for g in groups_response['Groups']]
                except:
                    pass
                
                print(f"✅ {email}:")
                print(f"   Status: {user_status}")
                print(f"   Enabled: {enabled}")
                print(f"   Groups: {groups}")
                
            except Exception as e:
                print(f"❌ {email}: {e}")
    
    except Exception as e:
        print(f"❌ Cognito check failed: {e}")

def main():
    """Main function"""
    test_login_scenarios()
    check_cognito_users()

if __name__ == "__main__":
    main()