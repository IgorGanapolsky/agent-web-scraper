#!/bin/bash
set -e

echo "🚀 Deploying SaaS Intelligence to production..."

# Load environment variables
source .env.production

# Build and push Docker image
docker build -t saas-intelligence:latest .
docker tag saas-intelligence:latest your-registry/saas-intelligence:latest
docker push your-registry/saas-intelligence:latest

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose exec app python -m alembic upgrade head

# Health check
sleep 30
curl -f http://localhost:8000/health || exit 1

echo "✅ Deployment completed successfully!"
