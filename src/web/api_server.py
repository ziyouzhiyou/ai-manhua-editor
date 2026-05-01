"""
FastAPI-based Web API Server
Provides REST endpoints for workflow management
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.core.workflow_engine import WorkflowEngine, WorkflowTemplates
from src.core.config_manager import ConfigManager
from src.core.event_bus import EventBus
from src.storage.project_store import ProjectStore

logger = logging.getLogger(__name__)


# Pydantic models for API
class GenerateRequest(BaseModel):
    script: str = Field(..., description="Script text or file path")
    workflow: str = Field("standard", description="Workflow type: fast, standard, premium")
    style: str = Field("anime", description="Visual style")
    title: str = Field("", description="Project title")

class ProjectResponse(BaseModel):
    project_id: str
    status: str
    message: str

class StatusResponse(BaseModel):
    project_id: str
    status: str
    progress: float = 0.0
    result: Optional[Dict] = None


# Global state
workflow_engine: Optional[WorkflowEngine] = None
event_bus: Optional[EventBus] = None
project_store: Optional[ProjectStore] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global workflow_engine, event_bus, project_store

    # Startup
    config = ConfigManager().load_config()
    event_bus = EventBus()
    await event_bus.start()

    workflow_engine = WorkflowEngine()
    project_store = ProjectStore(config.output_dir)

    logger.info("API server started")
    yield

    # Shutdown
    await event_bus.stop()
    logger.info("API server stopped")


app = FastAPI(
    title="AI Manhua Editor API",
    description="AI-powered comic drama video generation system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API info"""
    return {
        "name": "AI Manhua Editor",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/generate",
            "/status/{project_id}",
            "/projects",
            "/ws"
        ]
    }


@app.post("/generate", response_model=ProjectResponse)
async def generate_video(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate AI Manhua video from script
    """
    try:
        # Create project
        project_id = project_store.create_project(
            title=request.title or "Untitled Project",
            description=f"Workflow: {request.workflow}, Style: {request.style}"
        )

        # Start workflow in background
        background_tasks.add_task(
            _run_workflow,
            project_id=project_id,
            script=request.script,
            workflow_type=request.workflow,
            style=request.style
        )

        return ProjectResponse(
            project_id=project_id,
            status="started",
            message=f"Workflow '{request.workflow}' started"
        )

    except Exception as e:
        logger.error(f"Generate failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_workflow(project_id: str, script: str, workflow_type: str, style: str):
    """Run workflow in background"""
    try:
        # Select workflow
        if workflow_type == "fast":
            workflow = WorkflowTemplates.fast_workflow()
        elif workflow_type == "premium":
            workflow = WorkflowTemplates.premium_workflow()
        else:
            workflow = WorkflowTemplates.standard_workflow()

        workflow.global_config["script_text"] = script
        workflow.global_config["style"] = style

        # Run
        result = await workflow_engine.run_workflow(
            workflow,
            initial_context={
                "script_text": script,
                "project_id": project_id
            }
        )

        # Save result
        project_store.update_project(project_id, {
            "status": "completed",
            "result": result
        })

    except Exception as e:
        logger.error(f"Workflow failed for {project_id}: {e}")
        project_store.update_project(project_id, {
            "status": "failed",
            "error": str(e)
        })


@app.get("/status/{project_id}", response_model=StatusResponse)
async def get_status(project_id: str):
    """Get project status"""
    project = project_store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    status = workflow_engine.get_workflow_status(project_id)
    result = workflow_engine.get_workflow_result(project_id)

    # Calculate progress
    progress = 0.0
    if result and "metadata" in result:
        # Simple progress estimation
        status_map = {
            "pending": 0.0,
            "running": 0.5,
            "completed": 1.0,
            "failed": 0.0
        }
        progress = status_map.get(status.value if status else "unknown", 0.0)

    return StatusResponse(
        project_id=project_id,
        status=project.get("status", "unknown"),
        progress=progress,
        result=result
    )


@app.get("/projects")
async def list_projects(status: Optional[str] = None, limit: int = 50):
    """List all projects"""
    return {"projects": project_store.list_projects(status=status, limit=limit)}


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete project"""
    if project_store.delete_project(project_id):
        return {"message": "Project deleted"}
    raise HTTPException(status_code=404, detail="Project not found")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()

    async def send_event(event):
        await websocket.send_json(event)

    # Register event callback
    workflow_engine.register_event_callback(send_event)

    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "subscribe":
                project_id = message.get("project_id")
                await websocket.send_json({
                    "type": "subscribed",
                    "project_id": project_id
                })

    except Exception as e:
        logger.info(f"WebSocket disconnected: {e}")
    finally:
        # Unregister callback
        pass
