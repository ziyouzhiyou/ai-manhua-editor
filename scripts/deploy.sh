#!/bin/bash
# AI Manhua Editor - Deployment Script
# Supports Docker and local deployment

set -e

DEPLOYMENT_TYPE=${1:-"docker"}

echo "🚀 AI Manhua Editor - Deployment"
echo "================================="
echo "Deployment type: $DEPLOYMENT_TYPE"

if [ "$DEPLOYMENT_TYPE" == "docker" ]; then
    echo "🐳 Building Docker image..."
    docker build -f docker/Dockerfile -t ai-manhua-editor:latest .

    echo "🚀 Starting services..."
    docker-compose -f docker/docker-compose.yml up -d

    echo ""
    echo "✅ Docker deployment complete!"
    echo "API available at: http://localhost:8000"
    echo "View logs: docker-compose -f docker/docker-compose.yml logs -f"

elif [ "$DEPLOYMENT_TYPE" == "local" ]; then
    echo "💻 Local deployment..."

    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -r requirements.txt

    echo "🚀 Starting server..."
    uvicorn src.web.api_server:app --host 0.0.0.0 --port 8000 --workers 4

elif [ "$DEPLOYMENT_TYPE" == "openclaw" ]; then
    echo "🔧 OpenClaw deployment..."

    # Validate OpenClaw config
    if [ ! -f "openclaw/skill_manifest.json" ]; then
        echo "❌ OpenClaw skill manifest not found!"
        exit 1
    fi

    echo "✅ OpenClaw configuration validated"
    echo ""
    echo "To deploy to OpenClaw:"
    echo "1. Ensure OpenClaw is installed and running"
    echo "2. Run: openclaw skill install ./openclaw/skill_manifest.json"
    echo "3. The skill will be available as @ai-manhua-editor"

else
    echo "❌ Unknown deployment type: $DEPLOYMENT_TYPE"
    echo "Usage: ./scripts/deploy.sh [docker|local|openclaw]"
    exit 1
fi
