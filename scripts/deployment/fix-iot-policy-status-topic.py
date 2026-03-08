#!/usr/bin/env python3
"""
Fix IoT Policy to Allow Status Topic

This script updates the aquachain-device-policy-dev to allow
publishing to the status topic which is required for LWT messages.
"""

import boto3
import json

def fix_policy():
    iot = boto3.client('iot', region_name='ap-south-1')
    policy_name = 'aquachain-device-policy-dev'
    
    # Updated policy document
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["iot:Connect"],
                "Resource": "arn:aws:iot:ap-south-1:758346259059:client/${iot:Connection.Thing.ThingName}",
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
                    "arn:aws:iot:ap-south-1:758346259059:topic/aquachain/devices/${iot:Connection.Thing.ThingName}/data",
                    "arn:aws:iot:ap-south-1:758346259059:topic/aquachain/devices/${iot:Connection.Thing.ThingName}/telemetry",
                    "arn:aws:iot:ap-south-1:758346259059:topic/aquachain/devices/${iot:Connection.Thing.ThingName}/status"
                ]
            },
            {
                "Effect": "Allow",
                "Action": ["iot:Subscribe"],
                "Resource": "arn:aws:iot:ap-south-1:758346259059:topicfilter/aquachain/devices/${iot:Connection.Thing.ThingName}/commands"
            },
            {
                "Effect": "Allow",
                "Action": ["iot:Receive"],
                "Resource": "arn:aws:iot:ap-south-1:758346259059:topic/aquachain/devices/${iot:Connection.Thing.ThingName}/commands"
            },
            {
                "Effect": "Allow",
                "Action": ["iot:UpdateThingShadow", "iot:GetThingShadow"],
                "Resource": "arn:aws:iot:ap-south-1:758346259059:thing/${iot:Connection.Thing.ThingName}"
            }
        ]
    }
    
    print("=" * 60)
    print("Updating IoT Policy to Allow Status Topic")
    print("=" * 60)
    
    try:
        # Create new policy version
        response = iot.create_policy_version(
            policyName=policy_name,
            policyDocument=json.dumps(policy_document),
            setAsDefault=True
        )
        
        print(f"✓ Policy updated successfully")
        print(f"  New version: {response['policyVersionId']}")
        print(f"  Set as default: {response['isDefaultVersion']}")
        print()
        print("The policy now allows publishing to:")
        print("  - aquachain/devices/ESP32-001/data")
        print("  - aquachain/devices/ESP32-001/telemetry")
        print("  - aquachain/devices/ESP32-001/status ← ADDED")
        
    except Exception as e:
        print(f"✗ Error updating policy: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = fix_policy()
    exit(0 if success else 1)
