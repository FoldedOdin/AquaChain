#!/usr/bin/env python3
"""
Test complete technician display functionality
"""

import boto3
import json
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import requests

def create_test_order_with_technician():
    """Create a test order and assign a technician"""
    
    print("🧪 Creating test order with technician assignment...")
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    orders_table = dynamodb.Table('aquachain-orders')
    users_table = dynamodb.Table('AquaChain-Users-dev')
    
    # Create test order
    order_id = f"ord_{uuid.uuid4().hex[:8]}"
    consumer_id = "test-consumer-123"
    
    # Create test technician if not exists
    technician_id = "tech_001"
    technician_data = {
        'PK': f'USER#{technician_id}',
        'SK': f'USER#{technician_id}',
        'userId': technician_id,
        'name': 'Rahul Nair',
        'email': 'rahul@aquachain.in',
        'phone': '+91 9876543210',
        'role': 'technician',
        'address': 'Perumbavoor Service Center, Kerala',
        'location': {
            'latitude': Decimal('10.1102'),
            'longitude': Decimal('76.4742')
        },
        'skills': ['water_quality_testing', 'device_installation', 'maintenance'],
        'experience': '3 years',
        'rating': Decimal('4.7'),
        'verified': True,
        'active': True,
        'available': True,
        'workSchedule': {
            'monday': {'start': '09:00', 'end': '18:00'},
            'tuesday': {'start': '09:00', 'end': '18:00'},
            'wednesday': {'start': '09:00', 'end': '18:00'},
            'thursday': {'start': '09:00', 'end': '18:00'},
            'friday': {'start': '09:00', 'end': '18:00'},
            'saturday': {'start': '09:00', 'end': '15:00'}
        },
        'performanceScore': 95,
        'createdAt': datetime.now(timezone.utc).isoformat(),
        'updatedAt': datetime.now(timezone.utc).isoformat()
    }
    
    try:
        users_table.put_item(Item=technician_data)
        print(f"✅ Created test technician: {technician_data['name']}")
    except Exception as e:
        print(f"⚠️  Technician may already exist: {e}")
    
    # Create technician assignment
    assignment_timestamp = datetime.now(timezone.utc)
    estimated_arrival = assignment_timestamp + timedelta(hours=2)
    
    technician_assignment = {
        'orderId': order_id,
        'technicianId': technician_id,
        'technicianName': 'Rahul Nair',
        'technicianPhone': '+91 9876543210',
        'technicianEmail': 'rahul@aquachain.in',
        'technicianAddress': 'Perumbavoor Service Center, Kerala',
        'assignedAt': assignment_timestamp.isoformat(),
        'estimatedArrival': estimated_arrival.isoformat(),
        'distance': Decimal('12.5'),
        'estimatedTravelTime': 45,
        'status': 'assigned',
        'experience': '3 years',
        'rating': Decimal('4.7'),
        'serviceLocation': {
            'latitude': Decimal('10.1234'),
            'longitude': Decimal('76.5678')
        }
    }
    
    # Create order with technician assignment
    order_data = {
        'orderId': order_id,
        'userId': consumer_id,  # Use userId instead of GSI1PK
        'consumerId': consumer_id,
        'deviceType': 'AquaChain Pro',
        'serviceType': 'installation',
        'paymentMethod': 'COD',
        'status': 'TECHNICIAN_ASSIGNED',
        'amount': Decimal('15000'),
        'deliveryAddress': {
            'street': '123 Test Street',
            'city': 'Kochi',
            'state': 'Kerala',
            'pincode': '682001',
            'country': 'India',
            'coordinates': {
                'latitude': Decimal('10.1234'),
                'longitude': Decimal('76.5678')
            }
        },
        'contactInfo': {
            'name': 'Test Customer',
            'phone': '+91 9876543210',
            'email': 'test@example.com'
        },
        'assignedTechnician': technician_id,
        'assignedTechnicianName': 'Rahul Nair',
        'technicianAssignment': technician_assignment,
        'statusHistory': [
            {
                'status': 'ORDER_PLACED',
                'timestamp': (assignment_timestamp - timedelta(hours=1)).isoformat(),
                'message': 'Order placed successfully'
            },
            {
                'status': 'TECHNICIAN_ASSIGNED',
                'timestamp': assignment_timestamp.isoformat(),
                'message': 'Technician Rahul Nair assigned for installation'
            }
        ],
        'createdAt': (assignment_timestamp - timedelta(hours=1)).isoformat(),
        'updatedAt': assignment_timestamp.isoformat(),
        'specialInstructions': 'Please call before arrival'
    }
    
    try:
        orders_table.put_item(Item=order_data)
        print(f"✅ Created test order: {order_id}")
        print(f"   Status: {order_data['status']}")
        print(f"   Assigned Technician: {order_data['assignedTechnicianName']}")
        print(f"   Technician Phone: {technician_assignment['technicianPhone']}")
        print(f"   Estimated Arrival: {technician_assignment['estimatedArrival']}")
        
        return order_id, consumer_id
        
    except Exception as e:
        print(f"❌ Failed to create test order: {e}")
        return None, None

