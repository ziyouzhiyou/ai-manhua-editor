# Architecture Documentation

## System Overview

The AI Manhua Editor is a distributed workflow system designed for automated comic drama video generation. It follows a modular agent-based architecture with clear separation of concerns.

## Core Components

### 1. Workflow Engine (`src/core/workflow_engine.py`)

The heart of the system, responsible for:
- **DAG Execution**: Topological sorting with parallel level execution
- **Task Management**: Retry logic, timeout handling, semaphore-based concurrency
- **Event System**: Real-time progress reporting via callbacks
- **State Management**: Workflow status tracking and result persistence

Key features:
- Parallel task execution within the same dependency level
- Exponential backoff retry strategy
- Configurable concurrency limits
- Event-driven architecture for monitoring

### 2. Agents (`src/agents/`)

Specialized AI agents for each stage of production:

#### Script Parser Agent
- **Input**: Raw text/script
- **Output**: Structured scenes, characters, dialogues
- **Modes**: Fast (regex-based), Standard (LLM), Deep (emotion analysis)
- **API**: MiMo V2.5 Reasoning model for deep parsing

#### Storyboard Agent
- **Input**: Parsed scenes
- **Output**: Frame-by-frame storyboard with image prompts
- **Features**: Camera angles, movements, transitions
- **Optimization**: Prompt enhancement for better image generation

#### Image Generator Agent
- **Input**: Storyboard frames
- **Output**: Generated images
- **Providers**: MiMo, Stability AI, Midjourney
- **Batch Processing**: Concurrent generation with rate limiting

#### Voice Synthesizer Agent
- **Input**: Dialogues from parsed script
- **Output**: Audio segments
- **Features**: Multi-speaker, emotion control, speed adjustment
- **Providers**: MiMo TTS, Azure Speech, ElevenLabs

#### Video Editor Agent
- **Input**: Images, audio, subtitles
- **Output**: Final composed video
- **Tool**: FFmpeg with advanced filtering
- **Features**: Transitions, color grading, subtitle burning

#### Subtitle Generator Agent
- **Input**: Dialogues and timing data
- **Output**: ASS/SRT subtitle files
- **Styles**: Anime, cinematic, comic, simple
- **Features**: Emotion-based color coding

#### Quality Assessor Agent
- **Input**: Final video and intermediate results
- **Output**: Quality report with scores
- **Metrics**: Image quality, audio sync, video smoothness
- **Actions**: Auto-fix recommendations

### 3. Skills Layer (`src/skills/`)

API wrappers and integrations:

#### MiMo API (`mimo_api.py`)
- OpenAI-compatible API client
- Supports chat completion, image generation, TTS
- Streaming response handling
- Automatic retry with backoff

#### Image Generation API (`image_gen_api.py`)
- Unified interface for multiple providers
- Provider selection based on configuration
- Result normalization (URL, bytes, base64)

#### TTS API (`tts_api.py`)
- Multi-provider voice synthesis
- SSML support for Azure
- Voice settings optimization

#### Video Composition (`video_compose.py`)
- FFmpeg command builder
- Transition effects
- Audio track mixing
- Subtitle burning

### 4. Storage Layer (`src/storage/`)

#### Project Store
- JSON-based project metadata
- Versioned storage
- Index for fast lookups
- Result archiving

#### Asset Manager
- Content-addressable caching
- Deduplication via SHA256
- Project asset organization
- Cleanup utilities

### 5. Web Layer (`src/web/`)

#### API Server (`api_server.py`)
- FastAPI-based REST API
- Async endpoint handlers
- Background task execution
- CORS support

#### WebSocket Handler (`websocket_handler.py`)
- Real-time progress updates
- Project-specific subscriptions
- Connection management
- Broadcast capabilities

## Data Flow

```
1. User Input (Script)
   │
   ▼
2. Script Parser (MiMo LLM)
   │
   ├── Characters
   ├── Scenes
   └── Dialogues
   │
   ▼
3. Parallel Execution:
   │
   ├── Storyboard Agent ──▶ Image Generator ──┐
   │                                           │
   └── Voice Synthesizer ──────────────────────┤
                                               │
                                               ▼
4. Video Editor (FFmpeg)
   │
   ├── Image sequence
   ├── Audio track
   └── Subtitles
   │
   ▼
5. Quality Assessment
   │
   ▼
6. Output (MP4 Video)
```

## Concurrency Model

The system uses asyncio for concurrent operations:

- **Workflow Level**: Parallel execution of independent tasks
- **Agent Level**: Semaphore-controlled concurrent API calls
- **API Level**: Connection pooling and rate limiting

Default limits:
- Max concurrent workflows: 3
- Max concurrent image generations: 3
- Max concurrent TTS: 5
- Max concurrent tasks: 5

## Error Handling

### Retry Strategy
- Exponential backoff: 2^attempt seconds
- Max retries: Configurable per task (default 3)
- Timeout: Configurable per task (default 300s)

### Fallback Mechanisms
- LLM parsing fails → Regex-based fast parsing
- Image generation fails → Retry with adjusted prompt
- TTS fails → Skip segment or use default voice
- Video composition fails → Report error with partial results

## Scalability Considerations

### Horizontal Scaling
- Stateless API server design
- External storage for projects
- Redis for distributed caching (optional)

### Vertical Scaling
- Configurable concurrency limits
- GPU acceleration support (future)
- Memory limits enforcement

## Security

- API keys stored in environment variables
- No sensitive data in logs
- File path validation
- Request size limits
- CORS configuration

## Monitoring

### Metrics
- Workflow completion rate
- Task success/failure rates
- API response times
- Resource utilization

### Logging
- Structured JSON logging
- Correlation IDs for tracing
- Error context preservation
