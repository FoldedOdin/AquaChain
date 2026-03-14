#!/usr/bin/env python3
"""
Test Technician Assignment Flow

This script tests the complete technician assignment flow:
1. Check if technicians exist in the database
2. Check if auto assignment Lambda is deployed
3. Test manual technician assignment
4. Check order data to see if assignment is working
"""

import boto3
import json
import sys
import os
from datetime import datetime, timezone
from decimal import Decimal

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'shared'))

def get_aws_clients():
    """Get AWS clients"""
    return {
        'dynamodb': boto3.resource('dynamodb'),
        'lambda': boto3.client('lambda'),
        'eventbridge': boto3.client('events')
    }

def check_technicians_table(dynamodb):
    """Check if technicians exist in the database"""
    print("\n🔍 Checking technicians table...")
    
    try:
        table = dynamodb.Table('aquachain-technicians')
        
        # Scan for all technicians
        response = table.scan()
        technicians = response.get('Items', [])
        
        print(f"✅ Found {len(technicians)} technicians in database")
        
        if technicians:
            print("\n📋 Technician Details:")
            for i, tech in enumerate(technicians[:3], 1):  # Show first 3
                print(f"  {i}. ID: {tech.get('technicianId', 'N/A')}")
                print(f"     Name: {tech.get('name', 'N/A')}")
                print(f"     Available: {tech.get('available', 'N/A')}")
                print(f"     Location: {tech.get('location', 'N/A')}")
                print(f"     Skills: {tech.get('skills', 'N/A')}")
                print()
        else:
            print("❌ No technicians found in database")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking technicians table: {e}")
        return False

def check_auto_assignment_lambda(lambda_client):
    """Check if auto assignment Lambda is deployed"""
    print("\n🔍 Checking auto assignment Lambda...")
    
    try:
        function_name = 'aquachain-function-auto-technician-assignment-dev'
        
        response = lambda_client.get_function(FunctionName=function_name)
        
        print(f"✅ Auto assignment Lambda found: {function_name}")
        print(f"   Runtime: {response['Configuration']['Runtime']}")
        print(f"   Handler: {response['Configuration']['Handler']}")
        print(f"   Last Modified: {response['Configuration']['LastModified']}")
        
        return True
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"❌ Auto assignment Lambda not found: {function_name}")
        return False
    except Exception as e:
        print(f"❌ Error checking auto assignment Lambda: {e}")
        return False

def check_eventbridge_rule(eventbridge_client):
    """Check if EventBridge rule exists for ORDER_PLACED events"""
    print("\n🔍 Checking EventBridge rule...")
    
    try:
        rule_name = 'aquachain-rule-order-placed-assignment-dev'
        
        response = eventbridge_client.describe_rule(Name=rule_name)
        
        print(f"✅ EventBridge rule found: {rule_name}")
        print(f"   State: {response['State']}")
        print(f"   Event Pattern: {response.get('EventPattern', 'N/A')}")
        
        # Check targets
        targets_response = eventbridge_client.list_targets_by_rule(Rule=rule_name)
        targets = targets_response.get('Targets', [])
        
        print(f"   Targets: {len(targets)}")
        for target in targets:
            print(f"     - {target.get('Arn', 'N/A')}")
        
        return True
        
    except eventbridge_client.exceptions.ResourceNotFoundException:
        print(f"❌ EventBridge rule not found: {rule_name}")
        return False
    except Exception as e:
        print(f"❌ Error checking EventBridge rule: {e}")
        return False

def test_manual_technician_assignment(lambda_client):
    """Test manual technician assignment"""
    print("\n🧪 Testing manual technician assignment...")
    
    try:
        function_name = 'aquachain-function-technician-assignment-dev'
        
        # Test payload
        test_payload = {
            'httpMethod': 'POST',
            'path': '/technician-assignment',
            'body': json.dumps({
                'orderId': 'test-order-123',
                'serviceLocation': {
                    'latitude': 12.9716,
                    'longitude': 77.5946,
                    'address': 'Bangalore, India'
                }
            })
        }
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        print(f"✅ Manual assignment test completed")
        print(f"   Status Code: {result.get('statusCode', 'N/A')}")
        
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            print(f"   Success: {body.get('success', 'N/A')}")
            print(f"   Message: {body.get('message', 'N/A')}")
        else:
            print(f"   Error: {result.get('body', 'N/A')}")
        
        return result.get('statusCode') == 200
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"❌ Technician assignment Lambda not found: {function_name}")
        return False
    except Exception as e:
        print(f"❌ Error testing manual assignment: {e}")
        return False

