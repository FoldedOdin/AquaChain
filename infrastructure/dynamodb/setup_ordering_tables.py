#!/usr/bin/env python3
"""
Setup script for Enhanced Consumer Ordering System DynamoDB tables
Creates and configures all required tables with proper GSIs and TTL settings
"""

import boto3
import json
import sys
from datetime import datetime
from decimal import Decimal
from ordering_tables import OrderingSystemTableManager

def setup_ordering_tables(region_name='us-east-1'):
    """
    Set up all DynamoDB tables for the Enhanced Consumer Ordering System
    """
    print("Setting up Enhanced Consumer Ordering System DynamoDB tables...")
    print(f"Region: {region_name}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)
    
    try:
        # Initialize table manager
        manager = OrderingSystemTableManager(region_name=region_name)
        
        # Create all tables
        manager.create_all_ordering_tables()
        
        # Verify tables were created successfully
        print("\nVerifying table creation...")
        dynamodb = boto3.client('dynamodb', region_name=region_name)
        
        expected_tables = [
            'aquachain-orders',
            'aquachain-payments', 
            'aquachain-technicians',
            'aquachain-order-simulations'
        ]
        
        for table_name in expected_tables:
            try:
                response = dynamodb.describe_table(TableName=table_name)
                status = response['Table']['TableStatus']
                print(f"✓ {table_name}: {status}")
                
                # Check GSIs
                if 'GlobalSecondaryIndexes' in response['Table']:
                    for gsi in response['Table']['GlobalSecondaryIndexes']:
                        gsi_name = gsi['IndexName']
                        gsi_status = gsi['IndexStatus']
                        print(f"  └─ GSI {gsi_name}: {gsi_status}")
                
            except Exception as e:
                print(f"✗ {table_name}: Error - {e}")
        
        print("\n" + "=" * 60)
        print("Enhanced Consumer Ordering System setup completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"Error setting up ordering tables: {e}")
        return False

def seed_sample_technicians(region_name='us-east-1'):
    """
    Seed the technicians table with sample data for testing
    """
    print("\nSeeding sample technician data...")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=region_name)
        table = dynamodb.Table('aquachain-technicians')
        
        sample_technicians = [
            {
                'PK': 'TECHNICIAN#tech-001',
                'SK': 'TECHNICIAN#tech-001',
                'GSI1PK': 'LOCATION#Mumbai#Maharashtra',
                'GSI1SK': 'AVAILABLE#true#tech-001',
                'technicianId': 'tech-001',
                'name': 'Rajesh Kumar',
                'phone': '+91-9876543210',
                'email': 'rajesh.kumar@aquachain.com',
                'location': {
                    'latitude': Decimal('19.0760'),
                    'longitude': Decimal('72.8777'),
                    'address': 'Andheri East, Mumbai',
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'pincode': '400069'
                },
                'available': True,
                'skills': ['device_installation', 'maintenance', 'calibration'],
                'rating': Decimal('4.8'),
                'currentOrderId': None,
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            },
            {
                'PK': 'TECHNICIAN#tech-002',
                'SK': 'TECHNICIAN#tech-002',
                'GSI1PK': 'LOCATION#Delhi#Delhi',
                'GSI1SK': 'AVAILABLE#true#tech-002',
                'technicianId': 'tech-002',
                'name': 'Priya Sharma',
                'phone': '+91-9876543211',
                'email': 'priya.sharma@aquachain.com',
                'location': {
                    'latitude': Decimal('28.6139'),
                    'longitude': Decimal('77.2090'),
                    'address': 'Connaught Place, New Delhi',
                    'city': 'Delhi',
                    'state': 'Delhi',
                    'pincode': '110001'
                },
                'available': True,
                'skills': ['device_installation', 'repair', 'customer_support'],
                'rating': Decimal('4.9'),
                'currentOrderId': None,
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            },
            {
                'PK': 'TECHNICIAN#tech-003',
                'SK': 'TECHNICIAN#tech-003',
                'GSI1PK': 'LOCATION#Bangalore#Karnataka',
                'GSI1SK': 'AVAILABLE#false#tech-003',
                'technicianId': 'tech-003',
                'name': 'Arjun Patel',
                'phone': '+91-9876543212',
                'email': 'arjun.patel@aquachain.com',
                'location': {
                    'latitude': Decimal('12.9716'),
                    'longitude': Decimal('77.5946'),
                    'address': 'Koramangala, Bangalore',
                    'city': 'Bangalore',
                    'state': 'Karnataka',
                    'pincode': '560034'
                },
                'available': False,
                'skills': ['device_installation', 'maintenance', 'training'],
                'rating': Decimal('4.7'),
                'currentOrderId': 'order-123',
                'assignedAt': datetime.now().isoformat(),
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            }
        ]
        
        # Insert sample technicians
        for technician in sample_technicians:
            table.put_item(Item=technician)
            print(f"✓ Added technician: {technician['name']} ({technician['technicianId']})")
        
        print(f"Successfully seeded {len(sample_technicians)} sample technicians")
        return True
        
    except Exception as e:
        print(f"Error seeding technician data: {e}")
        return False

def main():
    """
    Main function to set up ordering system tables
    """
    region = 'us-east-1'
    if len(sys.argv) > 1:
        region = sys.argv[1]
    
    # Set up tables
    success = setup_ordering_tables(region)
    
    if success:
        # Seed sample data
        seed_sample_technicians(region)
        
        print("\n" + "=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)
        print("Next steps:")
        print("1. Deploy Lambda functions for order management")
        print("2. Configure API Gateway endpoints")
        print("3. Set up Razorpay integration")
        print("4. Test the complete ordering flow")
        print("=" * 60)
    else:
        print("Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()