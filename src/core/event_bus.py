"""
Event Bus for inter-agent communication and monitoring
Supports pub/sub pattern with async handlers
"""
import asyncio
import json
import logging
from typing import Dict, List, Callable, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import weakref

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event data structure"""
    type: str
    source: str
    payload: Dict[str, Any]
    timestamp: str = ""
    event_id: str = ""
    correlation_id: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.event_id:
            import uuid
            self.event_id = str(uuid.uuid4())

    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "correlation_id": self.correlation_id
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class EventBus:
    """
    Async event bus for decoupled agent communication
    Features:
    - Pattern-based subscription (wildcards supported)
    - Event persistence for replay
    - Priority queues
    - Backpressure handling
    """

    def __init__(self, max_queue_size: int = 10000):
        self._subscribers: Dict[str, List[weakref.ref]] = defaultdict(list)
        self._pattern_subscribers: List[tuple] = []  # (pattern, handler_ref)
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._running = False
        self._dispatcher_task: Optional[asyncio.Task] = None
        self._metrics = {
            "published": 0,
            "delivered": 0,
            "dropped": 0,
            "errors": 0
        }

    async def start(self):
        """Start the event dispatcher"""
        if not self._running:
            self._running = True
            self._dispatcher_task = asyncio.create_task(self._dispatch_loop())
            logger.info("Event bus started")

    async def stop(self):
        """Stop the event dispatcher"""
        self._running = False
        if self._dispatcher_task:
            self._dispatcher_task.cancel()
            try:
                await self._dispatcher_task
            except asyncio.CancelledError:
                pass
            logger.info("Event bus stopped")

    async def _dispatch_loop(self):
        """Main dispatch loop"""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch_event(event)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Dispatch loop error: {e}")
                self._metrics["errors"] += 1

    async def _dispatch_event(self, event: Event):
        """Dispatch event to all matching subscribers"""
        handlers = []

        # Exact match subscribers
        for ref in self._subscribers.get(event.type, []):
            handler = ref()
            if handler:
                handlers.append(handler)

        # Pattern match subscribers
        import fnmatch
        for pattern, ref in self._pattern_subscribers:
            if fnmatch.fnmatch(event.type, pattern):
                handler = ref()
                if handler:
                    handlers.append(handler)

        # Execute handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                self._metrics["delivered"] += 1
            except Exception as e:
                logger.error(f"Handler error for event {event.type}: {e}")
                self._metrics["errors"] += 1

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to specific event type"""
        ref = weakref.ref(handler)
        self._subscribers[event_type].append(ref)
        logger.debug(f"Subscribed to {event_type}")

    def subscribe_pattern(self, pattern: str, handler: Callable):
        """Subscribe to events matching pattern (e.g., 'workflow.*')"""
        ref = weakref.ref(handler)
        self._pattern_subscribers.append((pattern, ref))
        logger.debug(f"Subscribed to pattern {pattern}")

    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe from event type"""
        self._subscribers[event_type] = [
            ref for ref in self._subscribers[event_type]
            if ref() is not None and ref() is not handler
        ]

    async def publish(self, event: Event):
        """Publish event to the bus"""
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Add to queue
        try:
            self._queue.put_nowait(event)
            self._metrics["published"] += 1
        except asyncio.QueueFull:
            logger.warning("Event queue full, dropping event")
            self._metrics["dropped"] += 1

    async def publish_sync(self, event_type: str, source: str, payload: Dict[str, Any], 
                          correlation_id: Optional[str] = None):
        """Convenience method to create and publish event"""
        event = Event(
            type=event_type,
            source=source,
            payload=payload,
            correlation_id=correlation_id
        )
        await self.publish(event)

    def get_history(self, event_type: Optional[str] = None, 
                   limit: int = 100) -> List[Event]:
        """Get event history, optionally filtered by type"""
        events = self._event_history
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]

    def get_metrics(self) -> Dict[str, int]:
        """Get event bus metrics"""
        return self._metrics.copy()

    def clear_history(self):
        """Clear event history"""
        self._event_history.clear()


class EventLogger:
    """Utility class for logging events"""

    def __init__(self, event_bus: EventBus, logger_name: str = "ai_manhua"):
        self.event_bus = event_bus
        self.logger = logging.getLogger(logger_name)

    async def log_progress(self, task_id: str, progress: float, message: str = ""):
        """Log progress event"""
        await self.event_bus.publish_sync(
            "task.progress",
            "event_logger",
            {
                "task_id": task_id,
                "progress": progress,
                "message": message
            }
        )
        self.logger.info(f"[{task_id}] {progress:.1%} - {message}")

    async def log_error(self, task_id: str, error: str, details: Dict = None):
        """Log error event"""
        await self.event_bus.publish_sync(
            "task.error",
            "event_logger",
            {
                "task_id": task_id,
                "error": error,
                "details": details or {}
            }
        )
        self.logger.error(f"[{task_id}] Error: {error}")

    async def log_info(self, task_id: str, message: str, data: Dict = None):
        """Log info event"""
        await self.event_bus.publish_sync(
            "task.info",
            "event_logger",
            {
                "task_id": task_id,
                "message": message,
                "data": data or {}
            }
        )
        self.logger.info(f"[{task_id}] {message}")
