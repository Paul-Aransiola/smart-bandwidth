#!/bin/bash
# Start the Smart Bandwidth Monitor with network monitoring enabled
# Requires sudo for packet capture capabilities

echo "🚀 Starting Smart Bandwidth Monitor with Network Monitoring"
echo "⚠️  This requires elevated privileges for packet capture"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo:"
    echo "sudo ./start_with_monitoring.sh"
    exit 1
fi

# Get the actual user who ran sudo
ACTUAL_USER="${SUDO_USER:-$USER}"
USER_HOME=$(eval echo ~$ACTUAL_USER)

echo "📡 Network monitoring: ENABLED"
echo "🔧 Interface: en0"
echo "⏱️  Monitoring interval: 30 seconds"
echo ""

# Activate poetry environment and run
cd "$(dirname "$0")"
sudo -u "$ACTUAL_USER" poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
