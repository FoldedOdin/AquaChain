#!/usr/bin/env python3
"""
Test runner for infrastructure tests with proper path setup
"""

import sys
import os
import pytest

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    # Run the infrastructure tests
    test_file = os.path.join(os.path.dirname(__file__), "test_dashboard_overhaul_infrastructure.py")
    exit_code = pytest.main([test_file, "-v", "--tb=short"])
    sys.exit(exit_code)