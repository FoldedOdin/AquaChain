#!/usr/bin/env python3
"""
Quick script to deploy API stack CORS fixes
"""

import subprocess
import sys
import os

def run_command(command, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0

def main():
    """Deploy API stack with CORS fixes"""
    
    # Change to CDK directory
    cdk_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'infrastructure', 'cdk')
    
    print("🔧 Deploying API stack CORS fixes...")
    
    # Deploy only the API stack
    if not run_command("cdk deploy AquaChain-API-dev --require-approval never", cwd=cdk_dir):
        print("❌ Failed to deploy API stack")
        return False
    
    print("✅ API stack CORS fixes deployed successfully!")
    print("\n📋 Next steps:")
    print("1. Test the API endpoints from your frontend")
    print("2. Check browser console for CORS errors")
    print("3. Verify OPTIONS preflight requests are working")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)