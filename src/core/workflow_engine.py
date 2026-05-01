"""
AI Manhua (Comic Drama) Auto-Editing Workflow Engine
Core orchestration system for OpenClaw deployment
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import traceback

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    id: str
    name: str
    agent_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # seconds

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type,
            "config": self.config,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout": self.timeout
        }


@dataclass
class WorkflowDefinition:
    id: str
    name: str
    description: str
    tasks: List[TaskNode]
    global_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"

    def get_task(self, task_id: str) -> Optional[TaskNode]:
        return next((t for t in self.tasks if t.id == task_id), None)

    def get_execution_order(self) -> List[List[str]]:
        """Topological sort with parallel level grouping"""
        completed = set()
        levels = []
        remaining = {t.id for t in self.tasks}

        while remaining:
            level = []
            for task_id in remaining:
                task = self.get_task(task_id)
                if task and all(dep in completed for dep in task.dependencies):
                    level.append(task_id)

            if not level:
                raise ValueError("Circular dependency detected in workflow")

            levels.append(level)
            completed.update(level)
            remaining -= set(level)

        return levels


class WorkflowEngine:
    """
    DAG-based workflow engine optimized for AI Manhua video generation
    Supports parallel execution, retry logic, and real-time monitoring
    """

    def __init__(self, agent_registry: Dict[str, Callable] = None):
        self.agent_registry = agent_registry or {}
        self.active_workflows: Dict[str, WorkflowStatus] = {}
        self.workflow_results: Dict[str, Dict] = {}
        self.event_callbacks: List[Callable] = []
        self.semaphore = asyncio.Semaphore(5)  # Max concurrent tasks

    def register_agent(self, agent_type: str, handler: Callable):
        """Register an agent handler for a specific task type"""
        self.agent_registry[agent_type] = handler
        logger.info(f"Registered agent: {agent_type}")

    def register_event_callback(self, callback: Callable):
        """Register callback for workflow events"""
        self.event_callbacks.append(callback)

    async def _emit_event(self, event_type: str, data: Dict):
        """Emit event to all registered callbacks"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    async def execute_task(self, task: TaskNode, context: Dict[str, Any]) -> Any:
        """Execute a single task with retry logic"""
        agent_handler = self.agent_registry.get(task.agent_type)
        if not agent_handler:
            raise ValueError(f"No agent registered for type: {task.agent_type}")

        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()

        await self._emit_event("task.started", {
            "task_id": task.id,
            "task_name": task.name,
            "agent_type": task.agent_type
        })

        for attempt in range(task.max_retries + 1):
            try:
                async with self.semaphore:
                    # Merge global config with task config
                    merged_config = {**context.get("global_config", {}), **task.config}

                    # Execute agent
                    if asyncio.iscoroutinefunction(agent_handler):
                        result = await agent_handler(
                            config=merged_config,
                            context=context,
                            task_id=task.id
                        )
                    else:
                        result = agent_handler(
                            config=merged_config,
                            context=context,
                            task_id=task.id
                        )

                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.end_time = datetime.now()

                    await self._emit_event("task.completed", {
                        "task_id": task.id,
                        "task_name": task.name,
                        "duration": (task.end_time - task.start_time).total_seconds()
                    })

                    return result

            except asyncio.TimeoutError:
                task.retry_count += 1
                logger.warning(f"Task {task.id} timeout (attempt {attempt + 1})")
                if attempt < task.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

            except Exception as e:
                task.retry_count += 1
                task.error = str(e)
                logger.error(f"Task {task.id} failed (attempt {attempt + 1}): {e}")
                logger.debug(traceback.format_exc())

                if attempt < task.max_retries:
                    await asyncio.sleep(2 ** attempt)
                else:
                    task.status = TaskStatus.FAILED
                    task.end_time = datetime.now()

                    await self._emit_event("task.failed", {
                        "task_id": task.id,
                        "task_name": task.name,
                        "error": str(e),
                        "attempts": task.retry_count
                    })

                    raise

        return None

    async def run_workflow(self, workflow: WorkflowDefinition, 
                          initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute complete workflow with parallel task optimization"""
        workflow_id = str(uuid.uuid4())
        self.active_workflows[workflow_id] = WorkflowStatus.RUNNING

        context = {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "global_config": workflow.global_config,
            "results": {},
            "metadata": {
                "started_at": datetime.now().isoformat(),
                "version": workflow.version
            }
        }
        if initial_context:
            context.update(initial_context)

        await self._emit_event("workflow.started", {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "task_count": len(workflow.tasks)
        })

        try:
            execution_levels = workflow.get_execution_order()

            for level_idx, level_tasks in enumerate(execution_levels):
                logger.info(f"Executing level {level_idx + 1}: {level_tasks}")

                # Prepare tasks for this level
                level_task_objects = [workflow.get_task(tid) for tid in level_tasks]
                level_task_objects = [t for t in level_task_objects if t is not None]

                # Execute all tasks in this level concurrently
                async def run_level_task(task):
                    try:
                        result = await self.execute_task(task, context)
                        context["results"][task.id] = result
                        return task.id, result, None
                    except Exception as e:
                        context["results"][task.id] = None
                        return task.id, None, str(e)

                results = await asyncio.gather(
                    *[run_level_task(t) for t in level_task_objects],
                    return_exceptions=True
                )

                # Check for failures
                failures = [r for r in results if isinstance(r, tuple) and r[2] is not None]
                if failures:
                    failed_tasks = [f[0] for f in failures]
                    raise RuntimeError(f"Tasks failed: {failed_tasks}")

                await self._emit_event("workflow.level_completed", {
                    "workflow_id": workflow_id,
                    "level": level_idx + 1,
                    "tasks_completed": len(level_tasks)
                })

            self.active_workflows[workflow_id] = WorkflowStatus.COMPLETED
            context["metadata"]["completed_at"] = datetime.now().isoformat()
            context["metadata"]["status"] = "completed"

            await self._emit_event("workflow.completed", {
                "workflow_id": workflow_id,
                "workflow_name": workflow.name,
                "duration": self._calculate_duration(context["metadata"])
            })

            self.workflow_results[workflow_id] = context
            return context

        except Exception as e:
            self.active_workflows[workflow_id] = WorkflowStatus.FAILED
            context["metadata"]["failed_at"] = datetime.now().isoformat()
            context["metadata"]["status"] = "failed"
            context["metadata"]["error"] = str(e)

            await self._emit_event("workflow.failed", {
                "workflow_id": workflow_id,
                "workflow_name": workflow.name,
                "error": str(e)
            })

            self.workflow_results[workflow_id] = context
            raise

    def _calculate_duration(self, metadata: Dict) -> float:
        """Calculate workflow duration in seconds"""
        try:
            start = datetime.fromisoformat(metadata["started_at"])
            end = datetime.fromisoformat(metadata.get("completed_at", metadata.get("failed_at", datetime.now().isoformat())))
            return (end - start).total_seconds()
        except:
            return 0.0

    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowStatus]:
        return self.active_workflows.get(workflow_id)

    def get_workflow_result(self, workflow_id: str) -> Optional[Dict]:
        return self.workflow_results.get(workflow_id)


# Pre-built workflow templates for AI Manhua generation
class WorkflowTemplates:
    """Factory for standard AI Manhua video generation workflows"""

    @staticmethod
    def standard_workflow() -> WorkflowDefinition:
        """Standard quality workflow - balanced speed and quality"""
        tasks = [
            TaskNode(
                id="parse_script",
                name="Parse Script",
                agent_type="script_parser",
                config={"mode": "standard"},
                max_retries=2
            ),
            TaskNode(
                id="generate_storyboard",
                name="Generate Storyboard",
                agent_type="storyboard_agent",
                config={"style": "anime", "quality": "high"},
                dependencies=["parse_script"],
                max_retries=2
            ),
            TaskNode(
                id="generate_images",
                name="Generate Images",
                agent_type="image_generator",
                config={"batch_size": 4, "quality": "high"},
                dependencies=["generate_storyboard"],
                timeout=600,
                max_retries=3
            ),
            TaskNode(
                id="synthesize_voices",
                name="Synthesize Voices",
                agent_type="voice_synthesizer",
                config={"voice_style": "dramatic", "language": "zh"},
                dependencies=["parse_script"],
                timeout=300,
                max_retries=2
            ),
            TaskNode(
                id="compose_video",
                name="Compose Video",
                agent_type="video_editor",
                config={"resolution": "1080p", "fps": 24, "transition": "fade"},
                dependencies=["generate_images", "synthesize_voices"],
                timeout=600,
                max_retries=1
            ),
            TaskNode(
                id="generate_subtitles",
                name="Generate Subtitles",
                agent_type="subtitle_generator",
                config={"style": "anime", "position": "bottom"},
                dependencies=["compose_video"],
                max_retries=2
            ),
            TaskNode(
                id="quality_check",
                name="Quality Assessment",
                agent_type="quality_assessor",
                config={"threshold": 0.8},
                dependencies=["generate_subtitles"],
                max_retries=1
            )
        ]

        return WorkflowDefinition(
            id="standard-ai-manhua",
            name="Standard AI Manhua Workflow",
            description="Balanced quality and speed for standard comic drama production",
            tasks=tasks,
            global_config={
                "output_format": "mp4",
                "max_duration": 300,
                "target_resolution": "1920x1080"
            }
        )

    @staticmethod
    def fast_workflow() -> WorkflowDefinition:
        """Fast workflow - optimized for speed with acceptable quality"""
        tasks = [
            TaskNode(
                id="parse_script",
                name="Parse Script",
                agent_type="script_parser",
                config={"mode": "fast"}
            ),
            TaskNode(
                id="generate_storyboard",
                name="Generate Storyboard",
                agent_type="storyboard_agent",
                config={"style": "anime", "quality": "medium"},
                dependencies=["parse_script"]
            ),
            TaskNode(
                id="generate_images",
                name="Generate Images",
                agent_type="image_generator",
                config={"batch_size": 8, "quality": "medium", "fast_mode": True},
                dependencies=["generate_storyboard"],
                timeout=300
            ),
            TaskNode(
                id="synthesize_voices",
                name="Synthesize Voices",
                agent_type="voice_synthesizer",
                config={"voice_style": "natural", "language": "zh", "fast_mode": True},
                dependencies=["parse_script"],
                timeout=180
            ),
            TaskNode(
                id="compose_video",
                name="Compose Video",
                agent_type="video_editor",
                config={"resolution": "720p", "fps": 24, "simple_transitions": True},
                dependencies=["generate_images", "synthesize_voices"],
                timeout=300
            ),
            TaskNode(
                id="generate_subtitles",
                name="Generate Subtitles",
                agent_type="subtitle_generator",
                config={"style": "simple"},
                dependencies=["compose_video"]
            )
        ]

        return WorkflowDefinition(
            id="fast-ai-manhua",
            name="Fast AI Manhua Workflow",
            description="Optimized for rapid production with medium quality",
            tasks=tasks,
            global_config={
                "output_format": "mp4",
                "max_duration": 180,
                "target_resolution": "1280x720"
            }
        )

    @staticmethod
    def premium_workflow() -> WorkflowDefinition:
        """Premium workflow - maximum quality with advanced features"""
        tasks = [
            TaskNode(
                id="parse_script",
                name="Deep Script Analysis",
                agent_type="script_parser",
                config={"mode": "deep", "emotion_analysis": True, "character_profiles": True},
                max_retries=3
            ),
            TaskNode(
                id="generate_storyboard",
                name="Cinematic Storyboard",
                agent_type="storyboard_agent",
                config={"style": "cinematic_anime", "quality": "ultra", "camera_moves": True},
                dependencies=["parse_script"],
                max_retries=3
            ),
            TaskNode(
                id="generate_images",
                name="Ultra HD Image Generation",
                agent_type="image_generator",
                config={"batch_size": 2, "quality": "ultra", "upscale": True, "detail_enhancement": True},
                dependencies=["generate_storyboard"],
                timeout=1200,
                max_retries=5
            ),
            TaskNode(
                id="synthesize_voices",
                name="Premium Voice Acting",
                agent_type="voice_synthesizer",
                config={"voice_style": "emotional", "language": "zh", "multi_speaker": True, "prosody": True},
                dependencies=["parse_script"],
                timeout=600,
                max_retries=3
            ),
            TaskNode(
                id="compose_video",
                name="Cinematic Video Composition",
                agent_type="video_editor",
                config={"resolution": "4k", "fps": 60, "advanced_transitions": True, "color_grading": True, "sound_effects": True},
                dependencies=["generate_images", "synthesize_voices"],
                timeout=1200,
                max_retries=2
            ),
            TaskNode(
                id="generate_subtitles",
                name="Stylized Subtitles",
                agent_type="subtitle_generator",
                config={"style": "cinematic", "animations": True, "effects": True},
                dependencies=["compose_video"],
                max_retries=3
            ),
            TaskNode(
                id="quality_check",
                name="Rigorous Quality Assessment",
                agent_type="quality_assessor",
                config={"threshold": 0.95, "detailed_report": True},
                dependencies=["generate_subtitles"],
                max_retries=2
            ),
            TaskNode(
                id="auto_fix",
                name="Auto Fix Issues",
                agent_type="video_editor",
                config={"mode": "fix", "quality_threshold": 0.95},
                dependencies=["quality_check"],
                max_retries=2
            )
        ]

        return WorkflowDefinition(
            id="premium-ai-manhua",
            name="Premium AI Manhua Workflow",
            description="Maximum quality with cinematic production values",
            tasks=tasks,
            global_config={
                "output_format": "mp4",
                "max_duration": 600,
                "target_resolution": "3840x2160"
            }
        )
