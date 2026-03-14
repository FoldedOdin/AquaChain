#!/usr/bin/env python3

"""
Fix Technician ID Mapping

This script fixes the technician ID mapping between service requests and actual user IDs.
The service requests were created with generated technician IDs that don't match the real user IDs.

Author: AquaChain Development Team
Date: March 2026
"""

import boto3
import json
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Table names
USERS_TABLE = 'AquaChain-Users'
SERVICE_REQUESTS_TABLE = 'aquachain-service-requests'
ORDERS_TABLE = 'aquachain-orders'

def get_technician_users():
    """Get all technician users from the users table"""
    users_table = dynamodb.Table(USERS_TABLE)
    
    print("🔍 Getting technician users...")
    
    try:
        response = users_table.scan(
            FilterExpression='#role = :role',
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={':role': 'technician'}
        )
        
        technicians = response.get('Items', [])
        
        print(f"✅ Found {len(technicians)} technician users:")
        for tech in technicians:
            print(f"  - ID: {tech.get('userId')}")
            print(f"    Email: {tech.get('email', 'No email')}")
            print()
        
        return technicians
        
    except Exception as e:
        print(f"❌ Error getting technician users: {e}")
        return []

def get_orders_with_technicians():
    """Get orders with assigned technicians to understand the mapping"""
    orders_table = dynamodb.Table(ORDERS_TABLE)
    
    print("🔍 Getting orders with assigned technicians...")
    
    try:
        response = orders_table.scan(
            FilterExpression='attribute_exists(assignedTechnician) OR attribute_exists(assignedTechnicianName)'
        )
        
        orders = response.get('Items', [])
        
        print(f"✅ Found {len(orders)} orders with technicians:")
        for order in orders:
            print(f"  - Order: {order.get('orderId')}")
            print(f"    Technician Name: {order.get('assignedTechnicianName', 'N/A')}")
            print(f"    Technician ID: {order.get('assignedTechnician', 'N/A')}")
            print()
        
        return orders
        
    except Exception as e:
        print(f"❌ Error getting orders: {e}")
        return []

def get_service_requests():
    """Get all service requests"""
    service_requests_table = dynamodb.Table(SERVICE_REQUESTS_TABLE)
    
    print("🔍 Getting service requests...")
    
    try:
        response = service_requests_table.scan()
        service_requests = response.get('Items', [])
        
        print(f"✅ Found {len(service_requests)} service requests:")
        for sr in service_requests:
            print(f"  - Request: {sr.get('requestId')}")
            print(f"    Order: {sr.get('orderId')}")
            print(f"    Technician ID: {sr.get('technicianId')}")
            print(f"    Status: {sr.get('status')}")
            print()
        
        return service_requests
        
    except Exception as e:
        print(f"❌ Error getting service requests: {e}")
        return []

def create_technician_mapping(technicians, orders):
    """Create mapping between technician names and user IDs"""
    
    # Extract emails from technician users
    email_to_userid = {}
    for tech in technicians:
        email = tech.get('email', '').lower()
        user_id = tech.get('userId')
        if email and user_id:
            email_to_userid[email] = user_id
    
    print("📋 Email to User ID mapping:")
    for email, user_id in email_to_userid.items():
        print(f"  {email} → {user_id}")
    
    # Based on the emails we saw, create the mapping
    # leninat259@gmail.com → Sidharth Lenin
    # karthiikkpradeep897@gmail.com → Karthik K Pradeep
    
    name_to_userid = {}
    
    # Map based on known emails
    if 'leninat259@gmail.com' in email_to_userid:
        name_to_userid['Sidharth Lenin'] = email_to_userid['leninat259@gmail.com']
    
    if 'karthiikkpradeep897@gmail.com' in email_to_userid:
        name_to_userid['Karthik K Pradeep'] = email_to_userid['karthiikkpradeep897@gmail.com']
    
    print("\n📋 Name to User ID mapping:")
    for name, user_id in name_to_userid.items():
        print(f"  {name} → {user_id}")
    
    return name_to_userid

