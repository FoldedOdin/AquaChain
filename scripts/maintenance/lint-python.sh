#!/bin/bash
# Python linting script for Lambda functions
# This script runs Pylint on all Python Lambda functions

set -e

echo "🔍 Running Pylint on Lambda functions..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
OVERALL_STATUS=0
FAILED_FUNCTIONS=()

# Find all Lambda function directories
LAMBDA_DIRS=$(find lambda -maxdepth 1 -type d -not -path lambda -not -path "*/\.*")

if [ -z "$LAMBDA_DIRS" ]; then
    echo -e "${YELLOW}⚠️  No Lambda function directories found${NC}"
    exit 0
fi

# Run Pylint on each Lambda function
for lambda_dir in $LAMBDA_DIRS; do
    function_name=$(basename "$lambda_dir")
    
    # Skip if no Python files exist
    if ! find "$lambda_dir" -maxdepth 1 -name "*.py" -not -name "test_*.py" | grep -q .; then
        echo -e "${YELLOW}⏭️  Skipping $function_name (no Python files)${NC}"
        continue
    fi
    
    echo ""
    echo "📦 Linting $function_name..."
    
    # Run Pylint
    if pylint "$lambda_dir"/*.py --rcfile=.pylintrc --score=yes 2>&1; then
        echo -e "${GREEN}✅ $function_name passed${NC}"
    else
        LINT_STATUS=$?
        if [ $LINT_STATUS -ne 0 ]; then
            echo -e "${RED}❌ $function_name failed with exit code $LINT_STATUS${NC}"
            FAILED_FUNCTIONS+=("$function_name")
            OVERALL_STATUS=1
        fi
    fi
done

# Also lint shared modules
if [ -d "lambda/shared" ]; then
    echo ""
    echo "📦 Linting shared modules..."
    if pylint lambda/shared/*.py --rcfile=.pylintrc --score=yes 2>&1; then
        echo -e "${GREEN}✅ Shared modules passed${NC}"
    else
        echo -e "${RED}❌ Shared modules failed${NC}"
        FAILED_FUNCTIONS+=("shared")
        OVERALL_STATUS=1
    fi
fi

# Print summary
echo ""
echo "================================"
if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ All Python linting checks passed!${NC}"
else
    echo -e "${RED}❌ Python linting failed for:${NC}"
    for func in "${FAILED_FUNCTIONS[@]}"; do
        echo -e "${RED}   - $func${NC}"
    done
fi
echo "================================"

exit $OVERALL_STATUS
