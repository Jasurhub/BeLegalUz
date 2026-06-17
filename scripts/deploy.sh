#!/bin/bash
# deploy.sh - Production deployment script for BeLagel

set -e

APP_NAME="belagel"
DOCKER_COMPOSE_FILE="docker/docker-compose.yml"

echo " Deploying $APP_NAME..."

# 1. Pull latest code
echo "📥 Pulling latest changes..."
git pull origin main

# 2. Build and restart containers
echo "🏗️ Building Docker images..."
docker-compose -f $DOCKER_COMPOSE_FILE build --no-cache

echo "🔄 Restarting services..."
docker-compose -f $DOCKER_COMPOSE_FILE up -d

# 3. Clean up old images
echo "🧹 Cleaning up old Docker images..."
docker image prune -f

echo "✅ Deployment completed successfully!"
echo "🌐 Application is running at http://localhost:8000"