def update_service_requests_with_correct_technician_ids(service_requests, orders, name_to_userid):
    """Update service requests with correct technician IDs"""
    service_requests_table = dynamodb.Table(SERVICE_REQUESTS_TABLE)
    
    # Create order ID to technician name mapping
    order_to_technician = {}
    for order in orders:
        order_id = order.get('orderId')
        tech_name = order.get('assignedTechnicianName')
        if order_id and tech_name:
            order_to_technician[order_id] = tech_name
    
    print("🔧 Updating service requests with correct technician IDs...")
    
    updated_count = 0
    for sr in service_requests:
        request_id = sr.get('requestId')
        order_id = sr.get('orderId')
        current_tech_id = sr.get('technicianId')
        
        # Get technician name from order
        tech_name = order_to_technician.get(order_id)
        
        if tech_name and tech_name in name_to_userid:
            correct_tech_id = name_to_userid[tech_name]
            
            if current_tech_id != correct_tech_id:
                try:
                    service_requests_table.update_item(
                        Key={'requestId': request_id},
                        UpdateExpression='SET technicianId = :tech_id',
                        ExpressionAttributeValues={':tech_id': correct_tech_id}
                    )
                    print(f"✅ Updated {request_id}: {current_tech_id} → {correct_tech_id} ({tech_name})")
                    updated_count += 1
                except Exception as e:
                    print(f"❌ Error updating {request_id}: {e}")
            else:
                print(f"ℹ️  {request_id} already has correct technician ID")
        else:
            print(f"⚠️  Cannot map technician for {request_id} (order: {order_id}, tech: {tech_name})")
    
    print(f"\n✅ Updated {updated_count} service requests")
    return updated_count

def update_technician_user_profiles():
    """Update technician user profiles with proper names"""
    users_table = dynamodb.Table(USERS_TABLE)
    
    # Known mappings based on emails
    email_to_name = {
        'leninat259@gmail.com': 'Sidharth Lenin',
        'karthiikkpradeep897@gmail.com': 'Karthik K Pradeep'
    }
    
    print("🔧 Updating technician user profiles...")
    
    # Get technician users
    response = users_table.scan(
        FilterExpression='#role = :role',
        ExpressionAttributeNames={'#role': 'role'},
        ExpressionAttributeValues={':role': 'technician'}
    )
    
    technicians = response.get('Items', [])
    updated_count = 0
    
    for tech in technicians:
        user_id = tech.get('userId')
        email = tech.get('email', '').lower()
        current_name = tech.get('name', '')
        
        if email in email_to_name and not current_name:
            new_name = email_to_name[email]
            
            try:
                users_table.update_item(
                    Key={'userId': user_id},
                    UpdateExpression='SET #name = :name, phone = :phone, available = :available',
                    ExpressionAttributeNames={'#name': 'name'},
                    ExpressionAttributeValues={
                        ':name': new_name,
                        ':phone': '+91 98765 43210',  # Default phone
                        ':available': True
                    }
                )
                print(f"✅ Updated user {user_id}: Added name '{new_name}'")
                updated_count += 1
            except Exception as e:
                print(f"❌ Error updating user {user_id}: {e}")
    
    print(f"\n✅ Updated {updated_count} technician profiles")
    return updated_count

def main():
    """Main function to fix technician ID mapping"""
    
    print("🚀 Starting Technician ID Mapping Fix...")
    print("=" * 60)
    
    # Get data
    technicians = get_technician_users()
    orders = get_orders_with_technicians()
    service_requests = get_service_requests()
    
    if not technicians:
        print("❌ No technician users found")
        return
    
    if not service_requests:
        print("❌ No service requests found")
        return
    
    # Update technician user profiles first
    update_technician_user_profiles()
    
    # Create mapping
    name_to_userid = create_technician_mapping(technicians, orders)
    
    if not name_to_userid:
        print("❌ Could not create technician mapping")
        return
    
    # Update service requests
    updated_count = update_service_requests_with_correct_technician_ids(
        service_requests, orders, name_to_userid
    )
    
    print("\n" + "=" * 60)
    print("📊 MAPPING FIX RESULTS:")
    print(f"✅ Updated {updated_count} service requests")
    print("💡 Technicians should now see their tasks in the dashboard")
    
    print("\n🧪 To test the fix:")
    print("1. Log in as Sidharth Lenin (leninat259@gmail.com)")
    print("2. Navigate to technician dashboard")
    print("3. Check if assigned orders appear as tasks")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()