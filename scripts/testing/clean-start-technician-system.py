#!/usr/bin/env python3
"""
Clean Start - Technician System Reset

This script completely cleans up and resets the technician assignment system:
1. Remove all orders and unassign technicians
2. Clear all service requests
3. Reset technician availability
4. Create a fresh test scenario
"""

import boto3
import json
from datetime import datetime, timedelta
import uuid

def cleanup_orders():
    """Remove all orders and unassign technicians"""
    try:
        dynamodb = boto3.resource('dynamodb')
        orders_table = dynamodb.Table('aquachain-orders')
        
        print("🧹 Cleaning up orders...")
        
        # Scan all orders
        response = orders_table.scan()
        orders = response.get('Items', [])
        
        print(f"   Found {len(orders)} orders to clean up")
        
        for order in orders:
            order_id = order['orderId']
            print(f"   🗑️  Deleting order: {order_id}")
            
            # Delete the order
            orders_table.delete_item(Key={'orderId': order_id})
        
        print(f"✅ Cleaned up {len(orders)} orders")
        return len(orders)
        
    except Exception as e:
        print(f"❌ Error cleaning up orders: {e}")
        return 0

def cleanup_service_requests():
    """Remove all service requests"""
    try:
        dynamodb = boto3.resource('dynamodb')
        service_requests_table = dynamodb.Table('aquachain-service-requests')
        
        print("🧹 Cleaning up service requests...")
        
        # Scan all service requests
        response = service_requests_table.scan()
        service_requests = response.get('Items', [])
        
        print(f"   Found {len(service_requests)} service requests to clean up")
        
        for sr in service_requests:
            request_id = sr['requestId']
            print(f"   🗑️  Deleting service request: {request_id}")
            
            # Delete the service request
            service_requests_table.delete_item(Key={'requestId': request_id})
        
        print(f"✅ Cleaned up {len(service_requests)} service requests")
        return len(service_requests)
        
    except Exception as e:
        print(f"❌ Error cleaning up service requests: {e}")
        return 0

def reset_technician_availability():
    """Reset all technicians to available status"""
    try:
        dynamodb = boto3.resource('dynamodb')
        users_table = dynamodb.Table('AquaChain-Users')
        
        print("🔄 Resetting technician availability...")
        
        # Get all technicians
        response = users_table.scan(
            FilterExpression='#role = :role',
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={':role': 'technician'}
        )
        
        technicians = response.get('Items', [])
        print(f"   Found {len(technicians)} technicians to reset")
        
        for tech in technicians:
            user_id = tech['userId']
            name = f"{tech.get('profile', {}).get('firstName', 'Unknown')} {tech.get('profile', {}).get('lastName', '')}"
            
            print(f"   🔄 Resetting technician: {name} ({user_id})")
            
            # Update technician to available status
            users_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET workSchedule.overrideStatus = :status, workSchedule.currentTask = :task',
                ExpressionAttributeValues={
                    ':status': 'available',
                    ':task': None
                }
            )
        
        print(f"✅ Reset {len(technicians)} technicians to available")
        return technicians
        
    except Exception as e:
        print(f"❌ Error resetting technicians: {e}")
        return []

def create_fresh_test_scenario():
    """Create a fresh test scenario with one order and service request"""
    try:
        dynamodb = boto3.resource('dynamodb')
        
        print("🆕 Creating fresh test scenario...")
        
        # Get Sidharth's details
        sidharth_id = '31333d7a-7031-703b-2e21-966a49444222'
        
        # Create a new test order
        orders_table = dynamodb.Table('aquachain-orders')
        
        order_id = f"ord_{int(datetime.now().timestamp())}"
        
        new_order = {
            'orderId': order_id,
            'customerId': '51a3ed4a-c0b1-70e8-a7d7-19d7ca035fe0',  # Karthik's ID
            'customerName': 'Karthik K Pradeep',
            'customerEmail': 'karthikkpradeep123@gmail.com',
            'customerPhone': '+918547613649',
            'status': 'PLACED',
            'orderAmount': 5499,
            'paymentMethod': 'ONLINE',
            'paymentStatus': 'COMPLETED',
            'deviceInfo': {
                'model': 'AquaChain Pro',
                'serialNumber': f'SN-{order_id}',
                'deviceId': f'device-{uuid.uuid4().hex[:8]}'
            },
            'shippingAddress': {
                'address': '73/1276, Ernakulam, Kerala, 682012',
                'latitude': 10.0261,
                'longitude': 76.3125
            },
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat()
        }
        
        print(f"   📦 Creating order: {order_id}")
        orders_table.put_item(Item=new_order)
        
        # Create a corresponding service request
        service_requests_table = dynamodb.Table('aquachain-service-requests')
        
        service_request_id = f"SR-{uuid.uuid4().hex[:8].upper()}"
        
        new_service_request = {
            'requestId': service_request_id,
            'orderId': order_id,
            'customerId': '51a3ed4a-c0b1-70e8-a7d7-19d7ca035fe0',
            'deviceId': new_order['deviceInfo']['deviceId'],
            'technicianId': sidharth_id,  # Assign to Sidharth
            'status': 'assigned',
            'priority': 'normal',
            'description': 'Device installation and setup - Fresh test scenario',
            'location': {
                'address': '73/1276, Ernakulam, Kerala, 682012',
                'latitude': 10.0261,
                'longitude': 76.3125
            },
            'customerInfo': {
                'name': 'Karthik K Pradeep',
                'email': 'karthikkpradeep123@gmail.com',
                'phone': '+918547613649'
            },
            'deviceInfo': {
                'model': 'AquaChain Pro',
                'serialNumber': new_order['deviceInfo']['serialNumber']
            },
            'createdAt': datetime.now().isoformat(),
            'dueDate': (datetime.now() + timedelta(days=1)).isoformat(),
            'estimatedArrival': (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        print(f"   🔧 Creating service request: {service_request_id}")
        service_requests_table.put_item(Item=new_service_request)
        
        # Update the order to show technician assignment
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET assignedTechnician = :tech_id, assignedTechnicianName = :tech_name, technicianAssignment = :assignment, #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':tech_id': sidharth_id,
                ':tech_name': 'Sidharth Lenin',
                ':assignment': {
                    'technicianId': sidharth_id,
                    'technicianName': 'Sidharth Lenin',
                    'technicianPhone': '+911234567890',
                    'assignedAt': datetime.now().isoformat(),
                    'status': 'assigned'
                },
                ':status': 'TECHNICIAN_ASSIGNED'
            }
        )
        
        print(f"✅ Created fresh test scenario:")
        print(f"   📦 Order: {order_id}")
        print(f"   🔧 Service Request: {service_request_id}")
        print(f"   👤 Assigned to: Sidharth Lenin")
        
        return {
            'order': new_order,
            'service_request': new_service_request
        }
        
    except Exception as e:
        print(f"❌ Error creating test scenario: {e}")
        return None

