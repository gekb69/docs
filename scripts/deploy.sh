#!/bin/bash
set -e

ENV=${1:-dev}
echo "🚀 Deploying Super Agent in $ENV mode..."

# Generate config if not exists
if [ ! -f "config/security-policy.json" ]; then
echo "⚠️ Security policy not found, generating..."
python scripts/generate_user_config.py --level paranoid
fi

# Create logs directory
mkdir -p logs

# Start Docker Compose
if [ "$ENV" == "prod" ]; then
echo "🏭 Production deployment..."
docker-compose -f docker/docker-compose.prod.yml up -d --build
else
echo "🔧 Development deployment..."
sudo docker compose -f docker/docker-compose.yml up -d --build
fi

echo "✅ Deployment completed!"
echo "📊 View logs: docker-compose logs -f"
