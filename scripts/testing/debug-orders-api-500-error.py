#!/usr/bin/env python3
"""
Debug the 500 error in the orders API
"""

import boto3
import json
import sys
import os
from datetime import datetime, timezone

# Add the lambda directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'orders'))

def test_lambda_directly():
    """Test the get_orders Lambda function directly to see the error"""
    
    try:
        from get_orders import handler
        
        # Create a mock event
        mock_event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': '51a3ed4a-c0b1-70e8-a7d7-19d7ca035fe0'
                    }
                }
            },
            'httpMethod': 'GET',
            'path': '/api/orders'
        }
        
        mock_context = type('MockContext', (), {
            'request_id': 'test-request-123',
            'function_name': 'test-function'
        })()
        
        print("🧪 Testing get_orders Lambda function directly...")
        
        # Call the handler
        response = handler(mock_event, mock_context)
        
        print(f"📊 Response Status: {response['statusCode']}")
        print(f"📋 Response Body: {response.get('body', 'No body')}")
        
        if response['statusCode'] != 200:
            print("❌ Lambda function returned an error")
            body = json.loads(response['body']) if response.get('body') else {}
            print(f"Error details: {body}")
        else:
            print("✅ Lambda function executed successfully")
            
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")
        import traceback
        traceback.print_exc()

def check_dynamodb_data():
    """Check the DynamoDB data to see if there are any issues"""
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        orders_table = dynamodb.Table('aquachain-orders')
        
        print("🔍 Checking DynamoDB data...")
        
        # Get orders for the specific user
        response = orders_table.query(
            IndexName='userId-createdAt-index',
            KeyConditionExpression='userId = :user_id',
            ExpressionAttributeValues={
                ':user_id': '51a3ed4a-c0b1-70e8-a7d7-19d7ca035fe0'
            }
        )
        
        orders = response.get('Items', [])
        print(f"📋 Found {len(orders)} orders for user")
        
        for order in orders:
            order_id = order.get('orderId')
            print(f"\n📋 Order {order_id}:")
            
            # Check for problematic fields
            technician = order.get('technician')
            assignment = order.get('technicianAssignment')
            
            if technician:
                print(f"   ✅ Has technician object: {type(technician)}")
                # Check for any problematic data types
                for key, value in technician.items():
                    print(f"      {key}: {type(value)} = {value}")
            
            if assignment:
                print(f"   ✅ Has assignment object: {type(assignment)}")
                # Check for any problematic data types
                for key, value in assignment.items():
                    print(f"      {key}: {type(value)} = {value}")
                    
    except Exception as e:
        print(f"❌ Error checking DynamoDB data: {e}")
        import traceback
        traceback.print_exc()

def test_json_serialization():
    """Test if the data can be JSON serialized"""
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        orders_table = dynamodb.Table('aquachain-orders')
        
        print("🧪 Testing JSON serialization...")
        
        response = orders_table.query(
            IndexName='userId-createdAt-index',
            KeyConditionExpression='userId = :user_id',
            ExpressionAttributeValues={
                ':user_id': '51a3ed4a-c0b1-70e8-a7d7-19d7ca035fe0'
            }
        )
        
        orders = response.get('Items', [])
        
        for order in orders:
            order_id = order.get('orderId')
            print(f"\n🧪 Testing serialization for order {order_id}...")
            
            try:
                # Try to serialize the order
                json_str = json.dumps(order, default=str)
                print(f"   ✅ Order serializes successfully")
            except Exception as e:
                print(f"   ❌ Order serialization failed: {e}")
                
                # Check individual fields
                for key, value in order.items():
                    try:
                        json.dumps({key: value}, default=str)
                    except Exception as field_error:
                        print(f"      ❌ Field '{key}' causes serialization error: {field_error}")
                        print(f"         Type: {type(value)}, Value: {value}")
                        
    except Exception as e:
        print(f"❌ Error testing JSON serialization: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main execution"""
    print("🚀 Debugging Orders API 500 Error...")
    
    print("\n" + "="*50)
    print("1. Testing Lambda Function Directly")
    print("="*50)
    test_lambda_directly()
    
    print("\n" + "="*50)
    print("2. Checking DynamoDB Data")
    print("="*50)
    check_dynamodb_data()
    
    print("\n" + "="*50)
    print("3. Testing JSON Serialization")
    print("="*50)
    test_json_serialization()

if __name__ == "__main__":
    main()