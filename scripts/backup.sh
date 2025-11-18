#!/bin/bash
# Backup script for Smart Bandwidth Monitor

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="bandwidth_monitor_backup_${DATE}"

echo -e "${GREEN}=== Creating Backup ===${NC}\n"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup archive
echo -e "${YELLOW}Creating backup archive...${NC}"
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='htmlcov' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='backups' \
    .env \
    bandwidth_monitor.db \
    logs 2>/dev/null || true

echo -e "${GREEN}✓ Backup created: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz${NC}"

# Backup Docker volumes (if using Docker)
if command -v docker &> /dev/null && docker ps -q --filter name=bandwidth-monitor > /dev/null; then
    echo -e "\n${YELLOW}Backing up Docker volumes...${NC}"
    
    # Backup Redis data
    docker run --rm \
        -v bandwidth-monitor_redis-data:/data \
        -v "$(pwd)/${BACKUP_DIR}:/backup" \
        alpine \
        tar czf "/backup/redis_${DATE}.tar.gz" /data 2>/dev/null || true
    
    echo -e "${GREEN}✓ Docker volumes backed up${NC}"
fi

# Clean up old backups (keep last 7 days)
echo -e "\n${YELLOW}Cleaning up old backups...${NC}"
find "$BACKUP_DIR" -name "bandwidth_monitor_backup_*.tar.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "redis_*.tar.gz" -mtime +7 -delete
echo -e "${GREEN}✓ Cleanup complete${NC}"

# Display backup info
echo -e "\n${GREEN}=== Backup Summary ===${NC}"
ls -lh "${BACKUP_DIR}" | tail -n 5

echo -e "\n${GREEN}✓ Backup complete!${NC}"
echo -e "Location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
