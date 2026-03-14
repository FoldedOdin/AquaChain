#!/usr/bin/env python3
"""
Test technician display functionality with real Cognito users
"""

import boto3
import json
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

def get_real_cognito_users():
    """Get existing Cognito users"""
    
    print("🔍 Finding existing Cognito users...")
    
    try:
        cognito_client = boto3.client('cognito-idp')
        
        # Get user pool ID
        user_pools = cognito_client.list_user_pools(MaxResults=10)
        aquachain_pool = None
        
        for pool in user_pools['UserPools']:
            if 'aquachain' in pool['Name'].lower():
                aquachain_pool = pool
                break
        
        if not aquachain_pool:
            print("❌ No AquaChain user pool found")
            return None, None
        
        user_pool_id = aquachain_pool['Id']
        print(f"✅ Found user pool: {aquachain_pool['Name']} ({user_pool_id})")
        
        # List users
        users_response = cognito_client.list_users(
            UserPoolId=user_pool_id,
            Limit=10
        )
        
        consumer_user = None
        technician_user = None
        
        for user in users_response['Users']:
            username = user['Username']
            attributes = {attr['Name']: attr['Value'] for attr in user.get('Attributes', [])}
            
            print(f"   👤 User: {username}")
            print(f"      Email: {attributes.get('email', 'N/A')}")
            print(f"      Role: {attributes.get('custom:role', 'consumer')}")
            
            if attributes.get('custom:role') == 'technician' and not technician_user:
                technician_user = {
                    'id': username,
                    'email': attributes.get('email'),
                    'name': attributes.get('name', attributes.get('given_name', 'Technician')),
                    'phone': attributes.get('phone_number', '+91 9876543210')
                }
            elif not consumer_user and attributes.get('custom:role') != 'technician':
                consumer_user = {
                    'id': username,
                    'email': attributes.get('email'),
                    'name': attributes.get('name', attributes.get('given_name', 'Consumer'))
                }
        
        return consumer_user, technician_user
        
    except Exception as e:
        print(f"❌ Error getting Cognito users: {e}")
        return None, None

def ensure_technician_in_users_table(technician_user):
    """Ensure technician exists in Users table with complete profile"""
    
    if not technician_user:
        print("❌ No technician user provided")
        return None
    
    print(f"🔧 Ensuring technician {technician_user['name']} exists in Users table...")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        users_table = dynamodb.Table('AquaChain-Users-dev')
        
        # Check if technician exists
        try:
            response = users_table.get_item(
                Key={
                    'PK': f"USER#{technician_user['id']}",
                    'SK': f"USER#{technician_user['id']}"
                }
            )
            