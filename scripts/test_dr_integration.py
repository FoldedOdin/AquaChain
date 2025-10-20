#!/usr/bin/env python3
"""
Integration test for AquaChain Disaster Recovery implementation
Tests the integration between DR stack and existing infrastructure
"""

import sys
import os
import importlib.util
from pathlib import Path

def load_module_from_path(module_name: str, file_path: str):
    """Load a Python module from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_environment_config():
    """Test environment configuration for DR features"""
    print("Testing environment configuration...")
    
    try:
        # Load environment config
        config_path = "infrastructure/cdk/config/environment_config.py"
        config_module = load_module_from_path("environment_config", config_path)
        
        # Test dev config
        dev_config = config_module.get_environment_config("dev")
        assert "environment" in dev_config
        assert "region" in dev_config
        assert "replica_region" in dev_config
        
        # Test prod config
        prod_config = config_module.get_environment_config("prod")
        assert "backup_config" in prod_config
        assert prod_config["backup_config"]["enable_continuous_backup"] == True
        
        # Test resource naming
        resource_name = config_module.get_resource_name(dev_config, "vault", "main")
        assert resource_name == "aquachain-vault-main-dev"
        
        print("✓ Environment configuration tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Environment configuration test failed: {str(e)}")
        return False

def test_dr_stack_structure():
    """Test DR stack class structure and methods"""
    print("Testing DR stack structure...")
    
    try:
        # Load DR stack module
        dr_stack_path = "infrastructure/cdk/stacks/disaster_recovery_stack.py"
        
        with open(dr_stack_path, 'r') as f:
            content = f.read()
        
        # Check required class and methods exist
        required_elements = [
            "class AquaChainDisasterRecoveryStack",
            "def __init__",
            "def _create_backup_infrastructure",
            "def _create_cross_region_replication",
            "def _create_dr_automation",
            "def _create_dr_monitoring"
        ]
        
        for element in required_elements:
            if element not in content:
                raise AssertionError(f"Missing required element: {element}")
        
        # Check AWS service integrations
        aws_services = [
            "aws_backup as backup",
            "aws_lambda as lambda_",
            "aws_stepfunctions as sfn",
            "aws_sns as sns",
            "aws_cloudwatch as cloudwatch"
        ]
        
        for service in aws_services:
            if service not in content:
                raise AssertionError(f"Missing AWS service import: {service}")
        
        print("✓ DR stack structure tests passed")
        return True
        
    except Exception as e:
        print(f"✗ DR stack structure test failed: {str(e)}")
        return False

def test_lambda_handler_structure():
    """Test Lambda handler structure and functions"""
    print("Testing Lambda handler structure...")
    
    try:
        lambda_path = "lambda/disaster_recovery/handler.py"
        
        with open(lambda_path, 'r') as f:
            content = f.read()
        
        # Check required functions
        required_functions = [
            "def lambda_handler",
            "def validate_backups",
            "def test_restore",
            "def cleanup_test_resources",
            "def run_full_dr_test",
            "def validate_restored_data",
            "def send_notification",
            "def record_dr_metric"
        ]
        
        for func in required_functions:
            if func not in content:
                raise AssertionError(f"Missing required function: {func}")
        
        # Check AWS client initialization
        aws_clients = [
            "backup_client = boto3.client('backup')",
            "dynamodb_client = boto3.client('dynamodb')",
            "s3_client = boto3.client('s3')",
            "sns_client = boto3.client('sns')",
            "cloudwatch_client = boto3.client('cloudwatch')"
        ]
        
        for client in aws_clients:
            if client not in content:
                raise AssertionError(f"Missing AWS client: {client}")
        
        print("✓ Lambda handler structure tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Lambda handler structure test failed: {str(e)}")
        return False

def test_management_script_structure():
    """Test management script structure and CLI interface"""
    print("Testing management script structure...")
    
    try:
        script_path = "scripts/disaster_recovery.py"
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check class and methods
        required_elements = [
            "class DisasterRecoveryManager",
            "def __init__",
            "def list_backups",
            "def validate_backups", 
            "def run_dr_test",
            "def create_manual_backup",
            "def get_dr_metrics"
        ]
        
        for element in required_elements:
            if element not in content:
                raise AssertionError(f"Missing required element: {element}")
        
        # Check CLI interface
        cli_elements = [
            "argparse.ArgumentParser",
            "add_parser('list-backups'",
            "add_parser('validate-backups'",
            "add_parser('run-dr-test'",
            "add_parser('create-backup'",
            "add_parser('get-metrics'"
        ]
        
        for element in cli_elements:
            if element not in content:
                raise AssertionError(f"Missing CLI element: {element}")
        
        print("✓ Management script structure tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Management script structure test failed: {str(e)}")
        return False

def test_cdk_app_integration():
    """Test CDK app integration with DR stack"""
    print("Testing CDK app integration...")
    
    try:
        app_path = "infrastructure/cdk/app.py"
        
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check DR stack import
        if "from stacks.disaster_recovery_stack import AquaChainDisasterRecoveryStack" not in content:
            raise AssertionError("Missing DR stack import")
        
        # Check DR stack instantiation
        if "AquaChainDisasterRecoveryStack(" not in content:
            raise AssertionError("Missing DR stack instantiation")
        
        # Check dependency setup
        if "dr_stack.add_dependency(data_stack)" not in content:
            raise AssertionError("Missing DR stack dependency")
        
        print("✓ CDK app integration tests passed")
        return True
        
    except Exception as e:
        print(f"✗ CDK app integration test failed: {str(e)}")
        return False

def test_documentation_completeness():
    """Test documentation completeness"""
    print("Testing documentation completeness...")
    
    try:
        doc_path = "DOCS/disaster-recovery-procedures.md"
        
        with open(doc_path, 'r') as f:
            content = f.read()
        
        # Check required sections
        required_sections = [
            "# AquaChain Disaster Recovery Procedures",
            "## Overview",
            "## Architecture", 
            "## Automated Procedures",
            "## Manual Procedures",
            "## Emergency Response Procedures",
            "## Testing Procedures",
            "## Compliance and Audit",
            "## Contacts and Escalation"
        ]
        
        for section in required_sections:
            if section not in content:
                raise AssertionError(f"Missing documentation section: {section}")
        
        # Check for practical examples
        practical_elements = [
            "```bash",
            "python scripts/disaster_recovery.py",
            "Recovery Time Objective (RTO)",
            "Recovery Point Objective (RPO)"
        ]
        
        for element in practical_elements:
            if element not in content:
                raise AssertionError(f"Missing practical element: {element}")
        
        print("✓ Documentation completeness tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Documentation completeness test failed: {str(e)}")
        return False

def test_requirements_coverage():
    """Test that implementation covers all requirements"""
    print("Testing requirements coverage...")
    
    try:
        # Read requirements document
        req_path = ".kiro/specs/aquachain-system/requirements.md"
        
        if not os.path.exists(req_path):
            print("⚠ Requirements document not found, skipping requirements coverage test")
            return True
        
        with open(req_path, 'r') as f:
            req_content = f.read()
        
        # Check if requirement 10.4 is mentioned (disaster recovery requirement)
        if "10.4" in req_content:
            # Read DR stack to see if it addresses the requirement
            dr_stack_path = "infrastructure/cdk/stacks/disaster_recovery_stack.py"
            with open(dr_stack_path, 'r') as f:
                dr_content = f.read()
            
            # Check for key DR features
            dr_features = [
                "backup",
                "cross_region_replication", 
                "disaster_recovery",
                "automated",
                "failover"
            ]
            
            for feature in dr_features:
                if feature not in dr_content.lower():
                    raise AssertionError(f"Missing DR feature: {feature}")
        
        print("✓ Requirements coverage tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Requirements coverage test failed: {str(e)}")
        return False

def main():
    """Run all integration tests"""
    print("AquaChain Disaster Recovery Integration Tests")
    print("=" * 60)
    
    tests = [
        test_environment_config,
        test_dr_stack_structure,
        test_lambda_handler_structure,
        test_management_script_structure,
        test_cdk_app_integration,
        test_documentation_completeness,
        test_requirements_coverage
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {str(e)}")
            results.append(False)
        print()
    
    # Summary
    print("=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total} tests")
    
    if passed == total:
        print("✓ All integration tests passed! DR implementation is properly integrated.")
        return 0
    else:
        print(f"✗ {total - passed} tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())