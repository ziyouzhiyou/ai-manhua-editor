"""
OpenClaw Skill Integration
Exposes AI Manhua Editor as an OpenClaw skill
"""
import json
import logging
from typing import Dict, Any

from src.core.workflow_engine import WorkflowEngine, WorkflowTemplates
from src.core.config_manager import ConfigManager
from src.core.event_bus import EventBus
from src.agents.script_parser import ScriptParserAgent
from src.agents.storyboard_agent import StoryboardAgent
from src.agents.image_generator import ImageGeneratorAgent
from src.agents.voice_synthesizer import VoiceSynthesizerAgent
from src.agents.video_editor import VideoEditorAgent
from src.agents.subtitle_generator import SubtitleGeneratorAgent
from src.agents.quality_assessor import QualityAssessorAgent

logger = logging.getLogger(__name__)


class AIManhuaSkill:
    """
    OpenClaw Skill for AI Manhua Video Generation

    Usage in OpenClaw:
    @ai-manhua generate --script "path/to/script.txt" --workflow standard
    @ai-manhua status --project-id <id>
    @ai-manhua list-projects
    """

    def __init__(self):
        self.config_manager = ConfigManager()
        self.event_bus = EventBus()
        self.engine = WorkflowEngine()
        self._setup_agents()

    def _setup_agents(self):
        """Register all agents with the workflow engine"""
        self.engine.register_agent("script_parser", ScriptParserAgent().parse)
        self.engine.register_agent("storyboard_agent", StoryboardAgent().generate)
        self.engine.register_agent("image_generator", ImageGeneratorAgent().generate)
        self.engine.register_agent("voice_synthesizer", VoiceSynthesizerAgent().synthesize)
        self.engine.register_agent("video_editor", VideoEditorAgent().compose)
        self.engine.register_agent("subtitle_generator", SubtitleGeneratorAgent().generate)
        self.engine.register_agent("quality_assessor", QualityAssessorAgent().assess)

    async def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI Manhua video

        Args:
            params:
                - script: Script text or file path
                - workflow: "standard", "fast", or "premium"
                - output_dir: Output directory
                - style: Visual style
        """
        script = params.get("script", "")
        workflow_type = params.get("workflow", "standard")

        # Load script from file if path provided
        if script.endswith(".txt") or script.endswith(".md"):
            with open(script, "r", encoding="utf-8") as f:
                script = f.read()

        # Select workflow
        if workflow_type == "fast":
            workflow = WorkflowTemplates.fast_workflow()
        elif workflow_type == "premium":
            workflow = WorkflowTemplates.premium_workflow()
        else:
            workflow = WorkflowTemplates.standard_workflow()

        # Set script in workflow config
        workflow.global_config["script_text"] = script

        # Run workflow
        result = await self.engine.run_workflow(
            workflow,
            initial_context={"script_text": script}
        )

        return {
            "success": True,
            "project_id": result.get("workflow_id"),
            "status": "completed",
            "output": result
        }

    async def get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get project status"""
        project_id = params.get("project_id", "")
        status = self.engine.get_workflow_status(project_id)
        result = self.engine.get_workflow_result(project_id)

        return {
            "project_id": project_id,
            "status": status.value if status else "unknown",
            "result": result
        }

    async def list_projects(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """List all projects"""
        projects = []
        for workflow_id, status in self.engine.active_workflows.items():
            result = self.engine.get_workflow_result(workflow_id)
            projects.append({
                "id": workflow_id,
                "status": status.value,
                "name": result.get("workflow_name", "Unknown") if result else "Unknown"
            })

        return {"projects": projects, "count": len(projects)}


# OpenClaw skill manifest
SKILL_MANIFEST = {
    "name": "ai-manhua-editor",
    "version": "1.0.0",
    "description": "AI-powered comic drama (manhua) video generation system",
    "author": "AI Creator",
    "entry_point": "openclaw_skill:AIManhuaSkill",
    "commands": [
        {
            "name": "generate",
            "description": "Generate AI manhua video from script",
            "parameters": {
                "script": {"type": "string", "required": True, "description": "Script text or file path"},
                "workflow": {"type": "string", "required": False, "default": "standard", "enum": ["fast", "standard", "premium"]},
                "style": {"type": "string", "required": False, "default": "anime"},
                "output_dir": {"type": "string", "required": False}
            }
        },
        {
            "name": "status",
            "description": "Check project status",
            "parameters": {
                "project_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "list-projects",
            "description": "List all projects",
            "parameters": {}
        }
    ],
    "permissions": ["file_read", "file_write", "network"],
    "dependencies": ["ffmpeg", "python3"]
}
