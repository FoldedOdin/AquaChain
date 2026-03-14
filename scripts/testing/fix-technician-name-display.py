#!/usr/bin/env python3
"""
Fix Technician Name Display in Orders
"""

import boto3
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def main():
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    
    # Check both order tables
    orders_table = dynamodb.Table('aquachain-table-orders-dev')
    users_table = dynamodb.Table('AquaChain-Users')
    
    print("🔍 Fixing Technician Name Display")
    print("=" * 50)
    
    # First, get the correct technician name from Users table
    print("📋 Getting technician details from Users table...")
    
    try:
        response = users_table.get_item(
            Key={'userId': '31333d7a-7031-703b-2e21-966a49444222'}
        )
        
        if 'Item' in response:
            technician = response['Item']
            correct_name = f"{technician['profile']['firstName']} {technician['profile']['lastName']}"
            correct_phone = technician['profile']['phone']
            correct_email = technician['email']
            
            print(f"✅ Found technician: {correct_name}")
            print(f"   Email: {correct_email}")
            print(f"   Phone: {correct_phone}")
            print()
        else:
            print("❌ Technician not found in Users table")
            return
            
    except Exception as e:
        print(f"❌ Error getting technician: {e}")
        return
    
    # Now scan all orders and fix the technician name
    print("🔧 Scanning orders and fixing technician names...")
    
    try:
        response = orders_table.scan()
        
        if response['Items']:
            print(f"✅ Found {len(response['Items'])} orders")
            
            for item in response['Items']:
                order_id = item.get('orderId', 'N/A')
                assigned_tech_id = item.get('assignedTechnicianId')
                current_tech_name = item.get('assignedTechnicianName', 'N/A')
                
                print(f"\n📋 Order: {order_id}")
                print(f"   Current Tech Name: {current_tech_name}")
                print(f"   Assigned Tech ID: {assigned_tech_id}")
                
                # If this order is assigned to Sidharth but shows wrong name
                if assigned_tech_id == '31333d7a-7031-703b-2e21-966a49444222' and current_tech_name != correct_name:
                    print(f"   🔧 FIXING: Updating technician name from '{current_tech_name}' to '{correct_name}'")
                    
                    # Update the order with correct technician details
                    orders_table.update_item(
                        Key={
                            'PK': item['PK'],
                            'SK': item['SK']
                        },
                        UpdateExpression='SET assignedTechnicianName = :tech_name, technicianPhone = :tech_phone, technicianEmail = :tech_email',
                        ExpressionAttributeValues={
                            ':tech_name': correct_name,
                            ':tech_phone': correct_phone,
                            ':tech_email': correct_email
                        }
                    )
                    
                    print(f"   ✅ Updated successfully!")
                elif assigned_tech_id == '31333d7a-7031-703b-2e21-966a49444222':
                    print(f"   ✅ Already has correct name")
                else:
                    print(f"   ℹ️  Different technician or no assignment")
                    
        else:
            print("❌ No orders found")
            
    except Exception as e:
        print(f"❌ Error scanning orders: {e}")
    
    # Now let's create a test order with the exact phone number from the image
    print(f"\n🆕 Creating test order with phone number from image...")
    
    test_order_id = "ord_17734098"  # From the image
    
    try:
        # Create the order with the exact details from the image
        orders_table.put_item(
            Item={
                'PK': f'ORDER#{test_order_id}',
                'SK': f'ORDER#{test_order_id}',
                'orderId': test_order_id,
                'customerName': 'Karthik K Pradeep',
                'customerPhone': '+918547613649',  # Exact phone from image
                'customerEmail': 'karthikkpradeep123@gmail.com',
                'status': 'SHIPPED',
                'deviceType': 'AquaChain Pro',
                'totalAmount': Decimal('15999.00'),
                'paymentMethod': 'cod',
                'assignedTechnicianId': '31333d7a-7031-703b-2e21-966a49444222',
                'assignedTechnicianName': correct_name,  # Correct name
                'technicianPhone': correct_phone,
                'technicianEmail': correct_email,
                'createdAt': '2026-03-13T15:51:00Z',
                'updatedAt': '2026-03-13T15:51:00Z',
                'installationAddress': {
                    'street': '123 Test Street',
                    'city': 'Bangalore',
                    'state': 'Karnataka',
                    'pincode': '560001',
                    'coordinates': {
                        'latitude': Decimal('12.9716'),
                        'longitude': Decimal('77.5946')
                    }
                },
                'timeline': [
                    {
                        'status': 'placed',
                        'timestamp': '2026-03-13T13:51:00Z',
                        'description': 'Order placed successfully'
                    },
                    {
                        'status': 'confirmed',
                        'timestamp': '2026-03-13T13:51:00Z',
                        'description': 'Payment confirmed'
                    },
                    {
                        'status': 'assigned',
                        'timestamp': '2026-03-13T14:00:00Z',
                        'description': f'Technician {correct_name} assigned for installation'
                    },
                    {
                        'status': 'shipped',
                        'timestamp': '2026-03-13T15:51:00Z',
                        'description': 'Device dispatched • Tracking ID will be shared'
                    }
                ]
            }
        )
        
        print(f"✅ Created test order {test_order_id} with:")
        print(f"   Customer: Karthik K Pradeep")
        print(f"   Phone: +918547613649")
        print(f"   Technician: {correct_name}")
        print(f"   Status: SHIPPED")
        
    except Exception as e:
        print(f"❌ Error creating test order: {e}")

if __name__ == '__main__':
    main()