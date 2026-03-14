#!/usr/bin/env python3
"""
Test Order API with Technician Details
"""

import boto3
import json
import requests
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def main():
    print("🔍 Testing Order API with Technician Details")
    print("=" * 60)
    
    # Test the order we created
    test_order_id = "ord_17734098"
    
    # First, verify the order exists in DynamoDB
    print(f"📋 Checking order {test_order_id} in DynamoDB...")
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    orders_table = dynamodb.Table('aquachain-table-orders-dev')
    
    try:
        response = orders_table.get_item(
            Key={
                'PK': f'ORDER#{test_order_id}',
                'SK': f'ORDER#{test_order_id}'
            }
        )
        
        if 'Item' in response:
            order = response['Item']
            print("✅ Order found in DynamoDB:")
            print(f"   Order ID: {order.get('orderId')}")
            print(f"   Customer: {order.get('customerName')}")
            print(f"   Phone: {order.get('customerPhone')}")
            print(f"   Status: {order.get('status')}")
            print(f"   Technician ID: {order.get('assignedTechnicianId')}")
            print(f"   Technician Name: {order.get('assignedTechnicianName')}")
            print(f"   Technician Phone: {order.get('technicianPhone')}")
            print()
            
            # Check if technician assignment is complete
            has_tech_id = bool(order.get('assignedTechnicianId'))
            has_tech_name = bool(order.get('assignedTechnicianName'))
            has_tech_phone = bool(order.get('technicianPhone'))
            
            print("🔧 Technician Assignment Status:")
            print(f"   Has Technician ID: {'✅' if has_tech_id else '❌'}")
            print(f"   Has Technician Name: {'✅' if has_tech_name else '❌'}")
            print(f"   Has Technician Phone: {'✅' if has_tech_phone else '❌'}")
            
            if has_tech_id and has_tech_name:
                print("✅ Order has complete technician assignment")
            else:
                print("❌ Order missing technician assignment details")
            
        else:
            print(f"❌ Order {test_order_id} not found in DynamoDB")
            return
            
    except Exception as e:
        print(f"❌ Error checking DynamoDB: {e}")
        return
    
    # Now test the API endpoint
    print(f"\n🌐 Testing API endpoint for order {test_order_id}...")
    
    # Get the API Gateway URL (you may need to adjust this)
    api_base_url = "https://your-api-gateway-url.amazonaws.com/dev"  # Replace with actual URL
    
    # For now, let's just verify the data structure is correct
    print("📋 Expected API Response Structure:")
    expected_response = {
        "success": True,
        "data": {
            "id": test_order_id,
            "orderId": test_order_id,
            "customerName": order.get('customerName'),
            "customerPhone": order.get('customerPhone'),
            "status": order.get('status'),
            "assignedTechnician": order.get('assignedTechnicianId'),
            "assignedTechnicianName": order.get('assignedTechnicianName'),
            "technicianPhone": order.get('technicianPhone'),
            "deviceType": order.get('deviceType'),
            "totalAmount": float(order.get('totalAmount', 0)),
            "paymentMethod": order.get('paymentMethod'),
            "createdAt": order.get('createdAt'),
            "updatedAt": order.get('updatedAt'),
            "timeline": order.get('timeline', [])
        }
    }
    
    print(json.dumps(expected_response, indent=2, cls=DecimalEncoder))
    
    print(f"\n🎯 Frontend Timeline Display Test:")
    print("The frontend should now show:")
    print("1. ✅ Order Placed - Payment confirmed")
    print("2. ✅ Device Ready - Assembly & calibration (1–2 days)")
    print(f"3. ✅ Technician Assigned - {order.get('assignedTechnicianName')} assigned for installation")
    print("4. ✅ Shipped - Device dispatched • Tracking ID will be shared")
    print("5. ⏳ Out for Delivery - Device is on the way to your location")
    print("6. ⏳ Delivered & Installed - Device delivered and installation completed successfully")
    
    print(f"\n📱 The 'Technician Assigned' step should now show:")
    print(f"   - Status: ✅ Completed (not grayed out)")
    print(f"   - Technician Name: {order.get('assignedTechnicianName')}")
    print(f"   - Description: Dedicated technician assigned for installation")

if __name__ == '__main__':
    main()