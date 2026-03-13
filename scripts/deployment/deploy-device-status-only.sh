#!/bin/bash
# Deploy Device Status Monitor Stack Only
# Linux/Mac script for deploying device status monitoring

set -e

echo ""
echo "========================================"
echo "   AquaChain Device Status Monitor"
echo "========================================"
echo ""

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "ERROR: AWS CDK is not installed or not in PATH"
    echo "Please install CDK: npm install -g aws-cdk"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS credentials not configured"
    echo "Please run: aws configure"
    exit 1
fi

# Set environment
ENVIRONMENT=${1:-dev}
echo "Environment: $ENVIRONMENT"
echo ""

# Change to CDK directory
cd "$(dirname "$0")/../../infrastructure/cdk"

echo "Deploying Device Status Monitor Stack..."
echo ""

# Deploy the stack
if cdk deploy AquaChain-DeviceStatusMonitor-$ENVIRONMENT --require-approval never; then
    echo ""
    echo "========================================"
    echo "   Deployment Successful!"
    echo "========================================"
    echo ""
    echo "Device Status Monitor is now active:"
    echo "  • Monitoring device connectivity every 2 minutes"
    echo "  • CloudWatch metrics and alarms configured"
    echo "  • Dashboard available in AWS Console"
    echo ""
    echo "Next steps:"
    echo "  1. Test the deployment: python ../../scripts/testing/test-device-status-monitor.py"
    echo "  2. View dashboard: https://console.aws.amazon.com/cloudwatch/home#dashboards:name=AquaChain-DeviceStatus"
    echo "  3. Check device status in frontend"
    echo ""
else
    echo ""
    echo "========================================"
    echo "   Deployment Failed!"
    echo "========================================"
    echo ""
    echo "Please check the error messages above."
    echo "Common issues:"
    echo "  • Missing DynamoDB tables (deploy data stack first)"
    echo "  • Insufficient IAM permissions"
    echo "  • Region mismatch"
    echo ""
    exit 1
fi