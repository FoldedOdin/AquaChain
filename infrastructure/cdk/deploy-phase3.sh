#!/bin/bash

###############################################################################
# AquaChain Phase 3 Infrastructure Deployment Script
# Deploys Phase 3 infrastructure stack (ML monitoring, certificate rotation)
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      AquaChain Phase 3 Infrastructure Deployment          ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}║  Environment: ${ENVIRONMENT}                                        ║${NC}"
echo -e "${BLUE}║  Region: ${AWS_REGION}                                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Pre-flight Checks
###############################################################################

echo -e "${YELLOW}🔍 Running pre-flight checks...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ AWS CLI found${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi
echo -e "${GREEN}✅ AWS credentials configured${NC}"

# Check CDK
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}❌ CDK not found. Please install: npm install -g aws-cdk${NC}"
    exit 1
fi
echo -e "${GREEN}✅ CDK found: $(cdk --version)${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"

echo ""

###############################################################################
# Install Dependencies
###############################################################################

echo -e "${YELLOW}📦 Installing CDK dependencies...${NC}"

if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found${NC}"
fi

echo ""

###############################################################################
# Synthesize Stack
###############################################################################

echo -e "${YELLOW}🔨 Synthesizing Phase 3 stack...${NC}"

cdk synth AquaChain-Phase3-${ENVIRONMENT} || {
    echo -e "${RED}❌ CDK synthesis failed${NC}"
    exit 1
}

echo -e "${GREEN}✅ Stack synthesized successfully${NC}"
echo ""

###############################################################################
# Deploy Stack
###############################################################################

echo -e "${YELLOW}🚀 Deploying Phase 3 infrastructure...${NC}"

cdk deploy AquaChain-Phase3-${ENVIRONMENT} --require-approval never || {
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
}

echo -e "${GREEN}✅ Phase 3 infrastructure deployed successfully${NC}"
echo ""

###############################################################################
# Verify Deployment
###############################################################################

echo -e "${YELLOW}✅ Verifying deployment...${NC}"

# Get stack outputs
STACK_NAME="AquaChain-Phase3-${ENVIRONMENT}"
OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs' \
    --output json 2>/dev/null)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Stack deployed successfully${NC}"
    echo ""
    echo -e "${BLUE}Stack Outputs:${NC}"
    echo "$OUTPUTS" | python3 -m json.tool
    
    # Extract table names
    MODEL_METRICS_TABLE=$(echo "$OUTPUTS" | python3 -c "import sys, json; outputs = json.load(sys.stdin); print(next((o['OutputValue'] for o in outputs if o['OutputKey'] == 'ModelMetricsTableName'), 'Not found'))")
    CERT_LIFECYCLE_TABLE=$(echo "$OUTPUTS" | python3 -c "import sys, json; outputs = json.load(sys.stdin); print(next((o['OutputValue'] for o in outputs if o['OutputKey'] == 'CertificateLifecycleTableName'), 'Not found'))")
    
    echo ""
    echo -e "${BLUE}Resources Created:${NC}"
    echo -e "  📊 ModelMetrics Table: ${GREEN}${MODEL_METRICS_TABLE}${NC}"
    echo -e "  🔐 CertificateLifecycle Table: ${GREEN}${CERT_LIFECYCLE_TABLE}${NC}"
    
    # Verify tables exist
    if aws dynamodb describe-table --table-name ${MODEL_METRICS_TABLE} &> /dev/null; then
        echo -e "  ${GREEN}✅ ModelMetrics table verified${NC}"
    else
        echo -e "  ${YELLOW}⚠️  ModelMetrics table not found${NC}"
    fi
    
    if aws dynamodb describe-table --table-name ${CERT_LIFECYCLE_TABLE} &> /dev/null; then
        echo -e "  ${GREEN}✅ CertificateLifecycle table verified${NC}"
    else
        echo -e "  ${YELLOW}⚠️  CertificateLifecycle table not found${NC}"
    fi
    
    # Check EventBridge rules
    echo ""
    echo -e "${BLUE}EventBridge Rules:${NC}"
    RULES=$(aws events list-rules --name-prefix "aquachain-rule" --query 'Rules[*].[Name,State]' --output text)
    if [ -n "$RULES" ]; then
        echo "$RULES" | while read name state; do
            echo -e "  ⏰ ${name}: ${GREEN}${state}${NC}"
        done
    else
        echo -e "  ${YELLOW}⚠️  No EventBridge rules found${NC}"
    fi
else
    echo -e "${RED}❌ Failed to retrieve stack outputs${NC}"
    exit 1
fi

echo ""

###############################################################################
# Deployment Summary
###############################################################################

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        🎉 PHASE 3 DEPLOYMENT COMPLETED! 🎉                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Environment:${NC} ${ENVIRONMENT}"
echo -e "${BLUE}Region:${NC} ${AWS_REGION}"
echo -e "${BLUE}Stack:${NC} ${STACK_NAME}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Deploy ML monitoring Lambda functions (Task 2)"
echo "2. Deploy training data validation Lambda (Task 3)"
echo "3. Deploy OTA update system (Task 4)"
echo "4. Deploy certificate rotation Lambda (Task 5)"
echo "5. Deploy dependency scanner Lambda (Task 6)"
echo "6. Deploy SBOM generator (Task 7)"
echo "7. Set up performance monitoring dashboard (Task 8)"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "- Phase 3 Infrastructure: infrastructure/cdk/PHASE3_INFRASTRUCTURE.md"
echo "- Requirements: .kiro/specs/phase-3-high-priority/requirements.md"
echo "- Design: .kiro/specs/phase-3-high-priority/design.md"
echo "- Tasks: .kiro/specs/phase-3-high-priority/tasks.md"
echo ""
echo -e "${GREEN}✨ Ready for Phase 3 implementation! ✨${NC}"
