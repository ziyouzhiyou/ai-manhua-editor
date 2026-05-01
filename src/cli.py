"""
AI Manhua Editor - Main Entry Point
"""
import asyncio
import argparse
import logging
import sys
from pathlib import Path

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_engine() -> WorkflowEngine:
    """Initialize and configure workflow engine"""
    engine = WorkflowEngine()

    # Register all agents
    engine.register_agent("script_parser", ScriptParserAgent().parse)
    engine.register_agent("storyboard_agent", StoryboardAgent().generate)
    engine.register_agent("image_generator", ImageGeneratorAgent().generate)
    engine.register_agent("voice_synthesizer", VoiceSynthesizerAgent().synthesize)
    engine.register_agent("video_editor", VideoEditorAgent().compose)
    engine.register_agent("subtitle_generator", SubtitleGeneratorAgent().generate)
    engine.register_agent("quality_assessor", QualityAssessorAgent().assess)

    return engine


async def generate_video(script_path: str, workflow_type: str = "standard", style: str = "anime"):
    """Generate video from script file"""
    # Read script
    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()

    # Setup engine
    engine = setup_engine()

    # Select workflow
    if workflow_type == "fast":
        workflow = WorkflowTemplates.fast_workflow()
    elif workflow_type == "premium":
        workflow = WorkflowTemplates.premium_workflow()
    else:
        workflow = WorkflowTemplates.standard_workflow()

    # Run workflow
    logger.info(f"Starting {workflow_type} workflow...")
    result = await engine.run_workflow(
        workflow,
        initial_context={"script_text": script_text}
    )

    # Output results
    print("\n" + "="*50)
    print("✅ Workflow completed!")
    print("="*50)
    print(f"Project ID: {result['workflow_id']}")
    print(f"Duration: {result['metadata'].get('completed_at', 'N/A')}")

    if "results" in result:
        video_result = result["results"].get("compose_video", {})
        if video_result.get("success"):
            print(f"\n🎬 Video saved to: {video_result.get('video_path')}")

        quality_result = result["results"].get("quality_check", {})
        if quality_result:
            print(f"\n📊 Quality Score: {quality_result.get('overall_score', 0):.2f}")
            print(f"✅ Passed: {quality_result.get('passed', False)}")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI Manhua Editor - Comic Drama Video Generator"
    )
    parser.add_argument(
        "command",
        choices=["generate", "server"],
        help="Command to execute"
    )
    parser.add_argument(
        "--script", "-s",
        help="Path to script file"
    )
    parser.add_argument(
        "--workflow", "-w",
        choices=["fast", "standard", "premium"],
        default="standard",
        help="Workflow type"
    )
    parser.add_argument(
        "--style",
        default="anime",
        choices=["anime", "cinematic_anime", "manhua", "chibi", "realistic", "watercolor"],
        help="Visual style"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Server port"
    )

    args = parser.parse_args()

    if args.command == "generate":
        if not args.script:
            print("❌ Error: --script is required for generate command")
            sys.exit(1)

        if not Path(args.script).exists():
            print(f"❌ Error: Script file not found: {args.script}")
            sys.exit(1)

        asyncio.run(generate_video(args.script, args.workflow, args.style))

    elif args.command == "server":
        import uvicorn
        from src.web.api_server import app

        print(f"🚀 Starting server on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
