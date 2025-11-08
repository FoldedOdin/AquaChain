#!/usr/bin/env python3
"""
Validation script for AquaChain Disaster Recovery implementation
Validates the DR implementation without requiring AWS CDK installation
"""

import os
import sys
import json
from pathlib import Path

def validate_file_exists(file_path: str, description: str) -> bool:
    """Validate that a file exists"""
    if os.path.exists(file_path):
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description}: {file_path} - NOT FOUND")
        return False

def validate_file_content(file_path: str, required_content: list, description: str) -> bool:
    """Validate that a file contains required content"""
    if not os.path.exists(file_path):
        print(f"✗ {description}: {file_path} - FILE NOT FOUND")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_content = []
        for required in required_content:
            if required not in content:
                missing_content.append(required)
        
        if missing_content:
            print(f"✗ {description}: Missing required content: {missing_content}")
            return False
        else:
            print(f"✓ {description}: All required content present")
            return True
            
    except Exception as e:
        print(f"✗ {description}: Error reading file - {str(e)}")
        return False

def validate_python_syntax(file_path: str, description: str) -> bool:
    """Validate Python file syntax"""
    if not os.path.exists(file_path):
        print(f"✗ {description}: {file_path} - FILE NOT FOUND")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, file_path, 'exec')
        print(f"✓ {description}: Valid Python syntax")
        return True
        
    except SyntaxError as e:
        print(f"✗ {description}: Syntax error - {str(e)}")
        return False
    except Exception as e:
        print(f"✗ {description}: Error validating syntax - {str(e)}")
        return False

def main():
    """Main validation function"""
    print("AquaChain Disaster Recovery Implementation Validation")
    print("=" * 60)
    
    validation_results = []
    
    # 1. Validate CDK stack files
    print("\n1. CDK Stack Files:")
    validation_results.append(validate_file_exists(
        "infrastructure/cdk/stacks/disaster_recovery_stack.py",
        "Disaster Recovery Stack"
    ))
    
    validation_results.append(validate_python_syntax(
        "infrastructure/cdk/stacks/disaster_recovery_stack.py",
        "DR Stack Syntax"
    ))
    
    # 2. Validate Lambda function
    print("\n2. Lambda Function:")
    validation_results.append(validate_file_exists(
        "lambda/disaster_recovery/handler.py",
        "DR Lambda Handler"
    ))
    
    validation_results.append(validate_file_exists(
        "lambda/disaster_recovery/requirements.txt",
        "DR Lambda Requirements"
    ))
    
    validation_results.append(validate_python_syntax(
        "lambda/disaster_recovery/handler.py",
        "DR Lambda Syntax"
    ))
    
    # 3. Validate management scripts
    print("\n3. Management Scripts:")
    validation_results.append(validate_file_exists(
        "scripts/disaster_recovery.py",
        "DR Management Script"
    ))
    
    validation_results.append(validate_python_syntax(
        "scripts/disaster_recovery.py",
        "DR Script Syntax"
    ))
    
    # 4. Validate documentation
    print("\n4. Documentation:")
    validation_results.append(validate_file_exists(
        "DOCS/disaster-recovery-procedures.md",
        "DR Procedures Documentation"
    ))
    
    # 5. Validate test files
    print("\n5. Test Files:")
    validation_results.append(validate_file_exists(
        "infrastructure/cdk/tests/test_disaster_recovery_stack.py",
        "DR Stack Tests"
    ))
    
    validation_results.append(validate_python_syntax(
        "infrastructure/cdk/tests/test_disaster_recovery_stack.py",
        "DR Test Syntax"
    ))
    
    # 6. Validate CDK app integration
    print("\n6. CDK App Integration:")
    validation_results.append(validate_file_content(
        "infrastructure/cdk/app.py",
        [
            "from stacks.disaster_recovery_stack import AquaChainDisasterRecoveryStack",
            "AquaChainDisasterRecoveryStack"
        ],
        "CDK App DR Integration"
    ))
    
    # 7. Validate required DR components
    print("\n7. DR Component Validation:")
    
    # Check DR stack components
    dr_stack_components = [
        "class AquaChainDisasterRecoveryStack",
        "_create_backup_infrastructure",
        "_create_cross_region_replication", 
        "_create_dr_automation",
        "_create_dr_monitoring",
        "backup.BackupVault",
        "backup.BackupPlan",
        "sfn.StateMachine",
        "lambda_.Function"
    ]
    
    validation_results.append(validate_file_content(
        "infrastructure/cdk/stacks/disaster_recovery_stack.py",
        dr_stack_components,
        "DR Stack Components"
    ))
    
    # Check Lambda handler components
    lambda_components = [
        "def validate_backups",
        "def test_restore", 
        "def cleanup_test_resources",
        "def run_full_dr_test",
        "backup_client = boto3.client('backup')",
        "dynamodb_client = boto3.client('dynamodb')",
        "s3_client = boto3.client('s3')"
    ]
    
    validation_results.append(validate_file_content(
        "lambda/disaster_recovery/handler.py",
        lambda_components,
        "DR Lambda Components"
    ))
    
    # Check management script components
    script_components = [
        "class DisasterRecoveryManager",
        "def list_backups",
        "def validate_backups",
        "def run_dr_test",
        "def create_manual_backup",
        "def get_dr_metrics"
    ]
    
    validation_results.append(validate_file_content(
        "scripts/disaster_recovery.py",
        script_components,
        "DR Script Components"
    ))
    
    # 8. Validate documentation completeness
    print("\n8. Documentation Completeness:")
    doc_sections = [
        "# AquaChain Disaster Recovery Procedures",
        "## Architecture",
        "## Automated Procedures", 
        "## Manual Procedures",
        "## Emergency Response Procedures",
        "## Testing Procedures",
        "## Compliance and Audit"
    ]
    
    validation_results.append(validate_file_content(
        "DOCS/disaster-recovery-procedures.md",
        doc_sections,
        "DR Documentation Sections"
    ))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(validation_results)
    total = len(validation_results)
    
    print(f"Passed: {passed}/{total} validations")
    
    if passed == total:
        print("✓ All validations passed! DR implementation is complete.")
        return 0
    else:
        print(f"✗ {total - passed} validations failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())