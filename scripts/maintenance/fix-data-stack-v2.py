#!/usr/bin/env python3
"""
Fix data_stack.py - Add missing commas after write_capacity
"""

filepath = "infrastructure/cdk/stacks/data_stack.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix missing comma after write_capacity=5
content = content.replace(
    "write_capacity=5\n            encryption=",
    "write_capacity=5,\n            encryption="
)

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed all missing commas in data_stack.py")