def check_order_with_technician_assignment(dynamodb, order_id):
    """Check a specific order to see if technician is assigned"""
    print(f"\n🔍 Checking order {order_id} for technician assignment...")
    
    try:
        table = dynamodb.Table('aquachain-orders')
        
        response = table.get_item(Key={'orderId': order_id})
        
        if 'Item' not in response:
            print(f"❌ Order {order_id} not found")
            return False
        
        order = response['Item']
        
        print(f"✅ Order found: {order_id}")
        print(f"   Status: {order.get('status', 'N/A')}")
        print(f"   Consumer ID: {order.get('consumerId', 'N/A')}")
        print(f"   Assigned Technician: {order.get('assignedTechnician', 'None')}")
        print(f"   Technician Assignment: {order.get('technicianAssignment', 'None')}")
        print(f"   Created At: {order.get('createdAt', 'N/A')}")
        print(f"   Updated At: {order.get('updatedAt', 'N/A')}")
        
        # Check status history
        status_history = order.get('statusHistory', [])
        print(f"   Status History ({len(status_history)} entries):")
        for i, entry in enumerate(status_history[-3:], 1):  # Show last 3
            print(f"     {i}. {entry.get('status', 'N/A')} - {entry.get('timestamp', 'N/A')}")
            print(f"        Message: {entry.get('message', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking order: {e}")
        return False

def create_test_technician(dynamodb):
    """Create a test technician for testing"""
    print("\n🔧 Creating test technician...")
    
    try:
        table = dynamodb.Table('aquachain-technicians')
        
        test_technician = {
            'PK': 'TECHNICIAN#test-tech-001',
            'SK': 'TECHNICIAN#test-tech-001',
            'technicianId': 'test-tech-001',
            'name': 'Test Technician',
            'phone': '+91-9876543210',
            'email': 'test.tech@aquachain.com',
            'available': True,
            'location': {
                'latitude': 12.9716,
                'longitude': 77.5946,
                'address': 'Bangalore, India',
                'city': 'Bangalore',
                'state': 'Karnataka',
                'pincode': '560001'
            },
            'skills': ['Installation', 'Maintenance', 'Repair'],
            'rating': 4.5,
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'updatedAt': datetime.now(timezone.utc).isoformat(),
            'GSI1PK': 'LOCATION#ALL',
            'GSI1SK': 'AVAILABLE#True#test-tech-001'
        }
        
        table.put_item(Item=test_technician)
        
        print(f"✅ Test technician created: test-tech-001")
        return True
        
    except Exception as e:
        print(f"❌ Error creating test technician: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Technician Assignment Flow")
    print("=" * 50)
    
    # Get AWS clients
    try:
        clients = get_aws_clients()
        print("✅ AWS clients initialized")
    except Exception as e:
        print(f"❌ Failed to initialize AWS clients: {e}")
        return
    
    # Test results
    results = {}
    
    # 1. Check technicians table
    results['technicians_exist'] = check_technicians_table(clients['dynamodb'])
    
    # If no technicians, create a test one
    if not results['technicians_exist']:
        results['test_technician_created'] = create_test_technician(clients['dynamodb'])
    
    # 2. Check auto assignment Lambda
    results['auto_assignment_lambda'] = check_auto_assignment_lambda(clients['lambda'])
    
    # 3. Check EventBridge rule
    results['eventbridge_rule'] = check_eventbridge_rule(clients['eventbridge'])
    
    # 4. Test manual assignment
    results['manual_assignment'] = test_manual_technician_assignment(clients['lambda'])
    
    # 5. Check specific order (use the order from context)
    test_order_id = 'ord_1773176454115'
    results['order_check'] = check_order_with_technician_assignment(clients['dynamodb'], test_order_id)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    # Overall assessment
    critical_tests = ['technicians_exist', 'auto_assignment_lambda', 'eventbridge_rule']
    critical_passed = all(results.get(test, False) for test in critical_tests)
    
    print(f"\n🎯 OVERALL STATUS: {'✅ READY' if critical_passed else '❌ ISSUES FOUND'}")
    
    if not critical_passed:
        print("\n🔧 RECOMMENDED ACTIONS:")
        if not results.get('technicians_exist'):
            print("   - Add technicians to the database")
        if not results.get('auto_assignment_lambda'):
            print("   - Deploy auto technician assignment Lambda")
        if not results.get('eventbridge_rule'):
            print("   - Deploy EventBridge rule for ORDER_PLACED events")

if __name__ == "__main__":
    main()