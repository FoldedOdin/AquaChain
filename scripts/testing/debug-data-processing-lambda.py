#!/usr/bin/env python3
"""
Debug the data processing Lambda to see why it's not updating lastSeen
"""

import boto3
import json
from datetime import datetime, timedelta

def check_lambda_logs():
    """Check recent logs from data processing Lambda"""
    try:
        logs_client = boto3.client('logs', region_name='ap-south-1')
        
        # Function name
        func_name = 'aquachain-function-data-processing-dev'
        log_group = f'/aws/lambda/{func_name}'
        
        print(f"🔍 Checking logs for: {func_name}")
        
        # Get recent logs (last 2 hours)
        now = datetime.now()
        two_hours_ago = now - timedelta(hours=2)
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=int(two_hours_ago.timestamp() * 1000),
            endTime=int(now.timestamp() * 1000),
            limit=50
        )
        
        events = response.get('events', [])
        
        print(f"📋 Found {len(events)} log events in last 2 hours")
        
        if events:
            print(f"\n📋 Recent Log Events:")
            for event in events[-20:]:  # Last 20 events
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                print(f"   {timestamp}: {message}")
        else:
            print(f"❌ No recent log events found")
            
        return len(events) > 0
        
    except Exception as e:
        print(f"❌ Error checking logs: {e}")
        return False

def check_iot_rule():
    """Check if IoT Core rule is configured correctly"""
    try:
        iot_client = boto3.client('iot', region_name='ap-south-1')
        
        # List IoT rules
        response = iot_client.list_topic_rules()
        rules = response.get('rules', [])
        
        print(f"\n🔍 Found {len(rules)} IoT rules:")
        
        data_processing_rules = []
        for rule in rules:
            rule_name = rule['ruleName']
            if 'data' in rule_name.lower() or 'ingestion' in rule_name.lower():
                data_processing_rules.append(rule)
                print(f"   📋 {rule_name} - {rule.get('description', 'No description')}")
        
        # Check rule details
        for rule in data_processing_rules:
            rule_name = rule['ruleName']
            
            try:
                rule_detail = iot_client.get_topic_rule(ruleName=rule_name)
                rule_info = rule_detail['rule']
                
                print(f"\n📋 Rule Details: {rule_name}")
                print(f"   SQL: {rule_info.get('sql', 'No SQL')}")
                print(f"   Disabled: {rule_info.get('ruleDisabled', False)}")
                
                actions = rule_info.get('actions', [])
                print(f"   Actions ({len(actions)}):")
                
                for action in actions:
                    if 'lambda' in action:
                        lambda_action = action['lambda']
                        func_arn = lambda_action.get('functionArn', 'Unknown')
                        print(f"     Lambda: {func_arn}")
                    elif 'dynamoDBv2' in action:
                        dynamo_action = action['dynamoDBv2']
                        table_name = dynamo_action.get('tableName', 'Unknown')
                        print(f"     DynamoDB: {table_name}")
                
            except Exception as e:
                print(f"   ❌ Error getting rule details: {e}")
        
        return len(data_processing_rules) > 0
        
    except Exception as e:
        print(f"❌ Error checking IoT rules: {e}")
        return False

def test_lambda_directly():
    """Test the data processing Lambda directly"""
    try:
        lambda_client = boto3.client('lambda', region_name='ap-south-1')
        
        func_name = 'aquachain-function-data-processing-dev'
        
        # Create test payload
        test_payload = {
            "deviceId": "ESP32-001",
            "reading": {
                "pH": 7.2,
                "turbidity": 3.5,
                "tds": 450,
                "temperature": 22.5
            },
            "timestamp": datetime.now().isoformat() + 'Z'
        }
        
        print(f"\n🧪 Testing Lambda directly with payload:")
        print(json.dumps(test_payload, indent=2))
        
        # Invoke Lambda
        response = lambda_client.invoke(
            FunctionName=func_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        print(f"\n📋 Lambda Response:")
        print(f"   Status Code: {response['StatusCode']}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        # Check if successful
        if response['StatusCode'] == 200 and payload.get('statusCode') == 200:
            print(f"✅ Lambda executed successfully")
            return True
        else:
            print(f"❌ Lambda execution failed")
            return False
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

def check_device_after_test():
    """Check if device status was updated after test"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        devices_table = dynamodb.Table('AquaChain-Devices')
        
        response = devices_table.get_item(Key={'deviceId': 'ESP32-001'})
        
        if 'Item' not in response:
            print(f"❌ Device ESP32-001 not found")
            return
        
        device = response['Item']
        
        print(f"\n📋 Device Status After Test:")
        print(f"   Connection Status: {device.get('connectionStatus', 'Not set')}")
        print(f"   Last Seen: {device.get('lastSeen', 'Not set')}")
        print(f"   Status Updated At: {device.get('statusUpdatedAt', 'Not set')}")
        
        # Check if lastSeen is recent (within last 5 minutes)
        last_seen = device.get('lastSeen')
        if last_seen:
            try:
                last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                now = datetime.now(last_seen_dt.tzinfo)
                time_diff = now - last_seen_dt
                
                if time_diff.total_seconds() <= 300:  # 5 minutes
                    print(f"✅ Device lastSeen is recent ({time_diff.total_seconds():.1f} seconds ago)")
                else:
                    print(f"❌ Device lastSeen is old ({time_diff.total_seconds() / 60:.1f} minutes ago)")
            except Exception as e:
                print(f"❌ Error parsing lastSeen: {e}")
        
    except Exception as e:
        print(f"❌ Error checking device: {e}")

def main():
    print("🔧 Debugging Data Processing Lambda")
    print("=" * 40)
    
    # Step 1: Check Lambda logs
    print("\n1. Checking Lambda Logs...")
    has_recent_activity = check_lambda_logs()
    
    # Step 2: Check IoT rules
    print("\n2. Checking IoT Core Rules...")
    has_iot_rules = check_iot_rule()
    
    # Step 3: Test Lambda directly
    print("\n3. Testing Lambda Directly...")
    lambda_success = test_lambda_directly()
    
    # Step 4: Check device status after test
    if lambda_success:
        print("\n4. Checking Device Status After Test...")
        import time
        time.sleep(3)  # Wait for update
        check_device_after_test()
    
    # Summary
    print(f"\n📋 Debug Summary:")
    print(f"   Recent Lambda Activity: {'✅' if has_recent_activity else '❌'}")
    print(f"   IoT Rules Configured: {'✅' if has_iot_rules else '❌'}")
    print(f"   Lambda Direct Test: {'✅' if lambda_success else '❌'}")
    
    if not has_recent_activity:
        print(f"\n🔧 Recommendations:")
        print(f"   1. Check if IoT Core rule is enabled and routing to Lambda")
        print(f"   2. Verify device is publishing to correct MQTT topic")
        print(f"   3. Check Lambda function permissions")
    
    if lambda_success:
        print(f"\n✅ Lambda function is working correctly")
        print(f"   The issue may be with IoT Core rule configuration")
    else:
        print(f"\n❌ Lambda function has issues")
        print(f"   Check the error logs above for details")

if __name__ == "__main__":
    main()