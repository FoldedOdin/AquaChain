#!/bin/bash
# Start AquaChain Local Development
# This starts both frontend and mock backend

echo "========================================"
echo "  AquaChain - Local Development"
echo "========================================"
echo ""

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "ERROR: Dependencies not installed!"
    echo ""
    echo "Please run setup-local.sh first:"
    echo "  chmod +x setup-local.sh"
    echo "  ./setup-local.sh"
    echo ""
    exit 1
fi

echo "Starting local development environment..."
echo ""
echo "Frontend: http://localhost:3000"
echo "Mock API: http://localhost:3002"
echo ""
echo "Use OTP: 123456 for email verification"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""
echo "========================================"
echo ""

cd frontend

# Start both dev server and React app
npm run start:full
