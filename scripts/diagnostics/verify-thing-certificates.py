#!/usr/bin/env python3
"""
Verify AWS IoT Thing certificates are properly configured
"""

import boto3
import json
from botocore.exceptions import ClientError

REGION = 'ap-south-1'
THING_NAME = 'ESP32-001'

def main():
    print("=" * 60)
    print("AWS IoT Thing Certificate Verification")
    print("=" * 60)
    
    iot = boto3.client('iot', region_name=REGION)
    
    # 1. Check Thing exists
    print(f"\n1. Checking Thing '{THING_NAME}'...")
    try:
        thing = iot.describe_thing(thingName=THING_NAME)
        print(f"   ✓ Thing exists")
        print(f"   ARN: {thing['thingArn']}")
    except ClientError as e:
        print(f"   ✗ Thing not found: {e}")
        return
    
    # 2. List principals (certificates) attached to Thing
    print(f"\n2. Checking attached certificates...")
    try:
        principals_response = iot.list_thing_principals(thingName=THING_NAME)
        principals = principals_response.get('principals', [])
        
        if not principals:
            print(f"   ✗ No certificates attached to Thing!")
            print(f"\n   To attach a certificate:")
            print(f"   1. Create certificate: aws iot create-keys-and-certificate --set-as-active")
            print(f"   2. Attach to Thing: aws iot attach-thing-principal --thing-name {THING_NAME} --principal <cert-arn>")
            return
        
        print(f"   ✓ Found {len(principals)} certificate(s)")
        
        for idx, principal in enumerate(principals, 1):
            cert_arn = principal
            cert_id = cert_arn.split('/')[-1]
            
            print(f"\n   Certificate {idx}:")
            print(f"   ARN: {cert_arn}")
            print(f"   ID: {cert_id}")
            
            # Get certificate details
            try:
                cert_response = iot.describe_certificate(certificateId=cert_id)
                cert_desc = cert_response['certificateDescription']
                
                status = cert_desc['status']
                created = cert_desc['creationDate']
                
                print(f"   Status: {status}")
                print(f"   Created: {created}")
                
                if status != 'ACTIVE':
                    print(f"   ✗ Certificate is {status} - must be ACTIVE!")
                    print(f"   Activate with: aws iot update-certificate --certificate-id {cert_id} --new-status ACTIVE")
                else:
                    print(f"   ✓ Certificate is ACTIVE")
                
                # Check attached policies
                print(f"\n   Checking policies for this certificate...")
                policies_response = iot.list_principal_policies(principal=cert_arn)
                policies = policies_response.get('policies', [])
                
                if not policies:
                    print(f"   ✗ No policies attached!")
                    print(f"   Attach policy: aws iot attach-policy --policy-name aquachain-device-policy-dev --target {cert_arn}")
                else:
                    print(f"   ✓ Found {len(policies)} policy/policies:")
                    for policy in policies:
                        print(f"     - {policy['policyName']}")
                
            except Exception as e:
                print(f"   ✗ Error getting certificate details: {e}")
        
        # 3. Get certificate PEM (for comparison with config.h)
        print(f"\n3. Certificate PEM (first 100 chars):")
        try:
            cert_response = iot.describe_certificate(certificateId=cert_id)
            cert_pem = cert_response['certificateDescription']['certificatePem']
            print(f"   {cert_pem[:100]}...")
            print(f"\n   ⚠ Compare this with AWS_CERT in your config.h")
            print(f"   They must match EXACTLY (including -----BEGIN CERTIFICATE-----)")
        except Exception as e:
            print(f"   ✗ Error getting certificate PEM: {e}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    print("\n" + "=" * 60)
    print("TROUBLESHOOTING MQTT rc=-2")
    print("=" * 60)
    print("\nMQTT rc=-2 (Connect Failed) usually means:")
    print("1. Certificate in config.h doesn't match AWS IoT Thing")
    print("2. Thing name in code doesn't match certificate")
    print("3. Certificate is not ACTIVE")
    print("4. No policy attached to certificate")
    print("5. System time is wrong (NTP failed)")
    print("\nTo fix NTP issue:")
    print("- Check your router allows NTP (UDP port 123)")
    print("- Try different NTP server: pool.ntp.org, time.google.com")
    print("- Or use manual time setting in ESP32 code")

if __name__ == '__main__':
    main()
