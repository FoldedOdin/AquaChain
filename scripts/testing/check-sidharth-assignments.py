#!/usr/bin/env python3
"""
Check Sidharth Lenin's Current Assignments

This script checks all assignments for Sidharth Lenin across:
1. Orders table (order assignments)
2. Service requests table (tasks)
3. Users table (technician status)
"""

import boto3
import json
from datetime import datetime

def check_sidharth_in_orders():
    """Check if Sidharth is assigned to any orders"""
    print("🔍 Checking orders assigned to Sidharth Lenin...")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        orders_table = dynamodb.Table('aquachain-orders')
        
        sidharth_id = '31333d7a-7031-703b-2e21-966a49444222'
        
        # Scan for orders assigned to Sidharth
        response = orders_table.scan(
            FilterExpression='assignedTechnician = :tech_id',
            ExpressionAttributeValues={':tech_id': sidharth_id}
        )
        
        orders = response.get('Items', [])
        print(f"✅ Found {len(orders)} orders assigned to Sidharth")
        
        for order in orders:
            print(f"  📋 Order: {order.get('orderId', 'N/A')}")
            print(f"     Status: {order.get('status', 'N/A')}")
            print(f"     Customer: {order.get('customerName', 'N/A')}")
            print(f"     Technician Name: {order.get('assignedTechnicianName', 'N/A')}")
            print(f"     Assignment: {order.get('technicianAssignment', {})}")
            print()
        
        return orders
        
    except Exception as e:
        print(f"❌ Error checking orders: {e}")
        return []

def check_sidharth_in_service_requests():
    """Check if Sidharth has any service requests/tasks"""
    print("🔍 Checking service requests assigned to Sidharth Lenin...")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        service_requests_table = dynamodb.Table('aquachain-service-requests')
        
        sidharth_id = '31333d7a-7031-703b-2e21-966a49444222'
        
        # Scan for service requests assigned to Sidharth
        response = service_requests_table.scan(
            FilterExpression='technicianId = :tech_id',
            ExpressionAttributeValues={':tech_id': sidharth_id}
        )
        
        service_requests = response.get('Items', [])
        print(f"✅ Found {len(service_requests)} service requests assigned to Sidharth")
        
        for sr in service_requests:
            print(f"  🔧 Request: {sr.get('requestId', 'N/A')}")
            print(f"     Status: {sr.get('status', 'N/A')}")
            print(f"     Description: {sr.get('description', 'N/A')}")
            print(f"     Customer: {sr.get('customerInfo', {}).get('name', 'N/A')}")
            print(f"     Created: {sr.get('createdAt', 'N/A')}")
            print(f"     Due Date: {sr.get('dueDate', 'N/A')}")
            print()
        
        return service_requests
        
    except Exception as e:
        print(f"❌ Error checking service requests: {e}")
        return []

def check_sidharth_technician_status():
    """Check Sidharth's technician status in users table"""
    print("🔍 Checking Sidharth's technician status...")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        users_table = dynamodb.Table('AquaChain-Users')
        
        sidharth_id = '31333d7a-7031-703b-2e21-966a49444222'
        
        # Get Sidharth's user record
        response = users_table.get_item(Key={'userId': sidharth_id})
        
        if 'Item' not in response:
            print("❌ Sidharth not found in users table")
            return None
        
        user = response['Item']
        print(f"✅ Found Sidharth in users table")
        print(f"  👤 Name: {user.get('profile', {}).get('firstName', 'N/A')} {user.get('profile', {}).get('lastName', 'N/A')}")
        print(f"  📧 Email: {user.get('email', 'N/A')}")
        print(f"  🔧 Role: {user.get('role', 'N/A')}")
        print(f"  ✅ Verified: {user.get('verified', False)}")
        print(f"  🟢 Active: {user.get('active', False)}")
        print(f"  📍 Override Status: {user.get('workSchedule', {}).get('overrideStatus', 'N/A')}")
        print()
        
        return user
        
    except Exception as e:
        print(f"❌ Error checking technician status: {e}")
        return None

