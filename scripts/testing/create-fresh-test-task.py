#!/usr/bin/env python3
"""
Create Fresh Test Task

Creates a single clean test task for Sidharth Lenin to verify the dashboard works.
"""

import boto3
import json
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

def create_test_service_request():
    """Create a single test service request for Sidharth"""
    try:
        dynamodb = boto3.resource('dynamodb')
        service_requests_table = dynamodb.Table('aquachain-service-requests')
        
        print("🆕 Creating fresh test service request...")
        
        sidharth_id = '31333d7a-7031-703b-2e21-966a49444222'
        service_request_id = f"SR-FRESH-{uuid.uuid4().hex[:8].upper()}"
        
        # Create service request with proper Decimal types
        new_service_request = {
            'requestId': service_request_id,
            'customerId': '51a3ed4a-c0b1-70e8-a7d7-19d7ca035fe0',
            'deviceId': f'device-fresh-{uuid.uuid4().hex[:8]}',
            'technicianId': sidharth_id,
            'status': 'assigned',
            'priority': 'normal',
            'description': 'Fresh test task - Device installation and setup',
            'location': {
                'address': '73/1276, Ernakulam, Kerala, 682012',
                'latitude': Decimal('10.0261'),
                'longitude': Decimal('76.3125')
            },
            'customerInfo': {
                'name': 'Karthik K Pradeep',
                'email': 'karthikkpradeep123@gmail.com',
                'phone': '+918547613649'
            },
            'deviceInfo': {
                'model': 'AquaChain Pro',
                'serialNumber': f'SN-FRESH-{service_request_id}'
            },
            'createdAt': datetime.now().isoformat(),
            'dueDate': (datetime.now() + timedelta(days=1)).isoformat(),
            'estimatedArrival': (datetime.now() + timedelta(hours=2)).isoformat(),
            'paymentMethod': 'ONLINE',
            'orderAmount': Decimal('5499'),
            'specialInstructions': 'Fresh test scenario for dashboard verification'
        }
        
        print(f"   🔧 Creating service request: {service_request_id}")
        print(f"   👤 Assigned to: Sidharth Lenin")
        print(f"   📍 Location: {new_service_request['location']['address']}")
        
        service_requests_table.put_item(Item=new_service_request)
        
        print(f"✅ Created fresh test service request successfully!")
        
        return new_service_request
        
    except Exception as e:
        print(f"❌ Error creating test service request: {e}")
        return None

def verify_task_created():
    """Verify the task was created and can be retrieved"""
    try:
        dynamodb = boto3.resource('dynamodb')
        service_requests_table = dynamodb.Table('aquachain-service-requests')
        
        sidharth_id = '31333d7a-7031-703b-2e21-966a49444222'
        
        print("🔍 Verifying task creation...")
        
        # Query for Sidharth's tasks
        response = service_requests_table.scan(
            FilterExpression='technicianId = :tech_id AND #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':tech_id': sidharth_id,
                ':status': 'assigned'
            }
        )
        
        tasks = response.get('Items', [])
        
        print(f"✅ Found {len(tasks)} assigned tasks for Sidharth:")
        
        for task in tasks:
            print(f"   🔧 Task ID: {task['requestId']}")
            print(f"      Description: {task['description']}")
            print(f"      Status: {task['status']}")
            print(f"      Customer: {task['customerInfo']['name']}")
            print(f"      Due Date: {task.get('dueDate', 'N/A')}")
            print()
        
        return tasks
        
    except Exception as e:
        print(f"❌ Error verifying task: {e}")
        return []

def test_lambda_function_with_fresh_data():
    """Test the Lambda function with the fresh data"""
    try:
        lambda_client = boto3.client('lambda')
        
        print("🧪 Testing Lambda function with fresh data...")
        
        # Create test event
        test_event = {
            "httpMethod": "GET",
            "path": "/api/v1/technician/tasks",
            "headers": {
                "Authorization": "Bearer test-token",
                "Content-Type": "application/json"
            },
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "31333d7a-7031-703b-2e21-966a49444222",
                        "email": "leninat259@gmail.com",
                        "cognito:username": "leninat259@gmail.com"
                    }
                }
            },
            "queryStringParameters": None,
            "body": None
        }
        
        # Invoke the function
        response = lambda_client.invoke(
            FunctionName='aquachain-function-technician-tasks-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        print(f"📊 Lambda Response:")
        print(f"   Status Code: {payload.get('statusCode', 'N/A')}")
        
        if 'body' in payload:
            try:
                body = json.loads(payload['body'])
                if 'tasks' in body:
                    print(f"   ✅ Tasks returned: {len(body['tasks'])}")
                    for task in body['tasks']:
                        print(f"      - {task.get('taskId', 'N/A')}: {task.get('description', 'N/A')}")
                else:
                    print(f"   ❌ No tasks in response")
                    print(f"   Response: {json.dumps(body, indent=2)}")
            except json.JSONDecodeError:
                print(f"   Raw response: {payload['body']}")
        
        if 'errorMessage' in payload:
            print(f"   ❌ Error: {payload['errorMessage']}")
        
        return payload
        
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")
        return None

def main():
    """Main function"""
    print("🚀 Creating Fresh Test Task for Sidharth Lenin")
    print("=" * 60)
    
    # Step 1: Create fresh test service request
    print("\n1. CREATE FRESH TEST TASK")
    print("-" * 30)
    
    test_task = create_test_service_request()
    
    # Step 2: Verify task was created
    print("\n2. VERIFY TASK CREATION")
    print("-" * 30)
    
    tasks = verify_task_created()
    
    # Step 3: Test Lambda function
    print("\n3. TEST LAMBDA FUNCTION")
    print("-" * 30)
    
    lambda_response = test_lambda_function_with_fresh_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FRESH TEST SUMMARY")
    print("=" * 60)
    
    if test_task and len(tasks) > 0:
        print("✅ SUCCESS!")
        print(f"   🔧 Created 1 fresh test task")
        print(f"   👤 Assigned to Sidharth Lenin")
        print(f"   📱 Dashboard should show 1 task")
        
        if lambda_response and lambda_response.get('statusCode') == 200:
            print(f"   ✅ Lambda function returns tasks correctly")
        else:
            print(f"   ❌ Lambda function has issues")
            
    else:
        print("❌ FAILED!")
        print(f"   🔧 Could not create test task")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"1. Log in to technician dashboard as Sidharth Lenin")
    print(f"2. Email: leninat259@gmail.com")
    print(f"3. Check if the task appears in the dashboard")
    print(f"4. If not visible, check browser console for errors")

if __name__ == "__main__":
    main()