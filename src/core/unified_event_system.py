#!/usr/bin/env python3
"""
Unified Real-time Event System for GitAIOps Platform
Centralizes all events, notifications, and real-time updates across the entire platform
"""
import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
import logging
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventType(Enum):
    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_HEALTH = "system.health"
    
    # AI Events
    AI_ANALYSIS_STARTED = "ai.analysis.started"
    AI_ANALYSIS_PROGRESS = "ai.analysis.progress"
    AI_ANALYSIS_COMPLETED = "ai.analysis.completed"
    AI_ANALYSIS_FAILED = "ai.analysis.failed"
    AI_CHAT_MESSAGE = "ai.chat.message"
    AI_CHAT_RESPONSE = "ai.chat.response"
    
    # Testing Events
    TEST_SUITE_STARTED = "test.suite.started"
    TEST_PROGRESS = "test.progress"
    TEST_COMPLETED = "test.completed"
    TEST_FAILED = "test.failed"
    
    # GitLab Events
    GITLAB_MR_CREATED = "gitlab.mr.created"
    GITLAB_MR_UPDATED = "gitlab.mr.updated"
    GITLAB_PIPELINE_STARTED = "gitlab.pipeline.started"
    GITLAB_PIPELINE_COMPLETED = "gitlab.pipeline.completed"
    
    # Security Events
    SECURITY_SCAN_STARTED = "security.scan.started"
    SECURITY_VULNERABILITY_FOUND = "security.vulnerability.found"
    SECURITY_SCAN_COMPLETED = "security.scan.completed"
    
    # Performance Events
    PERFORMANCE_ANALYSIS_STARTED = "performance.analysis.started"
    PERFORMANCE_ISSUE_DETECTED = "performance.issue.detected"
    PERFORMANCE_ANALYSIS_COMPLETED = "performance.analysis.completed"
    
    # Notification Events
    NOTIFICATION_CREATED = "notification.created"
    ALERT_TRIGGERED = "alert.triggered"
    
    # Dashboard Events
    DASHBOARD_USER_CONNECTED = "dashboard.user.connected"
    DASHBOARD_USER_DISCONNECTED = "dashboard.user.disconnected"

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Event:
    id: str
    type: EventType
    timestamp: str
    source: str
    data: Dict[str, Any]
    priority: Priority = Priority.MEDIUM
    tags: List[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class UnifiedEventSystem:
    """Centralized event system for the entire GitAIOps platform"""
    
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history = 1000
        self.server = None
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Performance metrics
        self.metrics = {
            "events_processed": 0,
            "clients_connected": 0,
            "events_per_second": 0,
            "last_metric_update": time.time()
        }
        
        # Auto-setup event handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default event handlers for system monitoring"""
        
        @self.on(EventType.DASHBOARD_USER_CONNECTED)
        async def handle_user_connected(event: Event):
            self.metrics["clients_connected"] = len(self.clients)
            logger.info(f"User connected: {event.data.get('user_id', 'unknown')}")
        
        @self.on(EventType.DASHBOARD_USER_DISCONNECTED)
        async def handle_user_disconnected(event: Event):
            self.metrics["clients_connected"] = len(self.clients)
            logger.info(f"User disconnected: {event.data.get('user_id', 'unknown')}")
        
        @self.on(EventType.AI_ANALYSIS_STARTED)
        async def handle_ai_started(event: Event):
            # Automatically create progress tracking
            await self.emit(EventType.AI_ANALYSIS_PROGRESS, {
                "operation_id": event.data.get("operation_id"),
                "progress": 0.1,
                "status": "initializing",
                "message": f"Starting {event.data.get('analysis_type', 'analysis')}..."
            }, source="ai_system")
        
        @self.on(EventType.TEST_SUITE_STARTED)
        async def handle_test_started(event: Event):
            # Auto-trigger AI analysis of test results
            await self.emit(EventType.AI_ANALYSIS_STARTED, {
                "operation_id": f"test_analysis_{uuid.uuid4().hex[:8]}",
                "analysis_type": "test_quality_analysis",
                "trigger": "automated",
                "test_suite_id": event.data.get("suite_id")
            }, source="automation_engine")
    
    def on(self, event_type: EventType):
        """Decorator to register event handlers"""
        def decorator(func: Callable):
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(func)
            return func
        return decorator
    
    async def emit(self, event_type: EventType, data: Dict[str, Any], 
                   source: str = "system", priority: Priority = Priority.MEDIUM,
                   tags: List[str] = None, user_id: str = None, session_id: str = None):
        """Emit an event to all subscribers"""
        
        event = Event(
            id=uuid.uuid4().hex,
            type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            data=data,
            priority=priority,
            tags=tags or [],
            user_id=user_id,
            session_id=session_id
        )
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Update metrics
        self.metrics["events_processed"] += 1
        self._update_metrics()
        
        # Process event handlers
        await self._process_event_handlers(event)
        
        # Broadcast to WebSocket clients
        await self._broadcast_to_clients(event)
        
        logger.debug(f"Event emitted: {event_type.value} from {source}")
        
        return event
    
    async def _process_event_handlers(self, event: Event):
        """Process all registered handlers for an event"""
        handlers = self.event_handlers.get(event.type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    # Run sync handlers in thread pool
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor, handler, event
                    )
            except Exception as e:
                logger.error(f"Error in event handler for {event.type.value}: {e}")
    
    async def _broadcast_to_clients(self, event: Event):
        """Broadcast event to all connected WebSocket clients"""
        if not self.clients:
            return
        
        # Convert event to dict with proper serialization
        event_dict = asdict(event)
        event_dict["type"] = event.type.value  # Convert enum to string
        event_dict["priority"] = event.priority.value  # Convert enum to string
        
        message = json.dumps({
            "event": event_dict,
            "metadata": {
                "server_time": datetime.now(timezone.utc).isoformat(),
                "client_count": len(self.clients)
            }
        })
        
        # Send to all clients
        disconnected_clients = set()
        for client in self.clients.copy():
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.discard(client)
            await self.emit(EventType.DASHBOARD_USER_DISCONNECTED, {
                "client_id": id(client),
                "disconnect_reason": "connection_lost"
            })
    
    def _update_metrics(self):
        """Update performance metrics"""
        now = time.time()
        time_diff = now - self.metrics["last_metric_update"]
        
        if time_diff >= 1.0:  # Update every second
            self.metrics["events_per_second"] = int(self.metrics["events_processed"] / time_diff)
            self.metrics["events_processed"] = 0
            self.metrics["last_metric_update"] = now
    
    async def handle_client_connection(self, websocket, path=None):
        """Handle new WebSocket client connections"""
        
        # Add client
        self.clients.add(websocket)
        
        # Emit connection event
        await self.emit(EventType.DASHBOARD_USER_CONNECTED, {
            "client_id": id(websocket),
            "connection_time": datetime.now(timezone.utc).isoformat(),
            "path": path
        })
        
        # Send welcome message with recent events
        welcome_data = {
            "type": "welcome",
            "recent_events": [asdict(event) for event in self.event_history[-10:]],
            "metrics": self.metrics
        }
        
        try:
            await websocket.send(json.dumps(welcome_data))
            
            # Keep connection alive and handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # Remove client
            self.clients.discard(websocket)
            await self.emit(EventType.DASHBOARD_USER_DISCONNECTED, {
                "client_id": id(websocket),
                "disconnect_time": datetime.now(timezone.utc).isoformat()
            })
    
    async def _handle_client_message(self, websocket, data: Dict[str, Any]):
        """Handle messages from WebSocket clients"""
        
        message_type = data.get("type")
        
        if message_type == "ping":
            # Respond to ping
            await websocket.send(json.dumps({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}))
            
        elif message_type == "subscribe":
            # Handle event subscriptions
            event_types = data.get("event_types", [])
            # Store subscription preferences (could be implemented)
            
        elif message_type == "trigger_action":
            # Handle client-triggered actions
            action = data.get("action")
            if action == "run_tests":
                await self.emit(EventType.TEST_SUITE_STARTED, {
                    "suite_id": f"manual_{uuid.uuid4().hex[:8]}",
                    "test_types": data.get("test_types", ["unit"]),
                    "triggered_by": "user",
                    "client_id": id(websocket)
                }, source="manual_trigger")
                
            elif action == "ai_analysis":
                await self.emit(EventType.AI_ANALYSIS_STARTED, {
                    "operation_id": f"manual_{uuid.uuid4().hex[:8]}",
                    "analysis_type": data.get("analysis_type", "general"),
                    "triggered_by": "user",
                    "client_id": id(websocket)
                }, source="manual_trigger")
    
    async def start_server(self, host="localhost", port=8766):
        """Start the unified WebSocket server"""
        
        logger.info(f"Starting Unified Event System on {host}:{port}")
        
        self.server = await websockets.serve(
            self.handle_client_connection,
            host,
            port
        )
        
        self.running = True
        
        # Emit startup event
        await self.emit(EventType.SYSTEM_STARTUP, {
            "host": host,
            "port": port,
            "startup_time": datetime.now(timezone.utc).isoformat()
        }, source="event_system")
        
        logger.info("Unified Event System is running")
        
        return self.server
    
    async def stop_server(self):
        """Stop the unified WebSocket server"""
        
        if self.server:
            await self.emit(EventType.SYSTEM_SHUTDOWN, {
                "shutdown_time": datetime.now(timezone.utc).isoformat(),
                "events_processed": self.metrics["events_processed"]
            }, source="event_system")
            
            self.server.close()
            await self.server.wait_closed()
            self.running = False
            
        logger.info("Unified Event System stopped")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            **self.metrics,
            "total_events": len(self.event_history),
            "event_handlers": {et.value: len(handlers) for et, handlers in self.event_handlers.items()},
            "active_clients": len(self.clients),
            "system_uptime": time.time() - self.metrics.get("startup_time", time.time())
        }
    
    def get_recent_events(self, limit: int = 50, event_type: Optional[EventType] = None) -> List[Event]:
        """Get recent events, optionally filtered by type"""
        events = self.event_history[-limit:] if not event_type else [
            e for e in self.event_history if e.type == event_type
        ][-limit:]
        
        return sorted(events, key=lambda e: e.timestamp, reverse=True)