def test_technician_tasks_api():
    """Test what the technician tasks API would return for Sidharth"""
    print("🧪 Testing what technician tasks API should return...")
    
    try:
        # This simulates what the Lambda function does
        dynamodb = boto3.resource('dynamodb')
        service_requests_table = dynamodb.Table('aquachain-service-requests')
        
        sidharth_id = '31333d7a-7031-703b-2e21-966a49444222'
        
        # Query for active service requests (assigned or in_progress)
        response = service_requests_table.scan(
            FilterExpression='technicianId = :tech_id AND #status IN (:assigned, :in_progress)',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':tech_id': sidharth_id,
                ':assigned': 'assigned',
                ':in_progress': 'in_progress'
            }
        )
        
        active_tasks = response.get('Items', [])
        print(f"✅ API should return {len(active_tasks)} active tasks")
        
        # Transform to task format (like the Lambda does)
        tasks = []
        for sr in active_tasks:
            task = {
                'taskId': sr['requestId'],
                'serviceRequestId': sr['requestId'],
                'deviceId': sr.get('deviceId'),
                'consumerId': sr.get('consumerId'),
                'priority': sr.get('priority', 'normal'),
                'status': sr.get('status'),
                'location': sr.get('location'),
                'description': sr.get('description'),
                'assignedAt': sr.get('createdAt'),
                'dueDate': sr.get('dueDate')
            }
            tasks.append(task)
        
        print(f"📋 Tasks that should appear in dashboard:")
        for task in tasks:
            print(f"  🔧 Task: {task['taskId']}")
            print(f"     Status: {task['status']}")
            print(f"     Description: {task['description']}")
            print(f"     Priority: {task['priority']}")
            print()
        
        return tasks
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return []

def main():
    """Main function"""
    print("🚀 Checking Sidharth Lenin's Current Assignments")
    print("=" * 60)
    
    # Check all assignment sources
    orders = check_sidharth_in_orders()
    service_requests = check_sidharth_in_service_requests()
    user_status = check_sidharth_technician_status()
    api_tasks = test_technician_tasks_api()
    
    print("\n" + "=" * 60)
    print("📊 ASSIGNMENT SUMMARY")
    print("=" * 60)
    
    print(f"📋 Orders Assigned: {len(orders)}")
    print(f"🔧 Service Requests: {len(service_requests)}")
    print(f"👤 Technician Status: {'✅ VERIFIED' if user_status and user_status.get('verified') else '❌ NOT VERIFIED'}")
    print(f"🎯 Active Tasks (API): {len(api_tasks)}")
    
    print("\n🎯 DASHBOARD EXPECTATION:")
    if len(api_tasks) > 0:
        print(f"✅ Dashboard SHOULD show {len(api_tasks)} tasks")
        print("   If dashboard shows 'No tasks found', there's still an API issue")
    else:
        print("❌ Dashboard SHOULD show 'No tasks found'")
        print("   This is correct if no active tasks exist")
    
    print("\n🔍 ANALYSIS:")
    if len(orders) > 0 and len(service_requests) == 0:
        print("⚠️  ISSUE: Order assigned but no corresponding service request created")
        print("   Orders need service requests to show as tasks in technician dashboard")
    elif len(service_requests) > 0 and len(api_tasks) == 0:
        print("⚠️  ISSUE: Service requests exist but none are in 'assigned' or 'in_progress' status")
        print("   Only active tasks show in dashboard")
    elif len(api_tasks) > 0:
        print("✅ Tasks exist and should be visible in dashboard")
        print("   If not visible, check API Gateway routing and Lambda function")
    else:
        print("ℹ️  No active assignments - dashboard showing 'No tasks' is correct")

if __name__ == "__main__":
    main()