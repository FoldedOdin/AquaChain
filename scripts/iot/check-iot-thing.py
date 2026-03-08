#!/usr/bin/env python3
"""
Check AWS IoT Thing configuration and certificate attachment
"""

import boto3
import sys

def check_iot_thing(thing_name):
    """Check if IoT Thing exists and show its configuration"""
    
    iot_client = boto3.client('iot')
    
    print(f"🔍 Checking IoT Thing: {thing_name}")
    print("="*60)
    
    try:
        # Check if Thing exists
        response = iot_client.describe_thing(thingName=thing_name)
        print(f"✅ Thing exists: {thing_name}")
        print(f"   Thing ARN: {response['thingArn']}")
        print(f"   Thing Type: {response.get('thingTypeName', 'None')}")
        print(f"   Attributes: {response.get('attributes', {})}")
        
        # List attached principals (certificates)
        principals = iot_client.list_thing_principals(thingName=thing_name)
        
        if principals['principals']:
            print(f"\n📜 Attached Certificates:")
            for principal in principals['principals']:
                cert_id = principal.split('/')[-1]
                print(f"   - {cert_id}")
                
                # Get certificate details
                try:
                    cert_response = iot_client.describe_certificate(certificateId=cert_id)
                    cert_status = cert_response['certificateDescription']['status']
                    print(f"     Status: {cert_status}")
                except Exception as e:
                    print(f"     Error getting cert details: {e}")
                
                # List attached policies
                try:
                    policies = iot_client.list_principal_policies(principal=principal)
                    if policies['policies']:
                        print(f"     Policies:")
                        for policy in policies['policies']:
                            print(f"       - {policy['policyName']}")
                    else:
                        print(f"     ⚠️  No policies attached!")
                except Exception as e:
                    print(f"     Error getting policies: {e}")
        else:
            print(f"\n⚠️  No certificates attached to this Thing!")
        
        return True
        
    except iot_client.exceptions.ResourceNotFoundException:
        print(f"❌ Thing '{thing_name}' does not exist")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_all_things():
    """List all IoT Things"""
    
    iot_client = boto3.client('iot')
    
    print("\n📋 All IoT Things:")
    print("="*60)
    
    try:
        response = iot_client.list_things()
        
        if response['things']:
            for thing in response['things']:
                print(f"   - {thing['thingName']}")
        else:
            print("   No Things found")
            
    except Exception as e:
        print(f"❌ Error listing Things: {e}")

def main():
    print("="*60)
    print("AWS IoT Thing Configuration Check")
    print("="*60)
    print()
    
    # Check common Thing names
    thing_names = ["ESP32-001", "DEV-0001", "DEV-001"]
    
    found = False
    for thing_name in thing_names:
        if check_iot_thing(thing_name):
            found = True
            print()
    
    if not found:
        print("\n⚠️  None of the expected Things found!")
        list_all_things()
        print("\n💡 Solution:")
        print("   1. Create a new Thing with the correct name")
        print("   2. Attach your certificate to the Thing")
        print("   3. Update config.h to match the Thing name")
    else:
        print("\n✅ Thing found and configured")
        print("\n💡 Next Steps:")
        print("   1. Update config.h DEVICE_ID to match the Thing name")
        print("   2. Reflash your ESP32")
        print("   3. Test connection")

if __name__ == '__main__':
    main()
