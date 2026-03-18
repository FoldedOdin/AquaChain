#!/usr/bin/env python3
"""
Check what's actually in the orders table:
1. Scan all orders and show their status + assignedTechnicianId fields
2. Find Sidharth Lenin's Cognito user ID
3. Check if the IDs match
"""
import boto3
import json
from decimal import Decimal

REGION = 'ap-south-1'
ORDERS_TABLE = 'aquachain-orders'
USERS_TABLE = 'aquachain-users'

dynamodb = boto3.resource('dynamodb', region_name=REGION)
cognito = boto3.client('cognito-idp', region_name=REGION)

# --- 1. Scan orders table ---
print("=== ORDERS TABLE ===")
orders_table = dynamodb.Table(ORDERS_TABLE)
response = orders_table.scan()
orders = response.get('Items', [])
print(f"Total orders: {len(orders)}")

for o in orders:
    print(f"\n  orderId: {o.get('orderId', 'N/A')}")
    print(f"  status: {o.get('status', 'N/A')}")
    print(f"  consumerId / userId: {o.get('consumerId', o.get('userId', 'N/A'))}")
    print(f"  assignedTechnicianId: {o.get('assignedTechnicianId', '*** MISSING ***')}")
    print(f"  assignedTechnician: {o.get('assignedTechnician', 'N/A')}")
    tech_assign = o.get('technicianAssignment', {})
    if tech_assign:
        print(f"  technicianAssignment.technicianId: {tech_assign.get('technicianId', 'N/A')}")
        print(f"  technicianAssignment.technicianName: {tech_assign.get('technicianName', 'N/A')}")
    # Show all keys so we don't miss anything
    print(f"  All keys: {sorted(o.keys())}")

# --- 2. Find Sidharth Lenin in Cognito ---
print("\n\n=== COGNITO: Find Sidharth Lenin ===")
try:
    # List user pools first
    idp = boto3.client('cognito-idp', region_name=REGION)
    pools = idp.list_user_pools(MaxResults=10)['UserPools']
    for pool in pools:
        print(f"Pool: {pool['Name']} ({pool['Id']})")
        try:
            users = idp.list_users(
                UserPoolId=pool['Id'],
                Filter='name = "Sidharth"',
                Limit=10
            )['Users']
            if not users:
                # Try by email
                users = idp.list_users(
                    UserPoolId=pool['Id'],
                    Limit=60
                )['Users']
                users = [u for u in users if any(
                    'sidharth' in str(a.get('Value', '')).lower()
                    for a in u.get('Attributes', [])
                )]
            for u in users:
                attrs = {a['Name']: a['Value'] for a in u.get('Attributes', [])}
                print(f"  Username: {u['Username']}")
                print(f"  sub (userId): {attrs.get('sub', 'N/A')}")
                print(f"  email: {attrs.get('email', 'N/A')}")
                print(f"  name: {attrs.get('name', 'N/A')}")
                # Check groups
                try:
                    groups = idp.admin_list_groups_for_user(
                        UserPoolId=pool['Id'],
                        Username=u['Username']
                    )['Groups']
                    print(f"  groups: {[g['GroupName'] for g in groups]}")
                except Exception:
                    pass
        except Exception as e:
            print(f"  Error listing users: {e}")
except Exception as e:
    print(f"Error: {e}")
