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


# 🎬 AI Manhua Editor

> 输入一段故事文本，系统自动生成带画面、配音、字幕的完整漫剧视频。

---

## 一、项目核心亮点

### 1.1 全流程自动化

传统漫剧制作需要编剧、分镜师、画师、配音员、剪辑师等多个角色协作，周期长达数周。本系统将整个过程压缩为**一条命令**：输入文本 → 输出视频，无需人工干预中间环节。

### 1.2 自研DAG工作流引擎

系统底层采用**有向无环图（DAG）调度引擎**，核心能力包括：

- **任务级并行**：无依赖关系的任务同时执行。例如"生成画面"和"合成配音"可以并行，互不等待
- **智能重试**：任务失败时自动重试，采用指数退避策略（2秒、4秒、8秒…），最多重试5次
- **超时保护**：每个任务设置独立超时（默认300秒），防止卡死拖垮整个流程
- **事件驱动**：全程通过事件总线实时推送进度，前端可实时看到"正在解析剧本…""正在生成第3张图…"

### 1.3 多Provider架构

系统不绑定单一AI服务商，图像生成和语音合成均支持多Provider切换：

| 功能 | 支持Provider | 切换方式 |
|------|-------------|----------|
| 图像生成 | / Stability AI / Midjourney | `IMAGE_PROVIDER=` |
| 语音合成 |  / Azure / ElevenLabs | `TTS_PROVIDER=azure` |

Provider之间接口统一，更换只需改一行配置，无需改动业务代码。

### 1.4 情感感知系统

系统能识别文本中的情感，并贯穿到输出：

- **剧本解析**：自动标注每句对话的情感标签（开心/悲伤/愤怒/兴奋/害怕/浪漫）
- **画面生成**：情感影响画面色调提示词（悲伤→冷色调，开心→暖色调）
- **语音合成**：情感控制语调（愤怒→语速加快、音量提高）
- **字幕样式**：情感变色（开心→金色，悲伤→蓝色，愤怒→红色）

### 1.5 三种工作流适配不同需求

| 模式 | 画质 | 预计耗时 | 适用场景 |
|------|------|---------|----------|
| **Fast** | 720P | 3-5分钟 | 快速验证剧本、批量试产 |
| **Standard** | 1080P | 5-10分钟 | 日常内容生产 |
| **Premium** | 4K | 15-30分钟 | 精品内容、商业发布 |

三种模式不是简单调参，而是**独立的任务编排**：Fast模式跳过深度分析、减少画面数量、降低生成精度；Premium模式增加情感分析、角色画像、画质增强、自动修复等额外环节。

### 1.6 OpenClaw原生集成

项目完整封装为OpenClaw Skill，支持：

- 命令式调用：`@ai-manhua-editor generate --script story.txt`
- 定时任务：配置Cron自动清理旧项目、导出指标
- 资源隔离：CPU/内存/磁盘限制，多实例并发安全

---

## 二、核心逻辑流

### 2.1 整体流程

```
┌─────────────┐
│  输入文本    │  ← 用户提供一个故事文本文件
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────────────────────────────────────┐
│ 剧本解析代理  │────▶│ 输出：角色列表、场景列表、对话列表、情感标注       │
│ (Script      │     │ 技术：LLM理解文本结构，提取实体和关系            │
│  Parser)     │     └─────────────────────────────────────────────┘
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────────────────────────────────────┐
│ 分镜生成代理  │────▶│ 输出：每帧画面描述、AI绘图提示词、镜头角度、时长   │
│ (Storyboard  │     │ 技术：LLM根据场景描述设计视觉呈现                │
│   Agent)     │     └─────────────────────────────────────────────┘
└──────┬──────┘
       │
       ├──────────────────────────────┐
       │                              │
       ▼                              ▼
┌─────────────┐              ┌─────────────┐
│ 图像生成代理  │              │ 语音合成代理  │
│ (Image       │              │ (Voice       │
│  Generator)  │              │  Synthesizer)│
│             │              │             │
│ 输入：提示词  │              │ 输入：对话文本 │
│ 输出：PNG图片 │              │ 输出：MP3音频 │
│ 并行：3张同时 │              │ 并行：5段同时 │
└──────┬──────┘              └──────┬──────┘
       │                              │
       └──────────────┬───────────────┘
                      │
                      ▼
┌─────────────┐     ┌─────────────────────────────────────────────┐
│ 视频剪辑代理  │────▶│ 输入：图片序列 + 音频序列                     │
│ (Video       │     │ 输出：MP4视频（含转场、对齐、编码）             │
│  Editor)     │     │ 技术：FFmpeg concat + 音频混合 + 缩放编码      │
└──────┬──────┘     └─────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────────────────────────────────────┐
│ 字幕生成代理  │────▶│ 输入：对话文本 + 音频时长                     │
│ (Subtitle    │     │ 输出：ASS/SRT字幕文件（含样式、位置、颜色）      │
│  Generator)  │     │ 技术：时间轴计算 + 样式模板渲染                 │
└──────┬──────┘     └─────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────────────────────────────────────┐
│ 质量评估代理  │────▶│ 输入：最终视频 + 各环节中间结果                │
│ (Quality     │     │ 输出：质量评分 + 问题列表 + 修复建议            │
│  Assessor)   │     │ 维度：画面成功率、音频同步、视频完整性、字幕准确  │
└─────────────┘     └─────────────────────────────────────────────┘
```

