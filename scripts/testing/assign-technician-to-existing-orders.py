#!/usr/bin/env python3
"""
Assign technicians to existing orders for testing
"""

import boto3
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# AWS Configuration
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
orders_table = dynamodb.Table('aquachain-orders')

def create_test_technician_assignment(order_id):
    """Create a test technician assignment with complete data"""
    estimated_arrival = datetime.now(timezone.utc) + timedelta(hours=2)
    
    # Sample technician data
    technician_data = {
        'id': 'tech_001',
        'name': 'Rahul Nair',
        'phone': '+91 9876543210',
        'email': 'rahul.nair@aquachain.in',
        'address': 'Perumbavoor Service Center, Ernakulam District',
        'experience': '3 years',
        'rating': Decimal('4.7'),
        'status': 'assigned'
    }
    
    assignment_data = {
        'orderId': order_id,
        'technicianId': 'tech_001',
        'technicianName': 'Rahul Nair',
        'technicianPhone': '+91 9876543210',
        'technicianEmail': 'rahul.nair@aquachain.in',
        'technicianAddress': 'Perumbavoor Service Center, Ernakulam District',
        'assignedAt': datetime.now(timezone.utc).isoformat(),
        'estimatedArrival': estimated_arrival.isoformat(),
        'distance': Decimal('5.2'),
        'estimatedTravelTime': Decimal('25'),
        'status': 'assigned',
        'experience': '3 years',
        'rating': Decimal('4.7'),
        'skills': ['installation', 'maintenance', 'calibration'],
        'vehicleType': 'Motorcycle',
        'workingHours': '9:00 AM - 6:00 PM',
        'serviceArea': 'Ernakulam, Kottayam'
    }
    
    return technician_data, assignment_data

def find_and_update_orders():
    """Find orders and assign technicians"""
    try:
        # Scan for orders
        response = orders_table.scan()
        orders = response.get('Items', [])
        
        print(f"🔍 Found {len(orders)} total orders")
        
        # Find orders that can have technicians assigned
        updated_count = 0
        for order in orders:
            order_id = order.get('orderId')
            current_status = order.get('status')
            
            print(f"\n📋 Order {order_id}: {current_status}")
            
            # Assign technician to orders that are DEVICE_READY or already have technicians
            if current_status in ['DEVICE_READY', 'TECHNICIAN_ASSIGNED', 'assigned']:
                technician, assignment = create_test_technician_assignment(order_id)
                
                try:
                    orders_table.update_item(
                        Key={'orderId': order_id},
                        UpdateExpression='''SET 
                            #status = :status,
                            assignedTechnician = :tech_id,
                            assignedTechnicianName = :tech_name,
                            technician = :technician,
                            technicianAssignment = :assignment,
                            updatedAt = :updated
                        ''',
                        ExpressionAttributeNames={
                            '#status': 'status'
                        },
                        ExpressionAttributeValues={
                            ':status': 'TECHNICIAN_ASSIGNED',
                            ':tech_id': technician['id'],
                            ':tech_name': technician['name'],
                            ':technician': technician,
                            ':assignment': assignment,
                            ':updated': datetime.now(timezone.utc).isoformat()
                        }
                    )
                    
                    print(f"✅ Updated order {order_id} with technician assignment")
                    print(f"   👤 Technician: {technician['name']}")
                    print(f"   📞 Phone: {technician['phone']}")
                    print(f"   ⭐ Rating: {technician['rating']}")
                    updated_count += 1
                    
                except Exception as e:
                    print(f"❌ Failed to update order {order_id}: {e}")
            else:
                print(f"   ⏭️  Skipping (status: {current_status})")
        
        print(f"\n✅ Updated {updated_count} orders with technician assignments")
        return updated_count
        
    except Exception as e:
        print(f"❌ Error processing orders: {e}")
        return 0

def verify_technician_data():
    """Verify that orders now have technician data"""
    try:
        response = orders_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'TECHNICIAN_ASSIGNED'}
        )
        
        orders = response.get('Items', [])
        print(f"\n🔍 Verification: Found {len(orders)} orders with TECHNICIAN_ASSIGNED status")
        
        for order in orders:
            order_id = order.get('orderId')
            technician = order.get('technician', {})
            assignment = order.get('technicianAssignment', {})
            
            print(f"\n📋 Order {order_id}:")
            print(f"   Status: {order.get('status')}")
            
            if technician:
                print(f"   ✅ Technician Object:")
                print(f"      Name: {technician.get('name', 'N/A')}")
                print(f"      Phone: {technician.get('phone', 'N/A')}")
                print(f"      Email: {technician.get('email', 'N/A')}")
                print(f"      Rating: {technician.get('rating', 'N/A')}")
            else:
                print(f"   ❌ No technician object")
            
            if assignment:
                print(f"   ✅ Assignment Object:")
                print(f"      Estimated Arrival: {assignment.get('estimatedArrival', 'N/A')}")
                print(f"      Distance: {assignment.get('distance', 'N/A')} km")
            else:
                print(f"   ❌ No assignment object")
        
        return len(orders)
        
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return 0

def main():
    """Main execution"""
    print("🚀 Assigning technicians to existing orders...")
    
    # Update orders with technician assignments
    updated_count = find_and_update_orders()
    
    if updated_count > 0:
        print(f"\n🔍 Verifying technician data...")
        verified_count = verify_technician_data()
        
        print(f"\n✅ Process completed!")
        print(f"   📊 Orders updated: {updated_count}")
        print(f"   ✅ Orders verified: {verified_count}")
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Open the frontend and go to 'My Orders'")
        print(f"   2. Look for orders with 'Technician Assigned' status")
        print(f"   3. Click 'View Details' to see the technician information")
        print(f"   4. Click 'View Details' next to the technician name to open the modal")
    else:
        print(f"\n⚠️  No orders were updated. Check if you have orders in the system.")

if __name__ == "__main__":
    main()