def verify_clean_state():
    """Verify the system is in a clean state"""
    try:
        dynamodb = boto3.resource('dynamodb')
        
        print("🔍 Verifying clean state...")
        
        # Check orders
        orders_table = dynamodb.Table('aquachain-orders')
        orders_response = orders_table.scan()
        orders_count = len(orders_response.get('Items', []))
        
        # Check service requests
        service_requests_table = dynamodb.Table('aquachain-service-requests')
        sr_response = service_requests_table.scan()
        sr_count = len(sr_response.get('Items', []))
        
        # Check technicians
        users_table = dynamodb.Table('AquaChain-Users')
        tech_response = users_table.scan(
            FilterExpression='#role = :role',
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={':role': 'technician'}
        )
        tech_count = len(tech_response.get('Items', []))
        
        print(f"✅ Current state:")
        print(f"   📦 Orders: {orders_count}")
        print(f"   🔧 Service Requests: {sr_count}")
        print(f"   👤 Technicians: {tech_count}")
        
        return {
            'orders': orders_count,
            'service_requests': sr_count,
            'technicians': tech_count
        }
        
    except Exception as e:
        print(f"❌ Error verifying state: {e}")
        return {}

def main():
    """Main cleanup and reset function"""
    print("🚀 Clean Start - Technician System Reset")
    print("=" * 60)
    
    # Step 1: Cleanup existing data
    print("\n1. CLEANUP PHASE")
    print("-" * 30)
    
    orders_cleaned = cleanup_orders()
    sr_cleaned = cleanup_service_requests()
    technicians_reset = reset_technician_availability()
    
    # Step 2: Verify clean state
    print("\n2. VERIFICATION PHASE")
    print("-" * 30)
    
    clean_state = verify_clean_state()
    
    # Step 3: Create fresh test scenario
    print("\n3. FRESH START PHASE")
    print("-" * 30)
    
    test_scenario = create_fresh_test_scenario()
    
    # Step 4: Final verification
    print("\n4. FINAL VERIFICATION")
    print("-" * 30)
    
    final_state = verify_clean_state()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 CLEANUP SUMMARY")
    print("=" * 60)
    
    print(f"🗑️  Cleaned up:")
    print(f"   📦 Orders: {orders_cleaned}")
    print(f"   🔧 Service Requests: {sr_cleaned}")
    print(f"   👤 Technicians Reset: {len(technicians_reset)}")
    
    print(f"\n🆕 Fresh state:")
    print(f"   📦 Orders: {final_state.get('orders', 0)}")
    print(f"   🔧 Service Requests: {final_state.get('service_requests', 0)}")
    print(f"   👤 Technicians: {final_state.get('technicians', 0)}")
    
    if test_scenario:
        print(f"\n✅ SYSTEM RESET COMPLETE!")
        print(f"   🎯 Fresh test scenario created")
        print(f"   👤 Sidharth Lenin has 1 new task assigned")
        print(f"   📱 Dashboard should now show 1 task")
    else:
        print(f"\n❌ SYSTEM RESET INCOMPLETE")
        print(f"   🔧 Manual intervention may be required")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"1. Test the technician dashboard")
    print(f"2. Verify Sidharth can see the new task")
    print(f"3. Check API authentication")
    print(f"4. Monitor Lambda function logs")

if __name__ == "__main__":
    main()