# Global instance
unified_events = UnifiedEventSystem()

# Convenience functions
async def emit_event(event_type: EventType, data: Dict[str, Any], **kwargs):
    """Convenience function to emit events"""
    return await unified_events.emit(event_type, data, **kwargs)

def on_event(event_type: EventType):
    """Convenience decorator for event handlers"""
    return unified_events.on(event_type)

async def start_unified_system(host="localhost", port=8766):
    """Start the unified event system"""
    return await unified_events.start_server(host, port)

async def stop_unified_system():
    """Stop the unified event system"""
    await unified_events.stop_server()

# Example usage and demo functions
async def demo_automated_workflow():
    """Demonstrate automated workflow capabilities"""
    
    # Simulate a GitLab MR creation
    await emit_event(EventType.GITLAB_MR_CREATED, {
        "mr_id": "123",
        "title": "Feature: Add user authentication",
        "author": "developer@company.com",
        "changed_files": ["auth.py", "models.py", "tests.py"]
    }, source="gitlab_webhook")
    
    # This will automatically trigger AI analysis
    await asyncio.sleep(0.1)
    
    # Simulate AI analysis progress
    operation_id = f"auto_{uuid.uuid4().hex[:8]}"
    for progress in [0.2, 0.4, 0.6, 0.8, 1.0]:
        await emit_event(EventType.AI_ANALYSIS_PROGRESS, {
            "operation_id": operation_id,
            "progress": progress,
            "status": "analyzing" if progress < 1.0 else "completed"
        }, source="ai_system")
        await asyncio.sleep(0.5)
    
    # Emit completion
    await emit_event(EventType.AI_ANALYSIS_COMPLETED, {
        "operation_id": operation_id,
        "result": {
            "risk_level": "medium",
            "issues_found": 2,
            "auto_mergeable": False,
            "confidence": 0.85
        }
    }, source="ai_system")

if __name__ == "__main__":
    async def main():
        # Start the unified event system
        await start_unified_system()
        
        # Run demo workflow
        await demo_automated_workflow()
        
        # Keep running
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            await stop_unified_system()
    
    asyncio.run(main())