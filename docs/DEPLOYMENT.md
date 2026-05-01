# Deployment Guide

## OpenClaw Deployment

### Prerequisites

1. OpenClaw installed and running
2. Docker installed (for containerized deployment)
3. MiMo API key

### Step 1: Configure Environment

```bash
cp .env.example .env
# Edit .env and add your MIMO_API_KEY
```

### Step 2: Install Skill

```bash
# Method 1: Direct installation
openclaw skill install ./openclaw/skill_manifest.json

# Method 2: Using deploy script
./scripts/deploy.sh openclaw
```

### Step 3: Verify Installation

```bash
# Check skill status
openclaw skill list

# Test the skill
@ai-manhua-editor generate --script "test.txt" --workflow fast
```

### OpenClaw Configuration

The `openclaw/agent_config.yaml` file contains:
- Runtime configuration
- Resource limits
- Environment variables
- Security settings

### Cron Jobs

The `openclaw/cron_schedule.yaml` defines automated tasks:
- Daily cleanup at 2 AM
- Health checks every 5 minutes
- Metrics export hourly
- Weekly project archiving

## Docker Deployment

### Single Container

```bash
# Build image
docker build -f docker/Dockerfile -t ai-manhua-editor .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/.env:/app/.env \
  --name ai-manhua-editor \
  ai-manhua-editor:latest
```

### Docker Compose

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

## Local Deployment

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn src.web.api_server:app --reload

# Or use Make
make run
```

### Production

```bash
# Install production dependencies
pip install -e .

# Run with multiple workers
uvicorn src.web.api_server:app --host 0.0.0.0 --port 8000 --workers 4

# Or use Make
make run-prod
```

## Cloud Deployment

### AWS

```bash
# Using ECS
aws ecs create-service \
  --cluster ai-manhua-cluster \
  --service-name ai-manhua-editor \
  --task-definition ai-manhua-editor:1 \
  --desired-count 2
```

### Google Cloud

```bash
# Using Cloud Run
gcloud run deploy ai-manhua-editor \
  --source . \
  --region asia-east1 \
  --allow-unauthenticated
```

### Azure

```bash
# Using Container Instances
az container create \
  --resource-group myResourceGroup \
  --name ai-manhua-editor \
  --image ai-manhua-editor:latest \
  --ports 8000
```

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `MIMO_API_KEY` | MiMo API access key |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `MIMO_BASE_URL` | `https://api.mimo.ai/v1` | API base URL |
| `IMAGE_PROVIDER` | `mimo` | Image generation provider |
| `TTS_PROVIDER` | `mimo` | TTS provider |
| `LOG_LEVEL` | `INFO` | Logging level |
| `OUTPUT_DIR` | `./output` | Output directory |
| `TEMP_DIR` | `./temp` | Temporary files |
| `CACHE_DIR` | `./cache` | Cache directory |
| `MAX_CONCURRENT_TASKS` | `5` | Concurrency limit |
| `TASK_TIMEOUT` | `300` | Task timeout (seconds) |

## Health Checks

The API server exposes a health endpoint:

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "name": "AI Manhua Editor",
  "version": "1.0.0",
  "status": "running"
}
```

## Troubleshooting

### FFmpeg Not Found

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### API Key Issues

```bash
# Verify API key is set
echo $MIMO_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $MIMO_API_KEY" \
  https://api.mimo.ai/v1/models
```

### Memory Issues

```bash
# Increase Docker memory limit
docker run -m 16g ai-manhua-editor:latest

# Or adjust in docker-compose.yml
services:
  ai-manhua-editor:
    deploy:
      resources:
        limits:
          memory: 16G
```

## Performance Tuning

### Concurrency

Adjust `max_concurrent_tasks` based on your API rate limits:

```yaml
# config/default.yaml
max_concurrent_tasks: 3  # Conservative
max_concurrent_tasks: 10  # Aggressive
```

### Caching

Enable Redis for distributed caching:

```yaml
# docker/docker-compose.yml
redis:
  image: redis:7-alpine
  volumes:
    - redis-data:/data
```

### GPU Acceleration

For local image generation (future feature):

```yaml
# config/default.yaml
enable_gpu: true
gpu_device: "cuda:0"
```

## Backup and Recovery

### Project Backup

```bash
# Backup all projects
tar -czf projects-backup.tar.gz projects/

# Backup specific project
tar -czf project-backup.tar.gz projects/{project_id}/
```

### Restore

```bash
# Restore from backup
tar -xzf projects-backup.tar.gz
```