def test_get_orders_api(consumer_id):
    """Test the get orders API to verify technician data is returned"""
    
    print(f"\n🔍 Testing get orders API for consumer: {consumer_id}")
    
    try:
        # Get API endpoint
        api_endpoint = "https://api.aquachain.example.com/dev"  # Adjust as needed
        
        # Create test JWT token (simplified for testing)
        import jwt
        
        test_token = jwt.encode({
            'sub': consumer_id,
            'iat': datetime.now(timezone.utc),
            'exp': datetime.now(timezone.utc) + timedelta(hours=1)
        }, 'test-secret', algorithm='HS256')
        
        headers = {
            'Authorization': f'Bearer {test_token}',
            'Content-Type': 'application/json'
        }
        
        # Make API request
        response = requests.get(f"{api_endpoint}/api/v1/orders", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API request successful")
            
            if data.get('success') and data.get('orders'):
                orders = data['orders']
                print(f"   📊 Found {len(orders)} orders")
                
                # Check for technician data
                for order in orders:
                    if order.get('technician') or order.get('technicianAssignment'):
                        print(f"   ✅ Order {order['orderId']} has technician data:")
                        
                        if order.get('technician'):
                            tech = order['technician']
                            print(f"      👤 Technician: {tech.get('name', 'N/A')}")
                            print(f"      📞 Phone: {tech.get('phone', 'N/A')}")
                            print(f"      📧 Email: {tech.get('email', 'N/A')}")
                            print(f"      📍 Address: {tech.get('address', 'N/A')}")
                            print(f"      ⭐ Rating: {tech.get('rating', 'N/A')}")
                        
                        if order.get('technicianAssignment'):
                            assignment = order['technicianAssignment']
                            print(f"      🕐 Estimated Arrival: {assignment.get('estimatedArrival', 'N/A')}")
                            print(f"      📏 Distance: {assignment.get('distance', 'N/A')} km")
                            print(f"      ⏱️  Travel Time: {assignment.get('estimatedTravelTime', 'N/A')} min")
                        
                        return True
                
                print("   ⚠️  No orders with technician data found")
                return False
            else:
                print(f"   ⚠️  No orders returned")
                return False
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_lambda_directly(consumer_id):
    """Test the Lambda function directly"""
    
    print(f"\n🔧 Testing Lambda function directly...")
    
    try:
        lambda_client = boto3.client('lambda')
        
        # Test event
        test_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": consumer_id
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/api/v1/orders"
        }
        
        response = lambda_client.invoke(
            FunctionName='aquachain-get-orders-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        if response['StatusCode'] == 200:
            payload = json.loads(response['Payload'].read())
            
            if payload.get('statusCode') == 200:
                body = json.loads(payload['body'])
                
                if body.get('success') and body.get('orders'):
                    orders = body['orders']
                    print(f"✅ Lambda test successful - {len(orders)} orders returned")
                    
                    # Check technician data
                    for order in orders:
                        if order.get('technician') or order.get('technicianAssignment'):
                            print(f"   ✅ Order {order['orderId']} includes technician data")
                            
                            if order.get('technician'):
                                tech = order['technician']
                                print(f"      Technician Object: {json.dumps(tech, indent=2)}")
                            
                            if order.get('technicianAssignment'):
                                assignment = order['technicianAssignment']
                                print(f"      Assignment Object: {json.dumps(assignment, indent=2)}")
                            
                            return True
                    
                    print("   ⚠️  No technician data found in orders")
                    return False
                else:
                    print(f"   ❌ No orders returned: {body}")
                    return False
            else:
                print(f"   ❌ Lambda returned error: {payload}")
                return False
        else:
            print(f"❌ Lambda invocation failed: {response['StatusCode']}")
            return False
            
    except Exception as e:
        print(f"❌ Lambda test failed: {e}")
        return False

def main():
    """Main test function"""
    
    print("🧪 AquaChain Technician Display Complete Test")
    print("=" * 50)
    
    # Create test order with technician
    order_id, consumer_id = create_test_order_with_technician()
    
    if not order_id:
        print("❌ Failed to create test order")
        return
    
    # Test Lambda function directly
    lambda_success = test_lambda_directly(consumer_id)
    
    # Test API endpoint (if available)
    # api_success = test_get_orders_api(consumer_id)
    
    print("\n📋 Test Results:")
    print(f"✅ Test order created: {order_id}")
    print(f"{'✅' if lambda_success else '❌'} Lambda function test: {'PASSED' if lambda_success else 'FAILED'}")
    # print(f"{'✅' if api_success else '❌'} API endpoint test: {'PASSED' if api_success else 'FAILED'}")
    
    if lambda_success:
        print("\n🎉 Technician display functionality is working!")
        print("\n📋 Frontend Testing Steps:")
        print("1. Open the AquaChain dashboard")
        print("2. Navigate to order history")
        print(f"3. Look for order {order_id}")
        print("4. Verify technician details are displayed")
        print("5. Click 'View Details' to open the modal")
        print("6. Verify all technician information is shown")
    else:
        print("\n❌ Tests failed - check the implementation")

if __name__ == "__main__":
    main()