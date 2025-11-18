#!/bin/bash
# Deployment script for Smart Bandwidth Monitor

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Smart Bandwidth Monitor Deployment ===${NC}\n"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please copy .env.production to .env and configure it:${NC}"
    echo "  cp .env.production .env"
    echo "  nano .env  # Edit with your settings"
    exit 1
fi

# Check if SECRET_KEY is set
if grep -q "CHANGE_THIS_TO_A_RANDOM_64_CHARACTER_STRING" .env 2>/dev/null; then
    echo -e "${RED}Error: SECRET_KEY not configured!${NC}"
    echo -e "${YELLOW}Generate a secure secret key:${NC}"
    echo "  openssl rand -hex 32"
    echo -e "${YELLOW}Then update SECRET_KEY in .env file${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Determine docker compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}\n"

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
$DOCKER_COMPOSE down || true

# Pull latest images
echo -e "${YELLOW}Pulling latest images...${NC}"
$DOCKER_COMPOSE pull || true

# Build application image
echo -e "${YELLOW}Building application image...${NC}"
$DOCKER_COMPOSE build --no-cache

# Start services
echo -e "${YELLOW}Starting services...${NC}"
$DOCKER_COMPOSE up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check service status
echo -e "\n${GREEN}=== Service Status ===${NC}"
$DOCKER_COMPOSE ps

# Check API health
echo -e "\n${YELLOW}Checking API health...${NC}"
for i in {1..30}; do
    if curl -sf http://localhost:8000/api/v1/health > /dev/null; then
        echo -e "${GREEN}✓ API is healthy!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ API health check failed${NC}"
        echo -e "${YELLOW}Check logs with: $DOCKER_COMPOSE logs api${NC}"
        exit 1
    fi
    echo -n "."
    sleep 2
done

# Display logs
echo -e "\n${YELLOW}Recent logs:${NC}"
$DOCKER_COMPOSE logs --tail=20

echo -e "\n${GREEN}=== Deployment Complete! ===${NC}"
echo -e "API: http://localhost:8000"
echo -e "Dashboard: http://localhost:3000"
echo -e "API Docs: http://localhost:8000/docs"
echo -e "Health Check: http://localhost:8000/api/v1/health"
echo -e "\n${YELLOW}Useful commands:${NC}"
echo -e "  View logs: $DOCKER_COMPOSE logs -f"
echo -e "  Stop services: $DOCKER_COMPOSE down"
echo -e "  Restart services: $DOCKER_COMPOSE restart"
echo -e "  View status: $DOCKER_COMPOSE ps"
