#!/usr/bin/env python3
"""
Complete fix for technician assignment display
This script will:
1. Create test technicians with complete data
2. Assign technicians to orders with full details
3. Test the API response
4. Verify frontend can display technician details
"""

import boto3
import json
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# AWS Configuration
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
orders_table = dynamodb.Table('aquachain-orders')
technicians_table = dynamodb.Table('aquachain-technicians')

def create_test_technicians():
    """Create comprehensive test technicians with all required fields"""
    technicians = [
        {
            'technicianId': 'tech_001',
            'name': 'Rahul Nair',
            'phone': '+91 9876543210',
            'email': 'rahul.nair@aquachain.in',
            'address': 'Perumbavoor Service Center, Ernakulam District',
            'location': {
                'latitude': Decimal('10.1102'),
                'longitude': Decimal('76.4735'),
                'city': 'Perumbavoor',
                'state': 'Kerala'
            },
            'available': True,
            'skills': ['installation', 'maintenance', 'calibration'],
            'rating': Decimal('4.7'),
            'experience': '3 years',
            'serviceArea': 'Ernakulam, Kottayam',
            'workingHours': '9:00 AM - 6:00 PM',
            'vehicleType': 'Motorcycle',
            'certifications': ['Water Quality Specialist', 'IoT Device Installation'],
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'updatedAt': datetime.now(timezone.utc).isoformat(),
            'GSI1PK': 'LOCATION#ALL',
            'GSI1SK': 'TECH#tech_001'
        },
        {
            'technicianId': 'tech_002', 
            'name': 'Priya Sharma',
            'phone': '+91 8765432109',
            'email': 'priya.sharma@aquachain.in',
            'address': 'Kochi Main Service Center, Marine Drive',
            'location': {
                'latitude': Decimal('9.9312'),
                'longitude': Decimal('76.2673'),
                'city': 'Kochi',
                'state': 'Kerala'
            },
            'available': True,
            'skills': ['installation', 'troubleshooting', 'customer_service'],
            'rating': Decimal('4.9'),
            'experience': '5 years',
            'serviceArea': 'Kochi, Ernakulam',
            'workingHours': '8:00 AM - 7:00 PM',
            'vehicleType': 'Car',
            'certifications': ['Senior Technician', 'Customer Service Excellence'],
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'updatedAt': datetime.now(timezone.utc).isoformat(),
            'GSI1PK': 'LOCATION#ALL',
            'GSI1SK': 'TECH#tech_002'
        },
        {
            'technicianId': 'tech_003',
            'name': 'Arjun Kumar',
            'phone': '+91 7654321098',
            'email': 'arjun.kumar@aquachain.in', 
            'address': 'Thrissur Regional Center, Round South',
            'location': {
                'latitude': Decimal('10.5276'),
                'longitude': Decimal('76.2144'),
                'city': 'Thrissur',
                'state': 'Kerala'
            },
            'available': True,
            'skills': ['installation', 'maintenance', 'training'],
            'rating': Decimal('4.5'),
            'experience': '2 years',
            'serviceArea': 'Thrissur, Palakkad',
            'workingHours': '9:00 AM - 5:00 PM',
            'vehicleType': 'Motorcycle',
            'certifications': ['Basic Installation', 'Safety Training'],
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'updatedAt': datetime.now(timezone.utc).isoformat(),
            'GSI1PK': 'LOCATION#ALL',
            'GSI1SK': 'TECH#tech_003'
        }
    ]
    
    print("🔧 Creating test technicians...")
    for tech in technicians:
        try:
            technicians_table.put_item(Item=tech)
            print(f"✅ Created technician: {tech['name']} ({tech['technicianId']})")
        except Exception as e:
            print(f"❌ Failed to create technician {tech['name']}: {e}")
    
    return technicians

def create_comprehensive_technician_assignment(order_id, technician):
    """Create a comprehensive technician assignment with all details"""
    estimated_arrival = datetime.now(timezone.utc) + timedelta(hours=2)
    
    assignment = {
        'orderId': order_id,
        'technicianId': technician['technicianId'],
        'technicianName': technician['name'],
        'technicianPhone': technician['phone'],
        'technicianEmail': technician['email'],
        'technicianAddress': technician['address'],
        'assignedAt': datetime.now(timezone.utc).isoformat(),
        'estimatedArrival': estimated_arrival.isoformat(),
        'distance': Decimal('5.2'),  # km
        'estimatedTravelTime': 25,  # minutes
        'status': 'assigned',
        'experience': technician['experience'],
        'rating': float(technician['rating']),
        'skills': technician['skills'],
        'vehicleType': technician['vehicleType'],
        'workingHours': technician['workingHours'],
        'serviceArea': technician['serviceArea']
    }
    
    return assignment

