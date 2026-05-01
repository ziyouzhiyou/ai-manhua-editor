#!/bin/bash
# AI Manhua Editor - Start Script
# Quick start for development and production

set -e

MODE=${1:-"dev"}

echo "🎬 AI Manhua Editor - Starting ($MODE mode)"
echo "============================================"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp .env.example .env
    echo "❌ Please edit .env and add your API keys before starting!"
    exit 1
fi

# Create directories
mkdir -p output temp cache projects

if [ "$MODE" == "dev" ]; then
    echo "🔄 Starting development server..."
    uvicorn src.web.api_server:app --host 0.0.0.0 --port 8000 --reload

elif [ "$MODE" == "prod" ]; then
    echo "🚀 Starting production server..."
    uvicorn src.web.api_server:app --host 0.0.0.0 --port 8000 --workers 4

elif [ "$MODE" == "openclaw" ]; then
    echo "🔧 Starting in OpenClaw mode..."
    python -m src.skills.openclaw_skill

else
    echo "❌ Unknown mode: $MODE"
    echo "Usage: ./scripts/start.sh [dev|prod|openclaw]"
    exit 1
fi
