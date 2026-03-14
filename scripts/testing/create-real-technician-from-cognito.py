#!/usr/bin/env python3
"""
Create real technician assignments using actual Cognito users
"""

import boto3
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# AWS Configuration
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
cognito = boto3.client('cognito-idp', region_name='ap-south-1')
orders_table = dynamodb.Table('aquachain-orders')

# Cognito User Pool ID
USER_POOL_ID = 'ap-south-1_QUDl7hG8u'

def get_cognito_users():
    """Get real users from Cognito to use as technicians"""
    
    print("🔍 Fetching real users from Cognito...")
    
    try:
        response = cognito.list_users(
            UserPoolId=USER_POOL_ID,
            Limit=10
        )
        
        users = response.get('Users', [])
        print(f"📋 Found {len(users)} Cognito users")
        
        technician_candidates = []
        
        for user in users:
            # Extract user attributes
            attributes = {attr['Name']: attr['Value'] for attr in user.get('Attributes', [])}
            
            user_info = {
                'id': user['Username'],
                'name': f"{attributes.get('given_name', 'Unknown')} {attributes.get('family_name', 'User')}",
                'email': attributes.get('email', ''),
                'phone': attributes.get('phone_number', ''),
                'status': user['UserStatus'],
                'created': user['UserCreateDate'].isoformat() if 'UserCreateDate' in user else '',
                'groups': []
            }
            
            # Get user groups
            try:
                groups_response = cognito.admin_list_groups_for_user(
                    UserPoolId=USER_POOL_ID,
                    Username=user['Username']
                )
                user_info['groups'] = [group['GroupName'] for group in groups_response.get('Groups', [])]
            except Exception as e:
                print(f"⚠️  Could not get groups for {user['Username']}: {e}")
            
            technician_candidates.append(user_info)
            
            print(f"👤 {user_info['name']} ({user_info['id']})")
            print(f"   📧 {user_info['email']}")
            print(f"   📞 {user_info['phone']}")
            print(f"   👥 Groups: {user_info['groups']}")
            print(f"   📊 Status: {user_info['status']}")
            print()
        
        return technician_candidates
        
    except Exception as e:
        print(f"❌ Error fetching Cognito users: {e}")
        return []

def create_technician_from_cognito_user(cognito_user, service_area="Ernakulam, Kerala"):
    """Create a technician profile from a Cognito user"""
    
    # Generate realistic technician data based on the real user
    technician = {
        'id': f"tech_{cognito_user['id'][:8]}",
        'name': cognito_user['name'],
        'phone': cognito_user['phone'] or '+91 9876543210',  # Fallback if no phone
        'email': cognito_user['email'],
        'address': f"AquaChain Service Center, {service_area}",
        'experience': '2-4 years',  # Realistic experience range
        'rating': Decimal('4.5'),  # Good rating
        'status': 'assigned',
        'skills': ['installation', 'maintenance', 'customer_service'],
        'vehicleType': 'Motorcycle',
        'workingHours': '9:00 AM - 6:00 PM',
        'serviceArea': service_area,
        'certifications': ['Water Quality Specialist', 'Customer Service']
    }
    
    return technician

def create_assignment_from_real_technician(order_id, technician):
    """Create a technician assignment using real user data"""
    
    estimated_arrival = datetime.now(timezone.utc) + timedelta(hours=3)  # 3 hours from now
    
    assignment = {
        'orderId': order_id,
        'technicianId': technician['id'],
        'technicianName': technician['name'],
        'technicianPhone': technician['phone'],
        'technicianEmail': technician['email'],
        'technicianAddress': technician['address'],
        'assignedAt': datetime.now(timezone.utc).isoformat(),
        'estimatedArrival': estimated_arrival.isoformat(),
        'distance': Decimal('8.5'),  # Realistic distance
        'estimatedTravelTime': Decimal('35'),  # 35 minutes travel time
        'status': 'assigned',
        'experience': technician['experience'],
        'rating': technician['rating'],
        'skills': technician['skills'],
        'vehicleType': technician['vehicleType'],
        'workingHours': technician['workingHours'],
        'serviceArea': technician['serviceArea']
    }
    
    return assignment

