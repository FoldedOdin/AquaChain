#!/usr/bin/env python3
"""
Seed the AquaChain inventory DynamoDB table with initial parts data.
Usage: python scripts/setup/seed-inventory.py [environment]
"""
import boto3
import json
import sys
from datetime import datetime, timedelta

ENV = sys.argv[1] if len(sys.argv) > 1 else 'dev'
TABLE_NAME = f'aquachain-table-inventory-{ENV}'

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table(TABLE_NAME)

def days_ago(n):
    return (datetime.utcnow() - timedelta(days=n)).isoformat() + 'Z'

PARTS = [
    # Sensors
    {'partId':'PART-001','name':'pH Sensor','category':'Sensors','quantity':15,'minQuantity':5,'location':'Warehouse A - Shelf 3','unitPrice':3850,'description':'High-precision pH sensor for water quality monitoring','lastRestocked':days_ago(7)},
    {'partId':'PART-002','name':'Turbidity Sensor','category':'Sensors','quantity':8,'minQuantity':5,'location':'Warehouse A - Shelf 3','unitPrice':4400,'description':'Optical turbidity sensor for measuring water clarity','lastRestocked':days_ago(10)},
    {'partId':'PART-003','name':'TDS Sensor','category':'Sensors','quantity':12,'minQuantity':5,'location':'Warehouse A - Shelf 3','unitPrice':3250,'description':'Total Dissolved Solids sensor','lastRestocked':days_ago(5)},
    {'partId':'PART-004','name':'Temperature Sensor','category':'Sensors','quantity':20,'minQuantity':10,'location':'Warehouse A - Shelf 4','unitPrice':1340,'description':'Digital temperature sensor (-40°C to 125°C)','lastRestocked':days_ago(3)},
    {'partId':'PART-013','name':'Conductivity Sensor','category':'Sensors','quantity':10,'minQuantity':5,'location':'Warehouse A - Shelf 3','unitPrice':4200,'description':'EC sensor for measuring water conductivity','lastRestocked':days_ago(8)},
    {'partId':'PART-014','name':'Dissolved Oxygen Sensor','category':'Sensors','quantity':6,'minQuantity':5,'location':'Warehouse A - Shelf 3','unitPrice':5500,'description':'DO sensor for oxygen level monitoring','lastRestocked':days_ago(12)},
    {'partId':'PART-015','name':'Flow Sensor','category':'Sensors','quantity':14,'minQuantity':8,'location':'Warehouse A - Shelf 4','unitPrice':2800,'description':'Water flow rate sensor (1-30 L/min)','lastRestocked':days_ago(6)},
    {'partId':'PART-016','name':'Pressure Sensor','category':'Sensors','quantity':18,'minQuantity':10,'location':'Warehouse A - Shelf 4','unitPrice':3600,'description':'Water pressure transducer (0-10 bar)','lastRestocked':days_ago(4)},
    # Filters
    {'partId':'PART-005','name':'Sediment Filter','category':'Filters','quantity':25,'minQuantity':10,'location':'Warehouse B - Shelf 1','unitPrice':1050,'description':'5-micron sediment filter cartridge','lastRestocked':days_ago(2)},
    {'partId':'PART-006','name':'Carbon Filter','category':'Filters','quantity':18,'minQuantity':8,'location':'Warehouse B - Shelf 1','unitPrice':1590,'description':'Activated carbon filter for chlorine removal','lastRestocked':days_ago(4)},
    {'partId':'PART-017','name':'RO Membrane','category':'Filters','quantity':12,'minQuantity':6,'location':'Warehouse B - Shelf 2','unitPrice':2200,'description':'Reverse osmosis membrane 75 GPD','lastRestocked':days_ago(5)},
    {'partId':'PART-018','name':'UV Filter','category':'Filters','quantity':8,'minQuantity':5,'location':'Warehouse B - Shelf 2','unitPrice':3200,'description':'UV sterilization filter cartridge','lastRestocked':days_ago(9)},
    {'partId':'PART-019','name':'Pre-Filter','category':'Filters','quantity':30,'minQuantity':15,'location':'Warehouse B - Shelf 1','unitPrice':650,'description':'20-micron pre-filter cartridge','lastRestocked':days_ago(1)},
    # Chemicals
    {'partId':'PART-007','name':'Calibration Solution pH 7','category':'Chemicals','quantity':30,'minQuantity':15,'location':'Warehouse C - Cabinet 2','unitPrice':750,'description':'pH 7.0 calibration buffer solution (500ml)','lastRestocked':days_ago(1)},
    {'partId':'PART-008','name':'Calibration Solution pH 4','category':'Chemicals','quantity':28,'minQuantity':15,'location':'Warehouse C - Cabinet 2','unitPrice':750,'description':'pH 4.0 calibration buffer solution (500ml)','lastRestocked':days_ago(1)},
    {'partId':'PART-020','name':'Calibration Solution pH 10','category':'Chemicals','quantity':25,'minQuantity':15,'location':'Warehouse C - Cabinet 2','unitPrice':750,'description':'pH 10.0 calibration buffer solution (500ml)','lastRestocked':days_ago(1)},
    {'partId':'PART-021','name':'Cleaning Solution','category':'Chemicals','quantity':20,'minQuantity':10,'location':'Warehouse C - Cabinet 3','unitPrice':950,'description':'Sensor cleaning solution (1L)','lastRestocked':days_ago(3)},
    {'partId':'PART-022','name':'Storage Solution','category':'Chemicals','quantity':22,'minQuantity':12,'location':'Warehouse C - Cabinet 3','unitPrice':550,'description':'Electrode storage solution (250ml)','lastRestocked':days_ago(2)},
    {'partId':'PART-023','name':'Disinfectant','category':'Chemicals','quantity':15,'minQuantity':8,'location':'Warehouse C - Cabinet 4','unitPrice':1200,'description':'System disinfectant solution (2L)','lastRestocked':days_ago(7)},
    # Tools
    {'partId':'PART-009','name':'Multimeter','category':'Tools','quantity':5,'minQuantity':3,'location':'Tool Room - Drawer 1','unitPrice':3750,'description':'Digital multimeter for electrical testing','lastRestocked':days_ago(30)},
    {'partId':'PART-010','name':'Screwdriver Set','category':'Tools','quantity':8,'minQuantity':5,'location':'Tool Room - Drawer 2','unitPrice':2170,'description':'Professional screwdriver set (12 pieces)','lastRestocked':days_ago(20)},
    {'partId':'PART-024','name':'Wrench Set','category':'Tools','quantity':6,'minQuantity':4,'location':'Tool Room - Drawer 3','unitPrice':1850,'description':'Adjustable wrench set (3 pieces)','lastRestocked':days_ago(25)},
    {'partId':'PART-025','name':'Pliers Set','category':'Tools','quantity':10,'minQuantity':5,'location':'Tool Room - Drawer 2','unitPrice':1650,'description':'Professional pliers set (5 pieces)','lastRestocked':days_ago(18)},
    {'partId':'PART-026','name':'Wire Stripper','category':'Tools','quantity':7,'minQuantity':5,'location':'Tool Room - Drawer 1','unitPrice':950,'description':'Automatic wire stripper tool','lastRestocked':days_ago(22)},
    {'partId':'PART-027','name':'Soldering Iron','category':'Tools','quantity':4,'minQuantity':3,'location':'Tool Room - Drawer 4','unitPrice':2800,'description':'Temperature controlled soldering station','lastRestocked':days_ago(35)},
    {'partId':'PART-028','name':'Drill Set','category':'Tools','quantity':3,'minQuantity':2,'location':'Tool Room - Cabinet 1','unitPrice':4500,'description':'Cordless drill with bit set','lastRestocked':days_ago(40)},
    # Parts
    {'partId':'PART-011','name':'O-Ring Kit','category':'Parts','quantity':3,'minQuantity':5,'location':'Warehouse A - Shelf 5','unitPrice':1300,'description':'Assorted O-rings for sealing (100 pieces)','lastRestocked':days_ago(15)},
    {'partId':'PART-012','name':'Replacement Gasket','category':'Parts','quantity':0,'minQuantity':10,'location':'Warehouse A - Shelf 5','unitPrice':500,'description':'Rubber gasket for filter housing','lastRestocked':days_ago(45)},
    {'partId':'PART-029','name':'Pipe Fittings','category':'Parts','quantity':45,'minQuantity':20,'location':'Warehouse A - Shelf 6','unitPrice':850,'description':'Assorted pipe fittings (50 pieces)','lastRestocked':days_ago(5)},
    {'partId':'PART-030','name':'Valve Assembly','category':'Parts','quantity':12,'minQuantity':6,'location':'Warehouse A - Shelf 6','unitPrice':1800,'description':'Solenoid valve assembly 12V DC','lastRestocked':days_ago(10)},
    {'partId':'PART-031','name':'Power Supply','category':'Parts','quantity':8,'minQuantity':5,'location':'Warehouse A - Shelf 7','unitPrice':650,'description':'12V 2A power adapter','lastRestocked':days_ago(8)},
    {'partId':'PART-032','name':'Cable Kit','category':'Parts','quantity':20,'minQuantity':10,'location':'Warehouse A - Shelf 7','unitPrice':450,'description':'Sensor cable kit with connectors (5m)','lastRestocked':days_ago(4)},
    {'partId':'PART-033','name':'Mounting Bracket','category':'Parts','quantity':25,'minQuantity':15,'location':'Warehouse A - Shelf 8','unitPrice':350,'description':'Universal sensor mounting bracket','lastRestocked':days_ago(6)},
    {'partId':'PART-034','name':'Battery Pack','category':'Parts','quantity':2,'minQuantity':5,'location':'Warehouse A - Shelf 7','unitPrice':2200,'description':'Rechargeable Li-ion battery pack','lastRestocked':days_ago(50)},
    {'partId':'PART-035','name':'Display Module','category':'Parts','quantity':6,'minQuantity':5,'location':'Warehouse A - Shelf 8','unitPrice':850,'description':'LCD display module 16x2','lastRestocked':days_ago(14)},
]

now = datetime.utcnow().isoformat() + 'Z'

print(f"Seeding {len(PARTS)} items into {TABLE_NAME}...")

with table.batch_writer() as batch:
    for part in PARTS:
        batch.put_item(Item={
            'PK': f"ITEM#{part['partId']}",
            'SK': 'CURRENT',
            'partId': part['partId'],
            'name': part['name'],
            'category': part['category'],
            'quantity': part['quantity'],
            'minQuantity': part['minQuantity'],
            'location': part['location'],
            'unitPrice': part['unitPrice'],
            'description': part['description'],
            'lastRestocked': part['lastRestocked'],
            'status': 'active',
            'createdAt': now,
            'updatedAt': now,
            # GSI fields
            'GSI1PK': f"WAREHOUSE#{part['location'].split(' - ')[0]}",
            'GSI1SK': f"ITEM#{part['partId']}",
        })

print(f"✅ Seeded {len(PARTS)} inventory items into {TABLE_NAME}")
