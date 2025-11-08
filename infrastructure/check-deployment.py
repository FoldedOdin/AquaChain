#!/usr/bin/env python3
"""
Check AquaChain infrastructure deployment status
"""

import subprocess
import json
import sys

def run_command(command, check=False):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        return e

def check_stack_status(environment="dev"):
    """Check the status of all AquaChain stacks"""
    print(f"🔍 Checking AquaChain infrastructure status for environment: {environment}")
    print("=" * 70)
    
    stacks = [
        f"AquaChain-Security-{environment}",
        f"AquaChain-Core-{environment}",
        f"AquaChain-Data-{environment}",
        f"AquaChain-Compute-{environment}",
        f"AquaChain-API-{environment}",
        f"AquaChain-Monitoring-{environment}",
        f"AquaChain-DR-{environment}",
        f"AquaChain-LandingPage-{environment}"
    ]
    
    deployed_stacks = []
    failed_stacks = []
    missing_stacks = []
    
    for stack in stacks:
        result = run_command(
            f"aws cloudformation describe-stacks --stack-name {stack} --query 'Stacks[0].StackStatus' --output text"
        )
        
        if result.returncode == 0:
            status = result.stdout.strip()
            if "COMPLETE" in status:
                print(f"✅ {stack}: {status}")
                deployed_stacks.append(stack)
            else:
                print(f"⚠️  {stack}: {status}")
                failed_stacks.append(stack)
        else:
            print(f"❌ {stack}: NOT DEPLOYED")
            missing_stacks.append(stack)
    
    print("\n📊 Summary:")
    print(f"✅ Deployed: {len(deployed_stacks)}")
    print(f"⚠️  Failed: {len(failed_stacks)}")
    print(f"❌ Missing: {len(missing_stacks)}")
    
    return len(deployed_stacks), len(failed_stacks), len(missing_stacks)

def get_api_endpoints(environment="dev"):
    """Get API endpoints from deployed stacks"""
    print(f"\n🔗 API Endpoints for {environment}:")
    print("=" * 40)
    
    api_stack = f"AquaChain-API-{environment}"
    
    result = run_command(
        f"aws cloudformation describe-stacks --stack-name {api_stack} --query 'Stacks[0].Outputs' --output json"
    )
    
    if result.returncode == 0:
        try:
            outputs = json.loads(result.stdout)
            
            for output in outputs:
                key = output['OutputKey']
                value = output['OutputValue']
                
                if key == 'RestAPIEndpoint':
                    print(f"🌐 REST API: {value}")
                elif key == 'WebSocketAPIEndpoint':
                    print(f"🔌 WebSocket: {value}")
                elif key == 'UserPoolId':
                    print(f"👤 User Pool: {value}")
                elif key == 'UserPoolClientId':
                    print(f"🔑 Client ID: {value}")
            
            return True
        except json.JSONDecodeError:
            print("❌ Failed to parse stack outputs")
            return False
    else:
        print(f"❌ API stack not found: {api_stack}")
        return False

def check_prerequisites():
    """Check if AWS CLI is configured"""
    print("🔧 Checking prerequisites...")
    
    # Check AWS CLI
    result = run_command("aws --version")
    if result.returncode != 0:
        print("❌ AWS CLI not found")
        return False
    
    # Check AWS credentials
    result = run_command("aws sts get-caller-identity")
    if result.returncode != 0:
        print("❌ AWS credentials not configured")
        return False
    
    try:
        identity = json.loads(result.stdout)
        print(f"✅ AWS Account: {identity['Account']}")
        print(f"✅ AWS User: {identity['Arn']}")
        return True
    except:
        print("❌ Failed to get AWS identity")
        return False

def main():
    """Main function"""
    environment = sys.argv[1] if len(sys.argv) > 1 else "dev"
    
    print("🌊 AquaChain Infrastructure Status Check")
    print("=" * 50)
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met")
        sys.exit(1)
    
    deployed, failed, missing = check_stack_status(environment)
    
    if deployed > 0:
        get_api_endpoints(environment)
    
    print(f"\n📋 Deployment Status:")
    if missing == 0 and failed == 0:
        print("🎉 All infrastructure deployed successfully!")
        print("\n🚀 Next steps:")
        print("1. Create users in Cognito")
        print("2. Configure frontend: cd frontend && npm run switch-to-aws")
        print("3. Start your app: npm start")
    elif missing > 0:
        print(f"⚠️  {missing} stacks not deployed yet")
        print("Run: python deploy-infrastructure.py dev")
    else:
        print("❌ Some stacks have issues. Check CloudFormation console.")

if __name__ == "__main__":
    main()