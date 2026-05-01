"""
WebSocket Handler for real-time progress updates
"""
import json
import logging
from typing import Dict, Any, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.project_subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept new connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        self.active_connections.discard(websocket)

        # Remove from project subscriptions
        for project_id, connections in self.project_subscriptions.items():
            connections.discard(websocket)

        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, project_id: str):
        """Subscribe to project updates"""
        if project_id not in self.project_subscriptions:
            self.project_subscriptions[project_id] = set()
        self.project_subscriptions[project_id].add(websocket)

        await websocket.send_json({
            "type": "subscribed",
            "project_id": project_id
        })

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast to all connections"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)

    async def send_to_project(self, project_id: str, message: Dict[str, Any]):
        """Send message to subscribers of a specific project"""
        if project_id not in self.project_subscriptions:
            return

        disconnected = []
        for connection in self.project_subscriptions[project_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def send_progress(self, project_id: str, task_id: str, progress: float, message: str = ""):
        """Send progress update"""
        await self.send_to_project(project_id, {
            "type": "progress",
            "project_id": project_id,
            "task_id": task_id,
            "progress": progress,
            "message": message,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
