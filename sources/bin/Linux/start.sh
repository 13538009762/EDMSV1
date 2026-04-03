#!/bin/bash

# EDMS Docker Startup Script for Linux/macOS
# This script starts the EDMS containers using files in bin/ directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/../docker-compose.yml"
ENV_FILE="$SCRIPT_DIR/../.env"
DATA_DIR="$SCRIPT_DIR/../data"
IMAGES_DIR="$SCRIPT_DIR/../images"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "   EDMS Docker Startup Script"
echo "============================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}ERROR: Docker daemon is not running${NC}"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Docker is running"
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

# Check if .env file exists in bin/ directory
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}ERROR: .env file not found in bin/ directory!${NC}"
    echo "Please run docker/build.sh first to initialize the environment."
    echo ""
    echo "Expected location: $ENV_FILE"
    exit 1
fi

# Check if data directory exists in bin/ directory
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}ERROR: Data directory not found in bin/ directory!${NC}"
    echo "Please run docker/build.sh first to initialize the environment."
    echo ""
    exit 1
fi

# Check if images exist, import if needed
echo "Checking Docker images..."

if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "edms-backend:latest"; then
    echo "edms-backend image not found, checking for export file..."
    if [ -f "$IMAGES_DIR/edms-backend.tar" ]; then
        echo "Importing edms-backend from $IMAGES_DIR/edms-backend.tar..."
        docker load -i "$IMAGES_DIR/edms-backend.tar"
        if [ $? -ne 0 ]; then
            echo -e "${RED}ERROR: Failed to import edms-backend${NC}"
            exit 1
        fi
        echo -e "${GREEN}[OK]${NC} edms-backend imported"
    else
        echo -e "${RED}ERROR: edms-backend image not found and no export file available${NC}"
        echo "Please run docker/build.sh first to build and export images."
        exit 1
    fi
else
    echo -e "${GREEN}[OK]${NC} edms-backend image exists"
fi

if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "edms-frontend:latest"; then
    echo "edms-frontend image not found, checking for export file..."
    if [ -f "$IMAGES_DIR/edms-frontend.tar" ]; then
        echo "Importing edms-frontend from $IMAGES_DIR/edms-frontend.tar..."
        docker load -i "$IMAGES_DIR/edms-frontend.tar"
        if [ $? -ne 0 ]; then
            echo -e "${RED}ERROR: Failed to import edms-frontend${NC}"
            exit 1
        fi
        echo -e "${GREEN}[OK]${NC} edms-frontend imported"
    else
        echo -e "${RED}ERROR: edms-frontend image not found and no export file available${NC}"
        echo "Please run docker/build.sh first to build and export images."
        exit 1
    fi
else
    echo -e "${GREEN}[OK]${NC} edms-frontend image exists"
fi

echo ""

# Check container status
echo "Checking container status..."
if $COMPOSE_CMD -f "$COMPOSE_FILE" ps 2>/dev/null | grep -q "Up "; then
    echo -e "${GREEN}[OK]${NC} Services are already running"
    echo ""
    echo "Container status:"
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps
    echo ""
    echo -e "To restart: ${YELLOW}$COMPOSE_CMD -f \"$COMPOSE_FILE\" restart${NC}"
    exit 0
else
    echo "Containers not found. Starting services..."
    echo ""
    
    # Start containers
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --no-build 2>&1 | grep -E "Creating|Starting|Started|Created|network" || true
    
    # Wait for containers to start
    sleep 5
    
    # Verify containers are actually running
    if docker ps --format "{{.Names}}" | grep -E "edms-backend|edms-frontend" | wc -l | grep -q "2"; then
        echo ""
        echo -e "${GREEN}[OK]${NC} Containers started successfully"
    else
        echo ""
        echo -e "${RED}ERROR: Failed to start containers${NC}"
        exit 1
    fi
fi

echo ""
echo "============================================"
echo "   EDMS Deployment Complete!"
echo "============================================"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost"
echo "  Backend API: http://localhost/api"
echo ""
echo "To view logs:"
echo "  $COMPOSE_CMD -f \"$COMPOSE_FILE\" logs -f"
echo ""
echo "To stop services:"
echo "  $COMPOSE_CMD -f \"$COMPOSE_FILE\" down"
echo ""
echo "To restart services:"
echo "  $COMPOSE_CMD -f \"$COMPOSE_FILE\" restart"
echo ""

# Show container status
echo "Current container status:"
docker ps --format "{{.Names}}\t{{.Image}}\t{{.Command}}\t{{.Status}}\t{{.Ports}}" | grep -E "edms-backend|edms-frontend"

echo ""
read -p "Press Enter to continue..."
