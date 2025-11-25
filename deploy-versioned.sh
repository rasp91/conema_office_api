#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Change to the script's directory
cd "$(dirname "$0")"

# Pull latest code from git
echo "Pulling latest code from git..."
git pull

# Extract version from FastAPI app
VERSION=$(grep -oP 'version="\K[^"]+' src/app.py)
echo "Detected FastAPI version: $VERSION"

# Build Docker image with version tag
echo "Building Docker image with version tag: $VERSION..."
sudo docker build --no-cache -t roechling-office-fastapi-app:$VERSION .

# Also tag as latest
echo "Tagging as latest..."
sudo docker tag roechling-office-fastapi-app:$VERSION roechling-office-fastapi-app:latest

# Build completed
echo "Deployment complete. Built image: roechling-office-fastapi-app:$VERSION"