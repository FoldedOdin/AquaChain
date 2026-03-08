#!/usr/bin/env python3
"""
Fix AWS IoT Policy to allow publishing to aquachain/devices/+/data
"""

import boto3
import json

REGION = 'ap-south-1'
POLICY_NAME = 'aquachain-device-policy-dev'

# Corrected policy document with /devices/ in the path
POLICY_DOCUMENT = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["iot:Connect"],
            "Resource": f"arn:aws:iot:{REGION}:*:client/${{iot:Connection.Thing.ThingName}}",
            "Condition": {
                "Bool": {
                    "iot:Connection.Thing.IsAttached": "true"
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": ["iot:Publish"],
            "Resource": [
                f"arn:aws:iot:{REGION}:*:topic/aquachain/devices/${{iot:Connection.Thing.ThingName}}/data",
                f"arn:aws:iot:{REGION}:*:topic/aquachain/devices/${{iot:Connection.Thing.ThingName}}/telemetry",
                f"arn:aws:iot:{REGION}:*:topic/aquachain/devices/${{iot:Connection.Thing.ThingName}}/status"
            ]
        },
        {
            "Effect": "Allow",
            "Action": ["iot:Subscribe"],
            "Resource": f"arn:aws:iot:{REGION}:*:topicfilter/aquachain/devices/${{iot:Connection.Thing.ThingName}}/commands"
        },
        {
            "Effect": "Allow",
            "Action": ["iot:Receive"],
            "Resource": f"arn:aws:iot:{REGION}:*:topic/aquachain/devices/${{iot:Connection.Thing.ThingName}}/commands"
        },
        {
            "Effect": "Allow",
            "Action": ["iot:UpdateThingShadow", "iot:GetThingShadow"],
            "Resource": f"arn:aws:iot:{REGION}:*:thing/${{iot:Connection.Thing.ThingName}}"
        }
    ]
}

def main():
    print("Fixing AWS IoT Policy...")
    print(f"Policy Name: {POLICY_NAME}")
    print(f"Region: {REGION}")
    
    iot = boto3.client('iot', region_name=REGION)
    
    try:
        # Get current policy version
        response = iot.get_policy(policyName=POLICY_NAME)
        current_version = response['defaultVersionId']
        print(f"\nCurrent policy version: {current_version}")
        
        # Create new policy version
        print("\nCreating new policy version with corrected topic paths...")
        new_version_response = iot.create_policy_version(
            policyName=POLICY_NAME,
            policyDocument=json.dumps(POLICY_DOCUMENT, indent=2),
            setAsDefault=True
        )
        
        new_version = new_version_response['policyVersionId']
        print(f"✓ Created new policy version: {new_version}")
        print(f"✓ Set as default version")
        
        print("\n" + "=" * 60)
        print("Policy Updated Successfully!")
        print("=" * 60)
        print("\nThe policy now allows:")
        print("  ✓ aquachain/devices/ESP32-001/data")
        print("  ✓ aquachain/devices/ESP32-001/telemetry")
        print("  ✓ aquachain/devices/ESP32-001/status")
        print("\nYour ESP32 should now be able to connect!")
        print("Reset your ESP32 and watch for 'AWS IoT connected' message.")
        
    except Exception as e:
        print(f"\n✗ Error updating policy: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