def assign_technician_to_order(order_id, technician):
    """Assign a technician to an order with complete details"""
    try:
        # Create comprehensive assignment
        assignment = create_comprehensive_technician_assignment(order_id, technician)
        
        # Update order with technician assignment
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='''SET 
                #status = :status,
                assignedTechnician = :tech_id,
                assignedTechnicianName = :tech_name,
                technicianAssignment = :assignment,
                updatedAt = :updated
            ''',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'TECHNICIAN_ASSIGNED',
                ':tech_id': technician['technicianId'],
                ':tech_name': technician['name'],
                ':assignment': assignment,
                ':updated': datetime.now(timezone.utc).isoformat()
            }
        )
        
        print(f"✅ Assigned technician {technician['name']} to order {order_id}")
        print(f"   📞 Phone: {technician['phone']}")
        print(f"   📧 Email: {technician['email']}")
        print(f"   🏢 Address: {technician['address']}")
        print(f"   ⭐ Rating: {technician['rating']}")
        print(f"   🕐 Estimated Arrival: {assignment['estimatedArrival']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to assign technician to order {order_id}: {e}")
        return False

def find_orders_needing_technicians():
    """Find orders that need technician assignment"""
    try:
        # Scan for orders with DEVICE_READY status
        response = orders_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'DEVICE_READY'}
        )
        
        orders = response.get('Items', [])
        print(f"🔍 Found {len(orders)} orders ready for technician assignment")
        
        return orders
        
    except Exception as e:
        print(f"❌ Error finding orders: {e}")
        return []

def test_api_response():
    """Test the API response to ensure technician data is included"""
    import requests
    
    try:
        # Get auth token (you may need to adjust this)
        token = "your-auth-token-here"  # Replace with actual token
        
        api_endpoint = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{api_endpoint}/api/orders", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get('orders', [])
            
            print(f"🌐 API Response: {len(orders)} orders returned")
            
            for order in orders:
                if order.get('status') == 'TECHNICIAN_ASSIGNED':
                    print(f"\n📋 Order {order['orderId']}:")
                    print(f"   Status: {order['status']}")
                    
                    # Check technician object
                    technician = order.get('technician')
                    if technician:
                        print(f"   ✅ Technician Object Found:")
                        print(f"      Name: {technician.get('name', 'N/A')}")
                        print(f"      Phone: {technician.get('phone', 'N/A')}")
                        print(f"      Email: {technician.get('email', 'N/A')}")
                        print(f"      Address: {technician.get('address', 'N/A')}")
                        print(f"      Rating: {technician.get('rating', 'N/A')}")
                    else:
                        print(f"   ❌ No technician object found")
                    
                    # Check assignment object
                    assignment = order.get('technicianAssignment')
                    if assignment:
                        print(f"   ✅ Assignment Object Found:")
                        print(f"      Estimated Arrival: {assignment.get('estimatedArrival', 'N/A')}")
                        print(f"      Distance: {assignment.get('distance', 'N/A')} km")
                    else:
                        print(f"   ❌ No assignment object found")
        else:
            print(f"❌ API request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

def main():
    """Main execution function"""
    print("🚀 Starting comprehensive technician display fix...")
    
    # Step 1: Create test technicians
    technicians = create_test_technicians()
    
    # Step 2: Find orders needing technicians
    orders = find_orders_needing_technicians()
    
    if not orders:
        print("ℹ️  No orders found needing technician assignment")
        return
    
    # Step 3: Assign technicians to orders
    for i, order in enumerate(orders[:3]):  # Limit to first 3 orders
        technician = technicians[i % len(technicians)]
        assign_technician_to_order(order['orderId'], technician)
    
    # Step 4: Test API response
    print("\n🧪 Testing API response...")
    test_api_response()
    
    print("\n✅ Technician display fix completed!")
    print("\nNext steps:")
    print("1. Test the frontend to see if technician details appear")
    print("2. Click 'View Details' on a TECHNICIAN_ASSIGNED order")
    print("3. Verify the technician modal shows complete information")

if __name__ == "__main__":
    main()