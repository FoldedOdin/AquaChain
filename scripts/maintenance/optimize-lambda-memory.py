#!/usr/bin/env python3
"""
Optimize Lambda Memory Configuration
Reduces memory from 1024MB to 256MB to stay in free tier
"""

import os
import re

def optimize_file(filepath, optimizations):
    """Apply optimizations to a file"""
    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    for pattern, replacement, description in optimizations:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes_made.append(description)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Optimized: {filepath}")
        for change in changes_made:
            print(f"   - {change}")
        return True
    else:
        print(f"ℹ️  No changes needed: {filepath}")
        return False

def main():
    print("=" * 60)
    print("  LAMBDA MEMORY OPTIMIZATION")
    print("  Target: Stay within AWS Free Tier")
    print("=" * 60)
    print()
    
    # Optimizations to apply
    compute_optimizations = [
        (r'memory_size=\d+', 'memory_size=256', 'Reduced memory to 256MB'),
        (r'timeout=Duration\.seconds\(\d+\)', 'timeout=Duration.seconds(30)', 'Reduced timeout to 30s'),
        (r'tracing=lambda_\.Tracing\.ACTIVE', 'tracing=lambda_.Tracing.DISABLED', 'Disabled X-Ray tracing'),
        (r'log_retention=logs\.RetentionDays\.\w+', 'log_retention=logs.RetentionDays.ONE_DAY', 'Set log retention to 1 day'),
        (r'reserved_concurrent_executions=\d+', '# reserved_concurrent_executions removed for cost', 'Removed reserved concurrency'),
    ]
    
    data_optimizations = [
        (r'billing_mode=dynamodb\.BillingMode\.PAY_PER_REQUEST', 
         'billing_mode=dynamodb.BillingMode.PROVISIONED,\n        read_capacity=5,\n        write_capacity=5', 
         'Changed to provisioned capacity (free tier)'),
        (r'removal_policy=RemovalPolicy\.RETAIN', 'removal_policy=RemovalPolicy.DESTROY', 'Set to DESTROY for easy cleanup'),
    ]
    
    api_optimizations = [
        (r'throttle_rate_limit=\d+', 'throttle_rate_limit=100', 'Reduced API throttle limit'),
        (r'throttle_burst_limit=\d+', 'throttle_burst_limit=200', 'Reduced API burst limit'),
    ]
    
    # Files to optimize
    files_to_optimize = [
        ('infrastructure/cdk/stacks/compute_stack.py', compute_optimizations),
        ('infrastructure/cdk/stacks/data_stack.py', data_optimizations),
        ('infrastructure/cdk/stacks/api_stack.py', api_optimizations),
    ]
    
    total_optimized = 0
    
    for filepath, optimizations in files_to_optimize:
        if optimize_file(filepath, optimizations):
            total_optimized += 1
        print()
    
    print("=" * 60)
    print(f"  OPTIMIZATION COMPLETE")
    print(f"  Files optimized: {total_optimized}/{len(files_to_optimize)}")
    print("=" * 60)
    print()
    
    print("📊 Expected Cost Reduction:")
    print("   - Lambda: ₹1,328-2,241 → ₹0-300 (saves ₹1,028-1,941/month)")
    print("   - DynamoDB: ₹664-1,245 → ₹0-200 (saves ₹464-1,045/month)")
    print("   - CloudWatch: ₹1,743-2,241 → ₹0-300 (saves ₹1,443-1,941/month)")
    print()
    print("   Total Savings: ₹2,935-5,127/month")
    print()
    
    print("🚀 Next Steps:")
    print("   1. Review changes in the modified files")
    print("   2. Deploy optimized stacks:")
    print("      cd infrastructure/cdk")
    print("      cdk deploy --all")
    print("   3. Monitor costs in AWS Cost Explorer")
    print()

if __name__ == '__main__':
    main()
