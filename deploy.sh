#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Change to the script's directory
SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
cd "$SCRIPT_DIR"
echo "Running from: $(pwd)"

# Pull latest code from git
echo "Pulling latest code from git..."
git pull

# Set docker build name
BUILD_NAME="roechling-office-fastapi-app"

# Extract version from FastAPI app
VERSION=$(grep -oP 'version="\K[^"]+' src/app.py)
if [[ -z "$VERSION" ]]; then
    echo "ERROR: Could not extract version from src/app.py"
    exit 1
fi
echo "Detected FastAPI version: $VERSION"

# Build Docker image with version tag
echo "Building Docker image with version tag: $VERSION..."
sudo docker build --no-cache -t "$BUILD_NAME:$VERSION" .

# Also tag as latest
echo "Tagging as latest..."
sudo docker tag "$BUILD_NAME:$VERSION" "$BUILD_NAME:latest"
# Build completed
echo "Build complete. Image: $BUILD_NAME:$VERSION"

# Temporarily disable exit on error for user input
set +e
read -p "Do you want to continue with deployment? (y/N): " answer
read_exit_code=$?
set -e

# Check if read was interrupted (Ctrl+C)
if [[ $read_exit_code -ne 0 ]]; then
    echo ""
    echo "Operation cancelled or interrupted."
    exit 1
fi

# Default to 'N' if answer is empty
answer=${answer:-N}

if [[ "$answer" =~ ^[Yy]$ ]]; then
    # Show Docker containers status
    echo "Current Docker containers status:"
    sudo docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$BUILD_NAME" || echo "No $BUILD_NAME containers currently running"

    # Docker stop compose
    sudo docker compose -p "$BUILD_NAME" down

    # Start containers
    sudo docker compose -p "$BUILD_NAME" up -d

    # Show status
    sudo docker compose -p "$BUILD_NAME" ps
else
    echo "Deployment skipped."
fi
