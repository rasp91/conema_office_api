#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Change to the script's directory
cd "$(dirname "$0")"

# Pull latest code from git
echo "Pulling latest code from git..."
git pull

# Build Docker image
echo "Building Docker image..."
sudo docker build --no-cache -t roechling-office-fastapi-app:latest .

# Build completed
echo "Deployment complete."
