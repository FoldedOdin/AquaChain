#!/bin/bash

# Check CloudWatch logs for the orders Lambda function
# This helps debug the 500 error

echo "Fetching latest CloudWatch logs for orders Lambda..."
echo "=================================================="

# Find the Lambda function name
FUNCTION_NAME=$(aws lambda list-functions --query "Functions[?contains(FunctionName, 'order')].FunctionName" --output text | head -1)

if [ -z "$FUNCTION_NAME" ]; then
    echo "❌ No orders Lambda function found"
    exit 1
fi

echo "Found Lambda: $FUNCTION_NAME"
echo ""

# Get the log group name
LOG_GROUP="/aws/lambda/$FUNCTION_NAME"

echo "Fetching logs from: $LOG_GROUP"
echo ""

# Get the latest log stream
LATEST_STREAM=$(aws logs describe-log-streams \
    --log-group-name "$LOG_GROUP" \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --query 'logStreams[0].logStreamName' \
    --output text)

if [ -z "$LATEST_STREAM" ] || [ "$LATEST_STREAM" == "None" ]; then
    echo "❌ No log streams found"
    exit 1
fi

echo "Latest log stream: $LATEST_STREAM"
echo ""
echo "Recent log events:"
echo "=================="

# Get the latest log events
aws logs get-log-events \
    --log-group-name "$LOG_GROUP" \
    --log-stream-name "$LATEST_STREAM" \
    --limit 50 \
    --query 'events[*].[timestamp,message]' \
    --output text | \
    while IFS=$'\t' read -r timestamp message; do
        # Convert timestamp to readable format
        date_str=$(date -d "@$((timestamp/1000))" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r "$((timestamp/1000))" '+%Y-%m-%d %H:%M:%S' 2>/dev/null)
        echo "[$date_str] $message"
    done

echo ""
echo "=================================================="
echo "Look for ERROR or Exception messages above"
