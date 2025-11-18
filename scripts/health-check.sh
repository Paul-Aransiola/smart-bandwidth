#!/bin/bash
# Health check script for Smart Bandwidth Monitor

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_URL="${API_URL:-http://localhost:8000}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

echo -e "${GREEN}=== Health Check ===${NC}\n"

# Check API health
echo -n "API Health: "
if curl -sf "${API_URL}/api/v1/health" > /dev/null; then
    response=$(curl -s "${API_URL}/api/v1/health")
    echo -e "${GREEN}✓ Healthy${NC}"
    echo "  $response"
else
    echo -e "${RED}✗ Failed${NC}"
    exit 1
fi

# Check Redis
echo -n "Redis: "
if command -v redis-cli &> /dev/null; then
    if redis-cli -h $REDIS_HOST -p $REDIS_PORT ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Connected${NC}"
    else
        echo -e "${YELLOW}⚠ Not reachable${NC}"
    fi
else
    echo -e "${YELLOW}⚠ redis-cli not installed (skipping)${NC}"
fi

# Check disk space
echo -n "Disk Space: "
disk_usage=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $disk_usage -lt 80 ]; then
    echo -e "${GREEN}✓ ${disk_usage}% used${NC}"
elif [ $disk_usage -lt 90 ]; then
    echo -e "${YELLOW}⚠ ${disk_usage}% used (warning)${NC}"
else
    echo -e "${RED}✗ ${disk_usage}% used (critical)${NC}"
fi

# Check memory
echo -n "Memory: "
if command -v free &> /dev/null; then
    mem_usage=$(free | grep Mem | awk '{printf("%.0f", ($3/$2) * 100)}')
    if [ $mem_usage -lt 80 ]; then
        echo -e "${GREEN}✓ ${mem_usage}% used${NC}"
    elif [ $mem_usage -lt 90 ]; then
        echo -e "${YELLOW}⚠ ${mem_usage}% used (warning)${NC}"
    else
        echo -e "${RED}✗ ${mem_usage}% used (critical)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ free command not available (skipping)${NC}"
fi

# Check if services are running (Docker)
if command -v docker &> /dev/null; then
    echo -e "\n${GREEN}Docker Services:${NC}"
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "bandwidth-monitor"; then
        docker ps --format "  {{.Names}}: {{.Status}}" | grep "bandwidth-monitor"
    else
        echo -e "${YELLOW}  No Docker services found${NC}"
    fi
fi

echo -e "\n${GREEN}✓ Health check complete${NC}"
