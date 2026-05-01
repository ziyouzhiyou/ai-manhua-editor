# 🎬 系统概览
这是一个完整的AI漫剧（AI Comic Drama）自动剪辑工作流系统，包含以下核心功能：

## 核心工作流（DAG并行执行）

| 阶段      | 功能                   | 技术                        |
| ------- | -------------------- | ------------------------- |
| 1. 剧本解析 | 智能提取角色、场景、对话         |  Reasoning       |
| 2. 分镜生成 | 自动生成带镜头语言的Storyboard |  LLM                  |
| 3. 图像生成 | 批量生成动漫/国漫风格画面        |  Image/Stability AI   |
| 4. 语音合成 | 多角色情感语音，支持中文         |  TTS/Azure/ElevenLabs |
| 5. 视频剪辑 | 自动合成、转场、调色           | FFmpeg                    |
| 6. 字幕生成 | ASS/SRT动漫风格字幕        | 情感色彩编码                    |
| 7. 质量评估 | 自动质检与修复建议            | 多维度评分                     |


## 三种工作流模式
Fast - 快速模式（3-5分钟，720p）
Standard - 标准模式（5-10分钟，1080p）
Premium - 高级模式（15-30分钟，4K cinematic）


## 🚀 快速部署到 OpenClaw

### OpenClaw 部署
bash
复制
# 安装技能
openclaw skill install ./openclaw/skill_manifest.json

# 使用技能生成视频
@ai-manhua-editor generate --script "你的剧本.txt" --workflow standard --style anime

###Docker 部署
bash
复制
./scripts/setup.sh      # 初始化环境
./scripts/deploy.sh docker   # Docker部署
./scripts/start.sh dev       # 启动开发服务器


# 📁 项目结构亮点
plain
复制
ai-manhua-editor/
├── src/
│   ├── core/          # DAG工作流引擎（支持并行执行、重试、事件驱动）
│   ├── agents/        # 7个专业AI代理
│   ├── skills/        # /Stability/Azure API封装
│   ├── web/           # FastAPI + WebSocket实时进度
│   └── storage/       # 项目持久化与资产缓存
├── openclaw/          # OpenClaw技能配置清单
├── workflows/         # 三种工作流JSON定义
├── docker/            # Docker Compose部署
└── docs/              # 完整架构文档与部署指南
系统已配置好 API 的 OpenAI-compatible 接口，申请通过Token后只需在 .env 中填入 API_KEY 即可运行。
  
</p>
