#!/bin/bash

# EDMS Docker Stop Script for Linux/macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/../docker-compose.yml"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "============================================"
echo "   EDMS Docker Stop Script"
echo "============================================"
echo ""

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}ERROR: docker-compose is not installed${NC}"
    exit 1
fi

# Stop and remove containers
echo "Stopping EDMS services..."
docker stop edms-backend edms-frontend 2>/dev/null || true
docker rm edms-backend edms-frontend 2>/dev/null || true
docker network rm bin_edms-network 2>/dev/null || true

echo ""
echo -e "${GREEN}[OK]${NC} Services stopped successfully"
echo ""
read -p "Press Enter to continue..."