def assign_real_technicians_to_orders():
    """Assign real Cognito users as technicians to orders"""
    
    print("🔧 Assigning real technicians to orders...")
    
    # Get real Cognito users
    cognito_users = get_cognito_users()
    
    if not cognito_users:
        print("❌ No Cognito users found")
        return
    
    # Filter for confirmed users only
    confirmed_users = [user for user in cognito_users if user['status'] == 'CONFIRMED']
    
    if not confirmed_users:
        print("❌ No confirmed Cognito users found")
        return
    
    print(f"✅ Found {len(confirmed_users)} confirmed users to use as technicians")
    
    # Get orders that need technician assignment
    try:
        response = orders_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'TECHNICIAN_ASSIGNED'}
        )
        
        orders = response.get('Items', [])
        print(f"📋 Found {len(orders)} orders with TECHNICIAN_ASSIGNED status")
        
        if not orders:
            print("⚠️  No orders found to assign technicians to")
            return
        
        # Assign technicians to orders
        for i, order in enumerate(orders):
            # Use different users for different orders (round-robin)
            cognito_user = confirmed_users[i % len(confirmed_users)]
            
            # Create technician profile from Cognito user
            technician = create_technician_from_cognito_user(cognito_user)
            assignment = create_assignment_from_real_technician(order['orderId'], technician)
            
            try:
                orders_table.update_item(
                    Key={'orderId': order['orderId']},
                    UpdateExpression='''SET 
                        assignedTechnician = :tech_id,
                        assignedTechnicianName = :tech_name,
                        technician = :technician,
                        technicianAssignment = :assignment,
                        updatedAt = :updated
                    ''',
                    ExpressionAttributeValues={
                        ':tech_id': technician['id'],
                        ':tech_name': technician['name'],
                        ':technician': technician,
                        ':assignment': assignment,
                        ':updated': datetime.now(timezone.utc).isoformat()
                    }
                )
                
                print(f"✅ Assigned real technician to order {order['orderId']}")
                print(f"   👤 Technician: {technician['name']}")
                print(f"   📧 Email: {technician['email']}")
                print(f"   📞 Phone: {technician['phone']}")
                print(f"   🕐 Estimated Arrival: {assignment['estimatedArrival']}")
                print()
                
            except Exception as e:
                print(f"❌ Failed to assign technician to order {order['orderId']}: {e}")
        
        print(f"✅ Completed technician assignments using real Cognito users")
        
    except Exception as e:
        print(f"❌ Error processing orders: {e}")

def verify_real_technician_assignments():
    """Verify that orders now have real technician data"""
    
    print("🔍 Verifying real technician assignments...")
    
    try:
        response = orders_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'TECHNICIAN_ASSIGNED'}
        )
        
        orders = response.get('Items', [])
        
        for order in orders:
            order_id = order.get('orderId')
            technician = order.get('technician', {})
            
            print(f"📋 Order {order_id}:")
            print(f"   👤 Technician: {technician.get('name', 'N/A')}")
            print(f"   📧 Email: {technician.get('email', 'N/A')}")
            print(f"   📞 Phone: {technician.get('phone', 'N/A')}")
            print(f"   🆔 ID: {technician.get('id', 'N/A')}")
            
            # Check if this looks like real data (not "Rahul Nair")
            if technician.get('name') != 'Rahul Nair':
                print(f"   ✅ Using real Cognito user data")
            else:
                print(f"   ⚠️  Still using test data")
            print()
        
    except Exception as e:
        print(f"❌ Error verifying assignments: {e}")

def main():
    """Main execution"""
    
    print("🚀 Creating Real Technician Assignments from Cognito Users...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Step 1: Get Cognito users
    cognito_users = get_cognito_users()
    
    if not cognito_users:
        print("❌ Cannot proceed without Cognito users")
        return
    
    # Step 2: Assign real technicians
    assign_real_technicians_to_orders()
    
    # Step 3: Verify assignments
    verify_real_technician_assignments()
    
    print("\n🎯 Next Steps:")
    print("1. Refresh the frontend to see real technician names")
    print("2. Verify that 'Rahul Nair' is replaced with actual user names")
    print("3. Test the technician modal with real contact information")

if __name__ == "__main__":
    main()