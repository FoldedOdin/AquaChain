#!/usr/bin/env python3
"""
Fix data_stack.py - Remove duplicate read_capacity/write_capacity lines
"""

import re

filepath = "infrastructure/cdk/stacks/data_stack.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match the problematic section
pattern = r'billing_mode=dynamodb\.BillingMode\.PROVISIONED,\s+read_capacity=5,\s+write_capacity=5[^\n]+\s+read_capacity=[^\n]+\s+write_capacity=[^\n]+'

# Replacement - clean version
replacement = '''billing_mode=dynamodb.BillingMode.PROVISIONED,
            read_capacity=5,
            write_capacity=5'''

# Replace all occurrences
content_fixed = re.sub(pattern, replacement, content)

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content_fixed)

print("✅ Fixed data_stack.py - Removed duplicate capacity lines")
print("📊 DynamoDB tables now set to:")
print("   - Billing Mode: PROVISIONED")
print("   - Read Capacity: 5 RCU per table")
print("   - Write Capacity: 5 WCU per table")
print("   - Total: 25 RCU + 25 WCU (FREE TIER!)")