### 2.2 DAG调度细节

系统不是线性执行，而是按依赖层级并行：

```
Level 1: [剧本解析]                                    ← 第1层，独立执行
            │
            ▼
Level 2: [分镜生成] ───┐                               ← 第2层，依赖Level 1
            │          │
            ▼          ▼
Level 3: [图像生成]  [语音合成]                          ← 第3层，两者并行！
            │          │
            └────┬─────┘
                 ▼
Level 4: [视频剪辑]                                    ← 第4层，依赖Level 3全部完成
                 │
                 ▼
Level 5: [字幕生成]                                    ← 第5层
                 │
                 ▼
Level 6: [质量评估] ──▶ [自动修复（Premium模式）]        ← 第6层
```

关键设计：图像生成和语音合成在**同一层级**，互不阻塞。如果某张图生成失败，不会影响配音进度；反之亦然。

### 2.3 数据流转

每个代理的输入输出通过**上下文对象**传递：

```python
context = {
    "workflow_id": "uuid",
    "global_config": {"output_dir": "./output", "style": "anime"},
    "results": {
        "parse_script": {"characters": [...], "scenes": [...]},
        "generate_storyboard": {"frames": [...]},
        "generate_images": {"images": [{"path": "..."}], "failed": []},
        "synthesize_voices": {"audio_segments": [...]},
        "compose_video": {"video_path": "..."},
        "generate_subtitles": {"ass_path": "..."},
        "quality_check": {"passed": True, "score": 0.92}
    }
}
```

代理通过`context["results"][上游任务ID]`读取上游输出，通过返回字典写入自己的结果。

---

## 三、使用方法

### 3.1 环境准备

**必需软件：**

```bash
# 1. Python 3.10+
python3 --version

# 2. FFmpeg（视频处理核心）
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows: https://ffmpeg.org/download.html
ffmpeg -version
```

**获取API密钥（至少选一个）：**

| 服务 | 用途 | 获取地址 |
|------|------|---------|
| AI | 图像+语音+文本 | https://ai |
| Stability AI | 图像生成 | https://stability.ai |
| Azure Speech | 语音合成 | https://azure.microsoft.com |
| ElevenLabs | 语音合成 | https://elevenlabs.io |

### 3.2 安装项目

```bash
# 克隆仓库
git clone https://github.com/yourusername/ai-manhua-editor.git
cd ai-manhua-editor

# 安装依赖
pip install -r requirements.txt

# 创建配置文件
cp .env.example .env
# 用文本编辑器打开 .env，填入你的API密钥
```

`.env` 示例：

```env
API_KEY=sk-xxxxxxxxxxxxxxxx
BASE_URL=https://api.ai/v1
IMAGE_PROVIDER=
TTS_PROVIDER=
OUTPUT_DIR=./output
LOG_LEVEL=INFO
```

### 3.3 准备故事文本

创建任意文本文件（如 `story.txt`），支持自然语言：

```text
第一章：初遇

清晨，繁华的街道上，阳光透过树叶洒下来。

小明（男，20岁，阳光开朗的大学生）抱着书本匆匆走着，
不小心撞到了迎面而来的小红（女，19岁，内向害羞的画家）。

小明说："啊！对不起对不起，你没事吧？"
小红低着头说："没、没事……是我没看路。"
小明笑着说："不不，是我的错。我叫小明，你呢？"
小红小声说："我叫小红……"

小明伸出手："很高兴认识你，小红。"
小红犹豫了一下，轻轻握了握手。

背景：街道两旁的樱花树随风飘落，氛围温暖而浪漫。
```

系统会自动识别：
- **角色**：小明（男，20岁，阳光）、小红（女，19岁，内向）
- **场景**：清晨街道，樱花飘落
- **对话**：4句对话，带情感标注
- **动作**：撞到人、握手、犹豫

