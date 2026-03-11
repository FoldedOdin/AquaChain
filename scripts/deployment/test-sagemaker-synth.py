#!/usr/bin/env python3
"""
Quick test script to validate SageMaker stack synthesis
"""

import subprocess
import sys
import os

def main():
    """Test SageMaker stack synthesis"""
    
    print("Testing SageMaker stack synthesis...")
    
    # Change to CDK directory
    cdk_dir = os.path.join(os.path.dirname(__file__), "..", "..", "infrastructure", "cdk")
    os.chdir(cdk_dir)
    
    try:
        # Run CDK synth for just the SageMaker stack
        result = subprocess.run([
            "cdk", "synth", "AquaChain-SageMaker-dev", 
            "--no-staging", "--quiet"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ SageMaker stack synthesis successful!")
            print("Stack can be deployed.")
            return True
        else:
            print("❌ SageMaker stack synthesis failed:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ CDK synth timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running CDK synth: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)