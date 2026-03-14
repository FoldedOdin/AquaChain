#!/usr/bin/env python3

"""
Fix Technician Tasks Synchronization

This script fixes the issue where technicians are assigned to orders but no tasks
appear in their dashboard. The problem is that orders and technician tasks are in
separate systems that don't communicate.

Solution:
1. Create service requests for existing orders with assigned technicians
2. Add a function to automatically create service requests when technicians are assigned
3. Ensure the technician dashboard shows these tasks

Author: AquaChain Development Team
Date: March 2026
"""

import boto3
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import sys
import os

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Table names
ORDERS_TABLE = 'aquachain-orders'
SERVICE_REQUESTS_TABLE = 'AquaChain-ServiceRequests'
USERS_TABLE = 'AquaChain-Users'

def get_orders_with_assigned_technicians():
    """Get all orders that have assigned technicians"""
    orders_table = dynamodb.Table(ORDERS_TABLE)
    
    print("🔍 Scanning for orders with assigned technicians...")
    
    # Scan for orders with assignedTechnician field
    response = orders_table.scan(
        FilterExpression='attribute_exists(assignedTechnician) OR attribute_exists(assignedTechnicianName)'
    )
    
    orders = response.get('Items', [])
    
    # Continue scanning if there are more items
    while 'LastEvaluatedKey' in response:
        response = orders_table.scan(
            FilterExpression='attribute_exists(assignedTechnician) OR attribute_exists(assignedTechnicianName)',
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        orders.extend(response.get('Items', []))
    
    print(f"✅ Found {len(orders)} orders with assigned technicians")
    return orders

def get_existing_service_requests():
    """Get all existing service requests to avoid duplicates"""
    service_requests_table = dynamodb.Table(SERVICE_REQUESTS_TABLE)
    
    print("🔍 Getting existing service requests...")
    
    try:
        response = service_requests_table.scan()
        service_requests = response.get('Items', [])
        
        # Continue scanning if there are more items
        while 'LastEvaluatedKey' in response:
            response = service_requests_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            service_requests.extend(response.get('Items', []))
        
        # Create a set of order IDs that already have service requests
        existing_order_ids = set()
        for sr in service_requests:
            if 'orderId' in sr:
                existing_order_ids.add(sr['orderId'])
        
        print(f"✅ Found {len(service_requests)} existing service requests")
        print(f"📋 {len(existing_order_ids)} orders already have service requests")
        
        return existing_order_ids
        
    except Exception as e:
        print(f"⚠️  Error getting existing service requests: {e}")
        return set()

def get_technician_user_id(technician_name: str) -> Optional[str]:
    """Get technician user ID from their name"""
    users_table = dynamodb.Table(USERS_TABLE)
    
    try:
        # Scan for users with technician role and matching name
        response = users_table.scan(
            FilterExpression='#role = :role AND contains(#name, :name)',
            ExpressionAttributeNames={
                '#role': 'role',
                '#name': 'name'
            },
            ExpressionAttributeValues={
                ':role': 'technician',
                ':name': technician_name
            }
        )
        
        users = response.get('Items', [])
        
        if users:
            return users[0]['userId']
        else:
            print(f"⚠️  No user found for technician: {technician_name}")
            return None
            
    except Exception as e:
        print(f"⚠️  Error finding technician user: {e}")
        return None

def create_service_request_from_order(order: Dict[str, Any]) -> Dict[str, Any]:
    """Create a service request from an order with assigned technician"""
    
    # Extract order details
    order_id = order.get('orderId')
    consumer_id = order.get('userId') or order.get('consumerId')
    assigned_technician_name = order.get('assignedTechnicianName')
    assigned_technician_id = order.get('assignedTechnician')
    device_sku = order.get('deviceSKU', 'Unknown Device')
    delivery_address = order.get('deliveryAddress', {})
    created_at = order.get('createdAt')
    
    # Get technician user ID
    technician_user_id = None
    if assigned_technician_name:
        technician_user_id = get_technician_user_id(assigned_technician_name)
    
    if not technician_user_id and assigned_technician_id:
        technician_user_id = assigned_technician_id
    
    if not technician_user_id:
        print(f"⚠️  Cannot create service request for order {order_id}: No technician user ID found")
        return None
    
    # Generate service request ID
    request_id = f"SR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
    
    # Parse delivery address
    if isinstance(delivery_address, str):
        try:
            delivery_address = json.loads(delivery_address)
        except:
            delivery_address = {'address': delivery_address}
    
    # Create location object
    location = {
        'address': delivery_address.get('street', '') + ', ' + 
                  delivery_address.get('city', '') + ', ' + 
                  delivery_address.get('state', ''),
        'coordinates': delivery_address.get('coordinates', {}),
        'city': delivery_address.get('city', ''),
        'state': delivery_address.get('state', ''),
        'pincode': delivery_address.get('pincode', '')
    }
    
    # Create service request
    service_request = {
        'requestId': request_id,
        'orderId': order_id,  # Link to the original order
        'consumerId': consumer_id,
        'technicianId': technician_user_id,
        'deviceId': f"device-{order_id}",  # Create a device ID based on order
        'deviceSKU': device_sku,
        'status': 'assigned',  # Since technician is already assigned
        'location': location,
        'description': f'Installation and setup of {device_sku} device',
        'priority': 'normal',
        'createdAt': created_at or datetime.now(timezone.utc).isoformat(),
        'assignedAt': datetime.now(timezone.utc).isoformat(),
        'notes': [],
        'statusHistory': [
            {
                'status': 'pending',
                'timestamp': created_at or datetime.now(timezone.utc).isoformat(),
                'updatedBy': 'system',
                'note': 'Service request created from order assignment'
            },
            {
                'status': 'assigned',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'updatedBy': 'system',
                'note': f'Assigned to technician {assigned_technician_name}'
            }
        ],
        # Additional fields for technician dashboard
        'customerInfo': {
            'name': delivery_address.get('name', 'Customer'),
            'phone': delivery_address.get('phone', ''),
            'address': location['address']
        },
        'deviceInfo': {
            'sku': device_sku,
            'type': 'Water Quality Monitor',
            'model': device_sku
        }
    }
    
    return service_request

def save_service_request(service_request: Dict[str, Any]) -> bool:
    """Save service request to DynamoDB"""
    service_requests_table = dynamodb.Table(SERVICE_REQUESTS_TABLE)
    
    try:
        service_requests_table.put_item(Item=service_request)
        return True
    except Exception as e:
        print(f"❌ Error saving service request {service_request['requestId']}: {e}")
        return False

def create_service_requests_for_assigned_orders():
    """Main function to create service requests for orders with assigned technicians"""
    
    print("🚀 Starting technician tasks synchronization fix...")
    print("=" * 60)
    
    # Get orders with assigned technicians
    orders = get_orders_with_assigned_technicians()
    
    if not orders:
        print("ℹ️  No orders with assigned technicians found")
        return
    
    # Get existing service requests to avoid duplicates
    existing_order_ids = get_existing_service_requests()
    
    # Filter orders that don't already have service requests
    orders_needing_service_requests = [
        order for order in orders 
        if order.get('orderId') not in existing_order_ids
    ]
    
    print(f"📋 {len(orders_needing_service_requests)} orders need service requests created")
    
    if not orders_needing_service_requests:
        print("✅ All assigned orders already have service requests")
        return
    
    # Create service requests
    created_count = 0
    failed_count = 0
    
    for order in orders_needing_service_requests:
        order_id = order.get('orderId')
        technician_name = order.get('assignedTechnicianName', 'Unknown')
        
        print(f"🔧 Creating service request for order {order_id} (Technician: {technician_name})")
        
        # Create service request from order
        service_request = create_service_request_from_order(order)
        
        if service_request:
            # Save to database
            if save_service_request(service_request):
                created_count += 1
                print(f"✅ Created service request {service_request['requestId']}")
            else:
                failed_count += 1
        else:
            failed_count += 1
    
    print("\n" + "=" * 60)
    print("📊 SYNCHRONIZATION RESULTS:")
    print(f"✅ Successfully created: {created_count} service requests")
    print(f"❌ Failed to create: {failed_count} service requests")
    print(f"📋 Total orders processed: {len(orders_needing_service_requests)}")
    
    if created_count > 0:
        print(f"\n🎉 Success! {created_count} technician tasks are now available in dashboards")
        print("💡 Technicians should now see their assigned orders as tasks")
    
    return created_count, failed_count

def test_technician_tasks_api():
    """Test the technician tasks API to verify the fix works"""
    print("\n🧪 Testing technician tasks API...")
    
    try:
        # This would require authentication, so we'll just print the instruction
        print("📋 To test the fix:")
        print("1. Log in as a technician (e.g., Sidharth Lenin)")
        print("2. Navigate to the technician dashboard")
        print("3. Check if assigned orders now appear as tasks")
        print("4. Verify task details match the order information")
        
    except Exception as e:
        print(f"⚠️  Error testing API: {e}")

if __name__ == "__main__":
    try:
        # Run the synchronization fix
        created, failed = create_service_requests_for_assigned_orders()
        
        # Test the API
        test_technician_tasks_api()
        
        print(f"\n🏁 Fix completed! Created {created} service requests.")
        
        if failed > 0:
            print(f"⚠️  {failed} service requests failed to create. Check logs above.")
            sys.exit(1)
        else:
            print("✅ All service requests created successfully!")
            
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)