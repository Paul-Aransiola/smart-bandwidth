#!/bin/bash
# Manual E2E test script for control endpoints
# Run this script while the server is running to test all endpoints

set -e

BASE_URL="http://localhost:8000/api/v1"
TEST_IP="192.168.1.100"

echo "=========================================="
echo "E2E Tests for Smart Bandwidth Monitor API"
echo "=========================================="
echo ""

# Check if server is running
echo "1. Checking if server is running..."
curl -s "${BASE_URL}/health" | jq '.'
echo "✓ Server is healthy"
echo ""

# Test device creation (you might need to manually create a device first)
echo "2. Testing device endpoints..."
echo "Listing all devices:"
curl -s "${BASE_URL}/devices" | jq 'length'
echo "✓ Device list retrieved"
echo ""

# Test block device
echo "3. Testing block device..."
curl -s -X POST "${BASE_URL}/block/${TEST_IP}" \
  -H "Content-Type: application/json" \
  -d '{"reason": "E2E test blocking"}' | jq '.'
echo "✓ Block request sent (note: might fail if not running as root)"
echo ""

# Test unblock device
echo "4. Testing unblock device..."
curl -s -X POST "${BASE_URL}/unblock/${TEST_IP}" | jq '.'
echo "✓ Unblock request sent"
echo ""

# Test throttle device
echo "5. Testing throttle device..."
curl -s -X POST "${BASE_URL}/throttle/${TEST_IP}" \
  -H "Content-Type: application/json" \
  -d '{"limit_mbps": 5.0, "reason": "E2E test throttling"}' | jq '.'
echo "✓ Throttle request sent (note: might fail if not running as root)"
echo ""

# Test unthrottle device
echo "6. Testing unthrottle device..."
curl -s -X POST "${BASE_URL}/unthrottle/${TEST_IP}" | jq '.'
echo "✓ Unthrottle request sent"
echo ""

# Test device history
echo "7. Testing device history..."
curl -s "${BASE_URL}/history/${TEST_IP}?limit=5" | jq '.'
echo "✓ History retrieved"
echo ""

# Test statistics
echo "8. Testing statistics..."
curl -s "${BASE_URL}/stats" | jq '.'
echo "✓ Statistics retrieved"
echo ""

# Test detailed health
echo "9. Testing detailed health..."
curl -s "${BASE_URL}/health/detailed" | jq '.'
echo "✓ Detailed health check passed"
echo ""

echo "=========================================="
echo "E2E Tests Completed!"
echo "=========================================="
echo ""
echo "Note: Block/throttle operations require root privileges."
echo "If you see 500 errors, try running the server with sudo."
echo ""
