# 🎬 AI Manhua Editor

> AI-powered comic drama (manhua) video generation system
> 
> 专为小米百万亿Token创造者激励计划设计的AI漫剧自动剪辑工作流系统

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🤖 **Intelligent Script Parsing** - Automatically extract characters, scenes, and dialogues from text using MiMo LLM
- 🎨 **AI Storyboard Generation** - Create cinematic storyboards with optimized image prompts
- 🖼️ **Batch Image Generation** - Generate anime/manhua style images with multiple provider support
- 🎙️ **Multi-speaker TTS** - Synthesize voices with emotion control and character differentiation
- 🎬 **Automated Video Composition** - Combine images, audio, and subtitles with FFmpeg
- 📝 **Stylized Subtitles** - Generate ASS/SRT subtitles with anime-style formatting
- 🔍 **Quality Assessment** - Automated quality checks with retry logic
- 🚀 **OpenClaw Ready** - Deploy seamlessly in OpenClaw environment

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Script Input  │────▶│  Script Parser  │────▶│  Storyboard     │
│   (.txt/.md)    │     │  (MiMo LLM)     │     │  Generation     │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                              ┌──────────────────────────┼──────────┐
                              │                          │          │
                              ▼                          ▼          ▼
                    ┌─────────────────┐        ┌─────────────────┐
                    │ Image Generator │        │ Voice Synthesizer│
                    │ (MiMo/Stability)│        │ (MiMo/Azure)     │
                    └────────┬────────┘        └────────┬────────┘
                             │                          │
                             └────────────┬─────────────┘
                                          ▼
                               ┌─────────────────┐
                               │  Video Editor   │
                               │    (FFmpeg)     │
                               └────────┬────────┘
                                        │
                               ┌────────▼────────┐
                               │ Subtitle Gen    │
                               │ Quality Check   │
                               └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- FFmpeg 4.4+
- MiMo API Key ([申请小米百万亿Token](https://100t.xiaomimimo.com/))

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/ai-manhua-editor.git
cd ai-manhua-editor

# Run setup script
./scripts/setup.sh

# Edit configuration
cp .env.example .env
# Add your MIMO_API_KEY to .env
```

### Usage

#### Local Development

```bash
# Start development server
make run

# Or use the start script
./scripts/start.sh dev
```

#### API Usage

```bash
# Generate video from script
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "script": "小明说：你好！小红说：你好呀！今天天气真好。",
    "workflow": "standard",
    "style": "anime",
    "title": "初次见面"
  }'

# Check status
curl http://localhost:8000/status/{project_id}

# List projects
curl http://localhost:8000/projects
```

#### OpenClaw Integration

```bash
# Deploy to OpenClaw
./scripts/deploy.sh openclaw

# Use in OpenClaw
@ai-manhua-editor generate --script "path/to/script.txt" --workflow standard
```

## 📁 Project Structure

```
ai-manhua-editor/
├── src/
│   ├── core/           # Workflow engine, config, event bus
│   ├── agents/         # AI agents (parser, generator, editor)
│   ├── models/         # Data schemas and enums
│   ├── skills/         # API wrappers (MiMo, TTS, Image)
│   ├── storage/        # Project persistence
│   └── web/            # FastAPI server and WebSocket
├── config/             # Configuration files
├── workflows/          # Workflow definitions (JSON)
├── templates/          # Prompt templates and styles
├── openclaw/           # OpenClaw skill configuration
├── docker/             # Docker deployment files
├── scripts/            # Setup and deployment scripts
├── tests/              # Test suite
└── docs/               # Documentation
```

## 🎨 Supported Styles

| Style | Description | Best For |
|-------|-------------|----------|
| `anime` | Classic Japanese anime | Romance, Comedy |
| `cinematic_anime` | Movie-quality anime | Action, Fantasy |
| `manhua` | Chinese comic style | Historical, Xianxia |
| `chibi` | Cute super-deformed | Comedy, Kids |
| `realistic` | Photorealistic 3D | Thriller, Mystery |
| `watercolor` | Artistic watercolor | Drama, Romance |

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MIMO_API_KEY` | ✅ | - | MiMo API access key |
| `MIMO_BASE_URL` | ❌ | `https://api.mimo.ai/v1` | API base URL |
| `IMAGE_PROVIDER` | ❌ | `mimo` | Image generation provider |
| `TTS_PROVIDER` | ❌ | `mimo` | Text-to-speech provider |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |
| `OUTPUT_DIR` | ❌ | `./output` | Output directory |

### Workflow Types

- **Fast** (`fast`) - Quick production, medium quality, ~3-5 min
- **Standard** (`standard`) - Balanced quality and speed, ~5-10 min
- **Premium** (`premium`) - Maximum quality, cinematic, ~15-30 min

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# Or use the deploy script
./scripts/deploy.sh docker
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Xiaomi MiMo](https://mimo.ai) - AI model provider
- [OpenClaw](https://openclaw.ai) - AI agent deployment platform
- [FFmpeg](https://ffmpeg.org) - Video processing toolkit

## 📞 Support

- Issues: [GitHub Issues](https://github.com/yourusername/ai-manhua-editor/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/ai-manhua-editor/discussions)

---

<p align="center">
  Made with ❤️ for the Xiaomi MiMo 100T Token Creator Incentive Program
</p>
