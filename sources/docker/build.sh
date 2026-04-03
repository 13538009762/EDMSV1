#!/bin/bash

# EDMS Docker Build Script for Linux/macOS
# This script prepares runtime files in bin/ directory and builds Docker images

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BIN_DIR="$(dirname "$SCRIPT_DIR")/bin/"
DATA_DIR="$BIN_DIR/data"
ENV_FILE="$BIN_DIR/.env"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

echo "============================================"
echo "   EDMS Docker Build Script"
echo "============================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH"
    echo "Please install Docker from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "ERROR: Docker daemon is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo "[OK] Docker is running"
echo ""

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "ERROR: docker-compose is not installed"
    exit 1
fi

# Create .env file in bin/ directory if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file in bin/ directory..."
    cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
    echo "[OK] Created .env file"
    
    # Auto-generate JWT_SECRET_KEY if empty
    if grep -q "^JWT_SECRET_KEY=$" "$ENV_FILE" || ! grep -q "^JWT_SECRET_KEY=" "$ENV_FILE"; then
        echo "Auto-generating JWT_SECRET_KEY..."
        JWT_KEY=$(openssl rand -hex 32)
        # Update .env file with generated key
        grep -v "^JWT_SECRET_KEY=" "$ENV_FILE" > "$ENV_FILE.tmp" || true
        echo "JWT_SECRET_KEY=$JWT_KEY" >> "$ENV_FILE.tmp"
        mv "$ENV_FILE.tmp" "$ENV_FILE"
        echo "[OK] JWT_SECRET_KEY generated"
    fi
    echo ""
else
    echo "[OK] .env file already exists in bin/ directory"
    echo ""
fi

# Create data directory in bin/ directory if it doesn't exist
if [ ! -d "$DATA_DIR" ]; then
    echo "Creating data directory in bin/ directory..."
    mkdir -p "$DATA_DIR/backend"
    echo "[OK] Created data directory"
    echo ""
else
    echo "[OK] Data directory already exists in bin/ directory"
    echo ""
fi

# Build Docker images
echo "Building Docker images..."
echo "This may take a while on first run..."
echo ""
$COMPOSE_CMD -f "$COMPOSE_FILE" build
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build Docker images"
    exit 1
fi

# Export images to bin/images/ directory
echo ""
echo "Exporting Docker images to bin/images/ directory..."
mkdir -p "$BIN_DIR/images"
docker save edms-backend:latest -o "$BIN_DIR/images/edms-backend.tar"
if [ $? -eq 0 ]; then
    echo "[OK] Exported edms-backend.tar"
else
    echo "ERROR: Failed to export edms-backend"
    exit 1
fi

docker save edms-frontend:latest -o "$BIN_DIR/images/edms-frontend.tar"
if [ $? -eq 0 ]; then
    echo "[OK] Exported edms-frontend.tar"
else
    echo "ERROR: Failed to export edms-frontend"
    exit 1
fi

# Copy docker-compose.yml to bin/ directory for runtime
echo "Copying docker-compose.yml to bin/ directory..."
cp "$COMPOSE_FILE" "$BIN_DIR/docker-compose.yml"
if [ -f "$BIN_DIR/docker-compose.yml" ]; then
    echo "[OK] docker-compose.yml copied to bin/ directory"
else
    echo "ERROR: Failed to copy docker-compose.yml"
    exit 1
fi

echo ""
echo "============================================"
echo "   EDMS Build Complete!"
echo "============================================"
echo ""
echo "Runtime files created in:"
echo "  $BIN_DIR"
echo ""
echo "Files:"
echo "  - .env (environment configuration)"
echo "  - data/ (persistent data)"
echo ""
echo "Next steps:"
echo "  1. Run bin/Linux/start.sh to start the services"
echo "  2. Access the application at http://localhost"
echo ""
echo "To rebuild:"
echo "  Run this script again"
echo ""
echo "To clean up:"
echo "  $COMPOSE_CMD -f \"$COMPOSE_FILE\" down -v"
echo ""

# Wait for user to see the message
read -p "Press Enter to continue..."