### 3.4 生成视频

**方式A：命令行（最简单）**

```bash
# 标准模式，动漫风格
python -m src.cli generate --script story.txt --workflow standard --style anime

# 快速模式，国漫风格
python -m src.cli generate --script story.txt --workflow fast --style manhua

# 高级模式，电影级画质
python -m src.cli generate --script story.txt --workflow premium --style cinematic_anime
```

**方式B：启动API服务**

```bash
# 启动服务
python -m src.cli server --host 0.0.0.0 --port 8000

# 另开终端，调用API生成
curl -X POST http://localhost:8000/generate   -H "Content-Type: application/json"   -d '{
    "script": "小明说：你好！小红说：你好呀！今天天气真好。",
    "workflow": "standard",
    "style": "anime",
    "title": "初次见面"
  }'

# 返回：{"project_id": "xxx", "status": "started"}

# 查询进度
curl http://localhost:8000/status/xxx

# 列出所有项目
curl http://localhost:8000/projects
```

**方式C：OpenClaw技能**

```bash
# 部署技能
openclaw skill install ./openclaw/skill_manifest.json

# 在OpenClaw中使用
@ai-manhua-editor generate --script story.txt --workflow standard --style anime

# 查看项目状态
@ai-manhua-editor status --project-id xxx

# 列出所有项目
@ai-manhua-editor list-projects
```

### 3.5 查看输出

生成完成后，文件结构如下：

```
output/
└── {project_id}/
    ├── final_video.mp4      ← 最终视频
    ├── images/
    │   ├── frame_0.png      ← 场景1画面
    │   ├── frame_1.png      ← 场景2画面
    │   └── ...
    ├── audio/
    │   ├── dlg_s_1234.mp3   ← 对话1配音
    │   ├── dlg_s_5678.mp3   ← 对话2配音
    │   └── ...
    ├── subtitles.ass        ← 动漫风格字幕
    ├── subtitles.srt        ← 标准字幕（备用）
    └── quality_report.json  ← 质量评估报告
```

### 3.6 Docker部署（生产环境）

```bash
# 一键启动所有服务
docker-compose -f docker/docker-compose.yml up -d

# 查看日志
docker-compose -f docker/docker-compose.yml logs -f

# 停止服务
docker-compose -f docker/docker-compose.yml down
```

### 3.7 实时进度监控

前端可通过WebSocket实时查看生成进度：

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    project_id: 'your-project-id'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'progress') {
    console.log(`${data.progress}% - ${data.message}`);
    // 例如："45% - Generating image 3 of 8"
  }
  if (data.type === 'task.completed') {
    console.log(`✅ ${data.data.task_name} 完成`);
  }
  if (data.type === 'workflow.completed') {
    console.log('🎉 视频生成完成！');
  }
};
```

---

## 四、适用场景

### 4.1 个人创作者

**小说可视化**
- 网文作者将章节转为漫剧视频，发布到抖音/B站引流
- 无需学习绘画、剪辑，专注写作即可

**自媒体内容**
- 情感故事、悬疑故事、搞笑段子的视频化
- 批量生产，日更多条

### 4.2 MCN机构

**批量内容生产**
- 同时跑多个项目，利用DAG并行能力最大化硬件利用率
- Fast模式3分钟一条，标准模式10分钟一条，日产百条

**多账号矩阵**
- 不同账号用不同画风（恋爱号用anime，古风号用manhua）
- 同一剧本快速切换风格，一鱼多吃

### 4.3 教育领域

**教材动画化**
- 将历史故事、文学片段转为可视化视频
- 情感标注帮助理解人物心理

**语言学习**
- 生成带字幕、配音的双语视频
- 不同角色区分声音，帮助辨识说话人

### 4.4 游戏/动漫行业

**原型验证**
- 编剧快速验证剧本节奏，看画面+配音效果
- 比传统分镜快100倍

**同人创作**
- 粉丝基于原作写剧本，自动生成同人漫剧
- 支持多种画风还原原作气质

### 4.5 企业应用

**内部培训**
- 将规章制度、案例故事转为视频
- 多角色配音模拟真实场景

**营销内容**
- 产品故事、品牌故事的视频化
- 快速迭代不同版本测试效果

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| Web框架 | FastAPI |
| 视频处理 | FFmpeg |
| 图像生成 |  Image / Stability AI / Midjourney |
| 语音合成 |  TTS / Azure Speech / ElevenLabs |
| 文本理解 |  LLM |
| 部署 | Docker / OpenClaw |
| 测试 | pytest |

---

## 许可证

MIT License

</p>
