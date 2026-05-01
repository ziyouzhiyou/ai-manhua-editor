"""
Project Storage Manager
Handles persistence of video projects and metadata
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from src.models.schemas import VideoProject

logger = logging.getLogger(__name__)


class ProjectStore:
    """
    JSON-based project storage with versioning
    """

    def __init__(self, base_dir: str = "./projects"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.base_dir / "index.json"
        self._index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """Load project index"""
        if self._index_file.exists():
            with open(self._index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"projects": {}, "version": "1.0"}

    def _save_index(self):
        """Save project index"""
        with open(self._index_file, "w", encoding="utf-8") as f:
            json.dump(self._index, f, ensure_ascii=False, indent=2)

    def create_project(self, title: str = "", description: str = "") -> str:
        """Create new project and return ID"""
        import uuid
        project_id = str(uuid.uuid4())

        project = VideoProject(
            id=project_id,
            title=title,
            description=description,
            status="created"
        )

        # Save project
        project_dir = self.base_dir / project_id
        project_dir.mkdir(exist_ok=True)

        with open(project_dir / "project.json", "w", encoding="utf-8") as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)

        # Update index
        self._index["projects"][project_id] = {
            "title": title,
            "description": description,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self._save_index()

        logger.info(f"Created project: {project_id}")
        return project_id

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        project_file = self.base_dir / project_id / "project.json"
        if project_file.exists():
            with open(project_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project data"""
        project = self.get_project(project_id)
        if not project:
            return False

        project.update(updates)
        project["updated_at"] = datetime.now().isoformat()

        project_file = self.base_dir / project_id / "project.json"
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)

        # Update index
        if project_id in self._index["projects"]:
            self._index["projects"][project_id].update({
                "title": project.get("title", ""),
                "status": project.get("status", ""),
                "updated_at": project["updated_at"]
            })
            self._save_index()

        return True

    def list_projects(self, status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List projects with optional filtering"""
        projects = []
        for pid, meta in self._index["projects"].items():
            if status is None or meta.get("status") == status:
                projects.append({"id": pid, **meta})

        # Sort by updated_at descending
        projects.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return projects[:limit]

    def delete_project(self, project_id: str) -> bool:
        """Delete project and all assets"""
        import shutil
        project_dir = self.base_dir / project_id
        if project_dir.exists():
            shutil.rmtree(project_dir)

        if project_id in self._index["projects"]:
            del self._index["projects"][project_id]
            self._save_index()

        logger.info(f"Deleted project: {project_id}")
        return True

    def save_workflow_result(self, project_id: str, task_name: str, result: Dict[str, Any]):
        """Save workflow task result"""
        result_dir = self.base_dir / project_id / "results"
        result_dir.mkdir(exist_ok=True)

        with open(result_dir / f"{task_name}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
