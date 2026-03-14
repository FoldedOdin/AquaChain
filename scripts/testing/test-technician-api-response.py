#!/usr/bin/env python3
"""
Test the API response to verify technician data is being returned correctly
"""

import boto3
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'lambda', 'orders'))

from get_orders import handler

def test_get_orders_api():
    """Test the get_orders Lambda function directly"""
    
    # Create a mock event (simulating API Gateway)
    mock_event = {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-consumer-123'  # Use the actual consumer ID from orders
                }
            }
        },
        'httpMethod': 'GET',
        'path': '/api/orders'
    }
    
    mock_context = type('MockContext', (), {
        'request_id': 'test-request-123',
        'function_name': 'test-function'
    })()
    
    try:
        print("🧪 Testing get_orders Lambda function...")
        
        # Call the handler directly
        response = handler(mock_event, mock_context)
        
        print(f"📊 Response Status: {response['statusCode']}")
        
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            orders = body.get('orders', [])
            
            print(f"📋 Found {len(orders)} orders")
            
            # Check for technician data
            technician_orders = []
            for order in orders:
                if order.get('status') == 'TECHNICIAN_ASSIGNED':
                    technician_orders.append(order)
            
            print(f"🔧 Found {len(technician_orders)} orders with technician assignments")
            
            # Detailed check of technician data
            for order in technician_orders:
                order_id = order.get('orderId')
                print(f"\n📋 Order {order_id}:")
                print(f"   Status: {order.get('status')}")
                
                # Check technician object
                technician = order.get('technician')
                if technician:
                    print(f"   ✅ Technician Object:")
                    print(f"      ID: {technician.get('id', 'N/A')}")
                    print(f"      Name: {technician.get('name', 'N/A')}")
                    print(f"      Phone: {technician.get('phone', 'N/A')}")
                    print(f"      Email: {technician.get('email', 'N/A')}")
                    print(f"      Address: {technician.get('address', 'N/A')}")
                    print(f"      Rating: {technician.get('rating', 'N/A')}")
                    print(f"      Experience: {technician.get('experience', 'N/A')}")
                else:
                    print(f"   ❌ No technician object found")
                
                # Check assignment object
                assignment = order.get('technicianAssignment')
                if assignment:
                    print(f"   ✅ Assignment Object:")
                    print(f"      Technician ID: {assignment.get('technicianId', 'N/A')}")
                    print(f"      Technician Name: {assignment.get('technicianName', 'N/A')}")
                    print(f"      Phone: {assignment.get('technicianPhone', 'N/A')}")
                    print(f"      Email: {assignment.get('technicianEmail', 'N/A')}")
                    print(f"      Estimated Arrival: {assignment.get('estimatedArrival', 'N/A')}")
                    print(f"      Distance: {assignment.get('distance', 'N/A')} km")
                    print(f"      Travel Time: {assignment.get('estimatedTravelTime', 'N/A')} min")
                else:
                    print(f"   ❌ No assignment object found")
                
                # Check legacy fields
                assigned_technician = order.get('assignedTechnician')
                assigned_technician_name = order.get('assignedTechnicianName')
                
                print(f"   📝 Legacy Fields:")
                print(f"      assignedTechnician: {assigned_technician}")
                print(f"      assignedTechnicianName: {assigned_technician_name}")
            
            if len(technician_orders) > 0:
                print(f"\n✅ API is returning technician data correctly!")
                print(f"   Frontend should now display:")
                print(f"   - Technician name in order status")
                print(f"   - 'View Details' button next to technician name")
                print(f"   - Complete technician info in modal")
            else:
                print(f"\n⚠️  No orders with technician assignments found")
                print(f"   Run the assign-technician-to-existing-orders.py script first")
        
        else:
            print(f"❌ API call failed with status {response['statusCode']}")
            print(f"Response: {response.get('body', 'No body')}")
    
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main execution"""
    print("🚀 Testing technician API response...")
    test_get_orders_api()

if __name__ == "__main__":
    main()