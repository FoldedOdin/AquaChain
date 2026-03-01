#!/usr/bin/env python3
"""
Quick validation script to test stack imports without full CDK synthesis
"""

import sys

def test_imports():
    """Test that all stacks can be imported"""
    errors = []
    
    # Test deployment_pipeline_stack
    try:
        from stacks.deployment_pipeline_stack import DeploymentPipelineStack
        print("✓ deployment_pipeline_stack imports successfully")
    except Exception as e:
        errors.append(f"✗ deployment_pipeline_stack: {e}")
    
    # Test production_monitoring_stack
    try:
        from stacks.production_monitoring_stack import ProductionMonitoringStack
        print("✓ production_monitoring_stack imports successfully")
    except Exception as e:
        errors.append(f"✗ production_monitoring_stack: {e}")
    
    # Test enhanced_consumer_ordering_stack
    try:
        from stacks.enhanced_consumer_ordering_stack import EnhancedConsumerOrderingStack
        print("✓ enhanced_consumer_ordering_stack imports successfully")
    except Exception as e:
        errors.append(f"✗ enhanced_consumer_ordering_stack: {e}")
    
    if errors:
        print("\nErrors found:")
        for error in errors:
            print(error)
        return False
    else:
        print("\n✓ All stacks import successfully!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
