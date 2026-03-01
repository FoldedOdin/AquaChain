#!/bin/bash
# Quick Phase 1 Testing Script (Bash/curl version)
# For Linux/Mac or Git Bash on Windows

set -e

API_BASE="https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev"

echo "============================================================"
echo "  Phase 1 Quick Test (curl)"
echo "============================================================"
echo ""

# Get JWT token
echo "Please enter your admin JWT token:"
echo "(Get from browser localStorage: aquachain_token)"
read -r TOKEN

if [ -z "$TOKEN" ]; then
    echo "Error: Token is required"
    exit 1
fi

echo ""
echo "Testing endpoints..."
echo ""

# Test 1: Get Current Configuration
echo "[1/4] GET /api/admin/system/configuration"
echo "------------------------------------------------------------"
curl -s -X GET "$API_BASE/api/admin/system/configuration" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" | jq '.' || echo "Failed"
echo ""
echo ""

# Test 2: Validate Configuration (Valid)
echo "[2/4] POST /api/admin/system/configuration/validate (Valid)"
echo "------------------------------------------------------------"
curl -s -X POST "$API_BASE/api/admin/system/configuration/validate" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "alertThresholds": {
            "global": {
                "pH": {
                    "min": 6.5,
                    "max": 8.5
                }
            }
        }
    }' | jq '.' || echo "Failed"
echo ""
echo ""

# Test 3: Validate Configuration (Invalid)
echo "[3/4] POST /api/admin/system/configuration/validate (Invalid)"
echo "------------------------------------------------------------"
curl -s -X POST "$API_BASE/api/admin/system/configuration/validate" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "alertThresholds": {
            "global": {
                "pH": {
                    "min": 15.0,
                    "max": 8.5
                }
            }
        },
        "systemLimits": {
            "dataRetentionDays": 10
        }
    }' | jq '.' || echo "Failed"
echo ""
echo ""

# Test 4: Get Configuration History
echo "[4/4] GET /api/admin/system/configuration/history"
echo "------------------------------------------------------------"
curl -s -X GET "$API_BASE/api/admin/system/configuration/history?limit=5" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" | jq '.' || echo "Failed"
echo ""
echo ""

echo "============================================================"
echo "  Testing Complete"
echo "============================================================"
echo ""
echo "If all tests returned JSON responses, Phase 1 is working!"
echo ""
