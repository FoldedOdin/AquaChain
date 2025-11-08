#!/usr/bin/env python3
"""
Setup AWS environment for AquaChain deployment
"""

import os
import subprocess
import json
from pathlib import Path

def run_command(command, check=True):
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
        if check:
            print(f"❌ Command failed: {e}")
            if e.stderr:
                print(f"Error: {e.stderr}")
        return e

def check_aws_cli():
    """Check if AWS CLI is installed and configured"""
    print("🔍 Checking AWS CLI...")
    
    # Check if AWS CLI is installed
    result = run_command("aws --version", check=False)
    if result.returncode != 0:
        print("❌ AWS CLI not found")
        print("📥 Please install AWS CLI:")
        print("   Windows: https://aws.amazon.com/cli/")
        print("   macOS: brew install awscli")
        print("   Linux: sudo apt install awscli")
        return False
    
    print(f"✅ AWS CLI installed: {result.stdout.strip()}")
    
    # Check if credentials are configured
    result = run_command("aws sts get-caller-identity", check=False)
    if result.returncode != 0:
        print("❌ AWS credentials not configured")
        return False
    
    try:
        identity = json.loads(result.stdout)
        print(f"✅ AWS Account: {identity['Account']}")
        print(f"✅ AWS User: {identity['Arn']}")
        return True, identity
    except:
        print("❌ Failed to parse AWS identity")
        return False

def create_env_file():
    """Create .env file with AWS configuration"""
    print("\n📝 Creating .env file...")
    
    # Get AWS identity
    aws_check = check_aws_cli()
    if not aws_check:
        print("❌ Cannot create .env file without AWS credentials")
        return False
    
    _, identity = aws_check
    account_id = identity['Account']
    
    # Get current region
    result = run_command("aws configure get region", check=False)
    region = result.stdout.strip() if result.returncode == 0 else "us-east-1"
    
    # Create .env content
    env_content = f"""# AWS Configuration for AquaChain Deployment
# Generated on {subprocess.run(['date'], capture_output=True, text=True, shell=True).stdout.strip()}

# AWS Account Configuration
AWS_ACCOUNT_ID={account_id}
AWS_DEFAULT_REGION={region}
CDK_DEFAULT_ACCOUNT={account_id}
CDK_DEFAULT_REGION={region}

# Environment Configuration
ENVIRONMENT=dev
PROJECT_NAME=aquachain

# Domain Configuration (optional - update with your domain)
DOMAIN_NAME=dev.aquachain.io
# CERTIFICATE_ARN=arn:aws:acm:{region}:{account_id}:certificate/your-cert-id

# Notification Configuration (optional)
ALERT_EMAIL=alerts@yourdomain.com
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
# PAGERDUTY_INTEGRATION_KEY=your-pagerduty-key

# Google OAuth Configuration (optional - for Cognito social login)
# GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
# GOOGLE_CLIENT_SECRET=your-google-client-secret

# Cross-account Replication (for staging/prod environments)
# REPLICA_ACCOUNT_ID=987654321098
# REPLICA_REGION=us-west-2
"""
    
    # Write .env file
    env_file = Path(__file__).parent / ".env"
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created {env_file}")
    print("\n📋 Configuration Summary:")
    print(f"   Account ID: {account_id}")
    print(f"   Region: {region}")
    print(f"   Environment: dev")
    
    return True

def setup_aws_credentials():
    """Guide user through AWS credentials setup"""
    print("🔧 AWS Credentials Setup")
    print("=" * 30)
    
    print("You need AWS credentials to deploy infrastructure.")
    print("Choose your preferred method:\n")
    
    print("1. AWS CLI Configuration (Recommended)")
    print("   - Run: aws configure")
    print("   - Enter your Access Key ID and Secret Access Key")
    print("   - Set default region (us-east-1)")
    print("   - Set output format (json)")
    
    print("\n2. Environment Variables")
    print("   - Set AWS_ACCESS_KEY_ID")
    print("   - Set AWS_SECRET_ACCESS_KEY")
    print("   - Set AWS_DEFAULT_REGION")
    
    print("\n3. IAM Roles (for EC2/Lambda)")
    print("   - Attach IAM role to your compute instance")
    print("   - No credentials needed in code")
    
    print("\n4. AWS SSO (for organizations)")
    print("   - Run: aws configure sso")
    print("   - Follow SSO setup process")
    
    choice = input("\nWhich method would you like to use? (1-4): ")
    
    if choice == "1":
        print("\n🔧 Running AWS CLI configuration...")
        print("You'll be prompted for:")
        print("- AWS Access Key ID")
        print("- AWS Secret Access Key") 
        print("- Default region name (recommend: us-east-1)")
        print("- Default output format (recommend: json)")
        
        result = run_command("aws configure", check=False)
        if result.returncode == 0:
            print("✅ AWS CLI configured successfully")
            return True
        else:
            print("❌ AWS CLI configuration failed")
            return False
    
    elif choice == "2":
        print("\n📝 Set these environment variables:")
        print("export AWS_ACCESS_KEY_ID=your-access-key-id")
        print("export AWS_SECRET_ACCESS_KEY=your-secret-access-key")
        print("export AWS_DEFAULT_REGION=us-east-1")
        print("\nOr add them to your .env file")
        return False
    
    elif choice == "3":
        print("\n🔧 IAM Role Setup:")
        print("1. Create IAM role with required permissions")
        print("2. Attach role to your EC2 instance")
        print("3. No additional configuration needed")
        return False
    
    elif choice == "4":
        print("\n🔧 AWS SSO Setup:")
        result = run_command("aws configure sso", check=False)
        return result.returncode == 0
    
    else:
        print("❌ Invalid choice")
        return False

def main():
    """Main setup function"""
    print("🌊 AquaChain AWS Environment Setup")
    print("=" * 40)
    
    # Check if AWS CLI is available and configured
    aws_check = check_aws_cli()
    
    if not aws_check:
        print("\n🔧 AWS credentials not configured")
        if setup_aws_credentials():
            # Recheck after setup
            aws_check = check_aws_cli()
        else:
            print("\n❌ Setup incomplete. Please configure AWS credentials and try again.")
            return False
    
    if aws_check:
        # Create .env file
        if create_env_file():
            print("\n🎉 AWS environment setup complete!")
            print("\n🚀 Next steps:")
            print("1. Review and update .env file if needed")
            print("2. Run deployment: python deploy-infrastructure.py dev")
            print("3. Check status: python check-deployment.py dev")
            return True
    
    return False

if __name__ == "__main__":
    main()