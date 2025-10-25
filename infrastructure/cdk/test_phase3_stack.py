#!/usr/bin/env python3
"""
Test script to validate Phase 3 infrastructure stack
"""

import sys
from stacks.phase3_infrastructure_stack import AquaChainPhase3InfrastructureStack
from config.environment_config import get_environment_config
from aws_cdk import App, Environment

def test_phase3_stack():
    """Test Phase 3 stack creation"""
    try:
        app = App()
        config = get_environment_config("dev")
        
        stack = AquaChainPhase3InfrastructureStack(
            app,
            "TestPhase3Stack",
            config=config,
            env=Environment(account="123456789012", region="us-east-1")
        )
        
        # Verify resources were created
        assert stack.model_metrics_table is not None, "ModelMetrics table not created"
        assert stack.certificate_lifecycle_table is not None, "CertificateLifecycle table not created"
        assert stack.certificate_check_rule is not None, "Certificate check rule not created"
        assert stack.dependency_scan_rule is not None, "Dependency scan rule not created"
        assert stack.sbom_generation_rule is not None, "SBOM generation rule not created"
        
        print("✓ Phase 3 stack validation successful!")
        print(f"  - ModelMetrics table: {stack.model_metrics_table.table_name}")
        print(f"  - CertificateLifecycle table: {stack.certificate_lifecycle_table.table_name}")
        print(f"  - Certificate check rule: {stack.certificate_check_rule.rule_name}")
        print(f"  - Dependency scan rule: {stack.dependency_scan_rule.rule_name}")
        print(f"  - SBOM generation rule: {stack.sbom_generation_rule.rule_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Phase 3 stack validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phase3_stack()
    sys.exit(0 if success else 1)
