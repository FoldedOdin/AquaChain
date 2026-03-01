#!/usr/bin/env python3
"""
Fix DynamoDB Point-in-Time Recovery parameter across all CDK stacks
The correct parameter is 'point_in_time_recovery=True' not 'point_in_time_recovery_specification'
"""

import re
from pathlib import Path

def fix_pitr_in_file(file_path: Path) -> bool:
    """Fix PITR parameter in a single file"""
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    # Pattern 1: point_in_time_recovery_specification with True
    pattern1 = r'point_in_time_recovery_specification=dynamodb\.PointInTimeRecoverySpecification\(\s*point_in_time_recovery_enabled=True\s*\),'
    replacement1 = 'point_in_time_recovery=True,'
    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)
    
    # Pattern 2: point_in_time_recovery_specification with config variable
    pattern2 = r'point_in_time_recovery_specification=dynamodb\.PointInTimeRecoverySpecification\(\s*point_in_time_recovery_enabled=self\.config\["enable_point_in_time_recovery"\]\s*\),'
    replacement2 = 'point_in_time_recovery=self.config["enable_point_in_time_recovery"],'
    content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)
    
    # Pattern 3: point_in_time_recovery_specification with config.get()
    pattern3 = r'point_in_time_recovery_specification=dynamodb\.PointInTimeRecoverySpecification\(\s*point_in_time_recovery_enabled=self\.config\.get\("enable_point_in_time_recovery",\s*False\)\s*\),'
    replacement3 = 'point_in_time_recovery=self.config.get("enable_point_in_time_recovery", False),'
    content = re.sub(pattern3, replacement3, content, flags=re.MULTILINE)
    
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return True
    return False

def main():
    """Fix all stack files"""
    stack_dir = Path('infrastructure/cdk/stacks')
    
    if not stack_dir.exists():
        print(f"Error: {stack_dir} not found")
        return 1
    
    files_fixed = 0
    files_checked = 0
    
    for stack_file in stack_dir.glob('*.py'):
        files_checked += 1
        if fix_pitr_in_file(stack_file):
            files_fixed += 1
            print(f"✓ Fixed: {stack_file.name}")
    
    print(f"\nSummary:")
    print(f"  Files checked: {files_checked}")
    print(f"  Files fixed: {files_fixed}")
    
    return 0

if __name__ == '__main__':
    exit(main())
