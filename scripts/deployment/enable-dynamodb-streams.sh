#!/bin/bash
# Enable DynamoDB Streams on existing tables for Global Monitoring Dashboard
# Requirements: 15.8, 19.8, 3.2

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Enabling DynamoDB Streams for Global Monitoring Dashboard${NC}"
echo "=========================================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Get AWS region from environment or use default
REGION=${AWS_REGION:-us-east-1}
echo -e "Using region: ${YELLOW}${REGION}${NC}"

# Function to enable stream on a table
enable_stream() {
    local table_name=$1
    local purpose=$2
    
    echo ""
    echo -e "Enabling stream on ${YELLOW}${table_name}${NC}..."
    echo "Purpose: ${purpose}"
    
    # Check if table exists
    if ! aws dynamodb describe-table --table-name "${table_name}" --region "${REGION}" &> /dev/null; then
        echo -e "${RED}Error: Table ${table_name} does not exist${NC}"
        return 1
    fi
    
    # Check if stream is already enabled
    STREAM_STATUS=$(aws dynamodb describe-table \
        --table-name "${table_name}" \
        --region "${REGION}" \
        --query 'Table.StreamSpecification.StreamEnabled' \
        --output text 2>/dev/null || echo "None")
    
    if [ "${STREAM_STATUS}" == "True" ]; then
        echo -e "${GREEN}✓ Stream already enabled on ${table_name}${NC}"
        
        # Get stream ARN
        STREAM_ARN=$(aws dynamodb describe-table \
            --table-name "${table_name}" \
            --region "${REGION}" \
            --query 'Table.LatestStreamArn' \
            --output text)
        echo "  Stream ARN: ${STREAM_ARN}"
        return 0
    fi
    
    # Enable stream
    aws dynamodb update-table \
        --table-name "${table_name}" \
        --region "${REGION}" \
        --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully enabled stream on ${table_name}${NC}"
        
        # Wait a moment for stream to be created
        sleep 2
        
        # Get stream ARN
        STREAM_ARN=$(aws dynamodb describe-table \
            --table-name "${table_name}" \
            --region "${REGION}" \
            --query 'Table.LatestStreamArn' \
            --output text)
        echo "  Stream ARN: ${STREAM_ARN}"
    else
        echo -e "${RED}✗ Failed to enable stream on ${table_name}${NC}"
        return 1
    fi
}

# Enable stream on AquaChain-Readings table
enable_stream "AquaChain-Readings" "Trigger incremental aggregation Lambda"

# Enable stream on AquaChain-Alerts table
enable_stream "AquaChain-Alerts" "Trigger alert stream Lambda for WebSocket push"

echo ""
echo -e "${GREEN}=========================================================="
echo "DynamoDB Streams configuration complete!"
echo "==========================================================${NC}"
echo ""
echo "Next steps:"
echo "1. Deploy the Global Monitoring Dashboard stack:"
echo "   cd infrastructure/cdk"
echo "   cdk deploy AquaChain-GlobalMonitoringDashboard-dev"
echo ""
echo "2. Verify the new tables were created:"
echo "   aws dynamodb list-tables --region ${REGION}"
echo ""
echo "3. Check stream ARNs for Lambda trigger configuration:"
echo "   aws dynamodb describe-table --table-name AquaChain-Readings --region ${REGION}"
echo "   aws dynamodb describe-table --table-name AquaChain-Alerts --region ${REGION}"
