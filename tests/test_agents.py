"""
Agent Tests
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.agents.script_parser import ScriptParserAgent
from src.agents.storyboard_agent import StoryboardAgent
from src.agents.quality_assessor import QualityAssessorAgent


class TestScriptParserAgent:

    @pytest.fixture
    def agent(self):
        mock_api = Mock()
        mock_api.chat_completion = AsyncMock(return_value="""
        {
            "characters": [
                {"id": "char_0", "name": "小明", "gender": "male", "description": "男主角"}
            ],
            "scenes": [
                {
                    "id": "scene_1",
                    "scene_number": 1,
                    "scene_type": "dialogue",
                    "dialogues": [
                        {"character_id": "char_0", "text": "你好！", "emotion": "happy"}
                    ]
                }
            ]
        }
        """)
        return ScriptParserAgent(mimo_api=mock_api)

    @pytest.mark.asyncio
    async def test_parse(self, agent):
        config = {
            "script_text": "小明说：你好！",
            "mode": "standard",
            "language": "zh"
        }
        context = {}

        result = await agent.parse(config, context, "task_1")

        assert "characters" in result
        assert "scenes" in result
        assert len(result["characters"]) > 0

    @pytest.mark.asyncio
    async def test_fast_parse(self, agent):
        config = {
            "script_text": "小明说：你好！小红说：你好呀！",
            "mode": "fast",
            "language": "zh"
        }
        context = {}

        result = await agent.parse(config, context, "task_1")

        assert "characters" in result
        assert "scenes" in result


class TestStoryboardAgent:

    @pytest.fixture
    def agent(self):
        mock_api = Mock()
        mock_api.chat_completion = AsyncMock(return_value="""
        [
            {
                "description": "Scene opening",
                "image_prompt": "Wide shot of city",
                "camera_angle": "long_shot",
                "duration": 3.0,
                "transition_type": "fade"
            }
        ]
        """)
        return StoryboardAgent(mimo_api=mock_api)

    @pytest.mark.asyncio
    async def test_generate(self, agent):
        config = {
            "scenes": [
                {
                    "id": "scene_1",
                    "description": "City scene",
                    "dialogues": []
                }
            ],
            "style": "anime",
            "quality": "high"
        }
        context = {"workflow_id": "test_123"}

        result = await agent.generate(config, context, "task_1")

        assert "storyboard" in result
        assert "frame_count" in result


class TestQualityAssessorAgent:

    @pytest.fixture
    def agent(self):
        return QualityAssessorAgent()

    @pytest.mark.asyncio
    async def test_assess(self, agent):
        config = {
            "video_path": "/tmp/test.mp4",
            "threshold": 0.8
        }
        context = {
            "results": {
                "generate_images": {
                    "images": [{"success": True}],
                    "failed": []
                },
                "synthesize_voices": {
                    "audio_segments": [{"success": True}],
                    "failed": []
                },
                "generate_subtitles": {
                    "subtitle_entries": [{"text": "Hello"}]
                }
            }
        }

        result = await agent.assess(config, context, "task_1")

        assert "report" in result
        assert "passed" in result
        assert "overall_score" in result
