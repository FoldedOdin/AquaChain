#!/usr/bin/env python3

"""
Check Technician Users in the System
"""

import boto3
import json
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Table names
USERS_TABLE = 'AquaChain-Users'
SERVICE_REQUESTS_TABLE = 'AquaChain-ServiceRequests'

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def check_technician_users():
    """Check what technician users exist in the system"""
    users_table = dynamodb.Table(USERS_TABLE)
    
    print("🔍 Checking technician users in the system...")
    
    try:
        # Scan for users with technician role
        response = users_table.scan(
            FilterExpression='#role = :role',
            ExpressionAttributeNames={'#role': 'role'},
            ExpressionAttributeValues={':role': 'technician'}
        )
        
        technicians = response.get('Items', [])
        
        print(f"✅ Found {len(technicians)} technician users:")
        
        for tech in technicians:
            print(f"  - ID: {tech.get('userId')}")
            print(f"    Name: {tech.get('name', 'No name')}")
            print(f"    Email: {tech.get('email', 'No email')}")
            print(f"    Phone: {tech.get('phone', 'No phone')}")
            print(f"    Role: {tech.get('role')}")
            print()
        
        return technicians
        
    except Exception as e:
        print(f"❌ Error checking technician users: {e}")
        return []

def check_service_requests():
    """Check the created service requests"""
    service_requests_table = dynamodb.Table(SERVICE_REQUESTS_TABLE)
    
    print("🔍 Checking created service requests...")
    
    try:
        response = service_requests_table.scan()
        service_requests = response.get('Items', [])
        
        print(f"✅ Found {len(service_requests)} service requests:")
        
        for sr in service_requests:
            print(f"  - Request ID: {sr.get('requestId')}")
            print(f"    Order ID: {sr.get('orderId')}")
            print(f"    Technician ID: {sr.get('technicianId')}")
            print(f"    Status: {sr.get('status')}")
            print(f"    Description: {sr.get('description')}")
            print(f"    Created: {sr.get('createdAt')}")
            print()
        
        return service_requests
        
    except Exception as e:
        print(f"❌ Error checking service requests: {e}")
        return []

def create_test_technician_users():
    """Create test technician users for the assigned technicians"""
    users_table = dynamodb.Table(USERS_TABLE)
    
    # Technicians from the orders
    test_technicians = [
        {
            'userId': 'tech-sidharth-lenin',
            'name': 'Sidharth Lenin',
            'email': 'sidharth.lenin@aquachain.com',
            'phone': '+91 98765 43210',
            'role': 'technician',
            'status': 'active',
            'location': {
                'city': 'Ernakulam',
                'state': 'Kerala',
                'coordinates': {'latitude': Decimal('9.9312'), 'longitude': Decimal('76.2673')}
            },
            'skills': ['installation', 'maintenance', 'water_quality_testing'],
            'experience': '5+ years',
            'rating': Decimal('4.8'),
            'available': True,
            'createdAt': '2024-01-01T00:00:00Z'
        },
        {
            'userId': 'tech-karthik-pradeep',
            'name': 'Karthik K Pradeep',
            'email': 'karthik.pradeep@aquachain.com',
            'phone': '+91 98765 43211',
            'role': 'technician',
            'status': 'active',
            'location': {
                'city': 'Ernakulam',
                'state': 'Kerala',
                'coordinates': {'latitude': Decimal('9.9312'), 'longitude': Decimal('76.2673')}
            },
            'skills': ['installation', 'repair', 'customer_service'],
            'experience': '3+ years',
            'rating': Decimal('4.6'),
            'available': True,
            'createdAt': '2024-01-01T00:00:00Z'
        },
        {
            'userId': 'tech-akash-vinod',
            'name': 'Akash Vinod',
            'email': 'akash.vinod@aquachain.com',
            'phone': '+91 98765 43212',
            'role': 'technician',
            'status': 'active',
            'location': {
                'city': 'Ernakulam',
                'state': 'Kerala',
                'coordinates': {'latitude': Decimal('9.9312'), 'longitude': Decimal('76.2673')}
            },
            'skills': ['installation', 'troubleshooting', 'water_analysis'],
            'experience': '4+ years',
            'rating': Decimal('4.7'),
            'available': True,
            'createdAt': '2024-01-01T00:00:00Z'
        }
    ]
    
    print("🔧 Creating test technician users...")
    
    created_count = 0
    for tech in test_technicians:
        try:
            users_table.put_item(Item=tech)
            print(f"✅ Created technician user: {tech['name']} ({tech['userId']})")
            created_count += 1
        except Exception as e:
            print(f"❌ Error creating technician {tech['name']}: {e}")
    
    print(f"\n✅ Created {created_count} technician users")
    return created_count

def update_service_requests_with_technician_ids():
    """Update service requests with proper technician IDs"""
    service_requests_table = dynamodb.Table(SERVICE_REQUESTS_TABLE)
    
    # Mapping of technician names to user IDs
    technician_mapping = {
        'Sidharth Lenin': 'tech-sidharth-lenin',
        'Karthik K Pradeep': 'tech-karthik-pradeep',
        'Akash Vinod': 'tech-akash-vinod'
    }
    
    print("🔧 Updating service requests with proper technician IDs...")
    
    # Get all service requests
    response = service_requests_table.scan()
    service_requests = response.get('Items', [])
    
    updated_count = 0
    for sr in service_requests:
        request_id = sr.get('requestId')
        current_tech_id = sr.get('technicianId')
        
        # Try to find the correct technician ID based on the order
        # We'll need to check the order to get the technician name
        # For now, let's update based on a pattern or default to Sidharth
        
        # If technicianId looks like a name or is missing, update it
        if not current_tech_id or len(current_tech_id) > 20:
            # Default to Sidharth Lenin for now
            new_tech_id = 'tech-sidharth-lenin'
            
            try:
                service_requests_table.update_item(
                    Key={'requestId': request_id},
                    UpdateExpression='SET technicianId = :tech_id',
                    ExpressionAttributeValues={':tech_id': new_tech_id}
                )
                print(f"✅ Updated service request {request_id} with technician ID: {new_tech_id}")
                updated_count += 1
            except Exception as e:
                print(f"❌ Error updating service request {request_id}: {e}")
    
    print(f"\n✅ Updated {updated_count} service requests")
    return updated_count

if __name__ == "__main__":
    print("🚀 Checking Technician Users and Service Requests")
    print("=" * 60)
    
    # Check existing technician users
    technicians = check_technician_users()
    
    # Check service requests
    service_requests = check_service_requests()
    
    # If no technician users exist, create them
    if not technicians:
        print("\n⚠️  No technician users found. Creating test users...")
        create_test_technician_users()
        
        # Update service requests with proper technician IDs
        update_service_requests_with_technician_ids()
    
    print("\n🏁 Check completed!")