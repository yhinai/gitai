#!/usr/bin/env python3
"""
Unified Real-time Dashboard System
Consolidates all GitAIOps components into a single, cohesive real-time experience
"""
import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging
from pathlib import Path
import websockets

logger = logging.getLogger(__name__)

class ComponentStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    OFFLINE = "offline"

class DashboardWidget(Enum):
    SYSTEM_HEALTH = "system_health"
    AI_OPERATIONS = "ai_operations"
    REAL_TIME_TESTING = "real_time_testing"
    SECURITY_MONITORING = "security_monitoring"
    PERFORMANCE_METRICS = "performance_metrics"
    WORKFLOW_STATUS = "workflow_status"
    GITLAB_INTEGRATION = "gitlab_integration"
    NOTIFICATION_CENTER = "notification_center"

@dataclass
class SystemComponent:
    name: str
    status: ComponentStatus
    last_check: str
    metrics: Dict[str, Any]
    endpoint: Optional[str] = None
    version: Optional[str] = None
    uptime: Optional[float] = None

@dataclass
class DashboardState:
    timestamp: str
    components: Dict[str, SystemComponent]
    active_workflows: List[Dict[str, Any]]
    recent_events: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    security_alerts: List[Dict[str, Any]]
    test_results: Dict[str, Any]
    ai_operations: Dict[str, Any]
    user_sessions: int
    system_load: Dict[str, Any]

class UnifiedDashboard:
    """Unified real-time dashboard that consolidates all GitAIOps components"""
    
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.components: Dict[str, SystemComponent] = {}
        self.dashboard_state = DashboardState(
            timestamp=datetime.now(timezone.utc).isoformat(),
            components={},
            active_workflows=[],
            recent_events=[],
            performance_metrics={},
            security_alerts=[],
            test_results={},
            ai_operations={},
            user_sessions=0,
            system_load={}
        )
        
        self.running = False
        self.update_interval = 2.0  # Update every 2 seconds
        self.health_check_interval = 30.0  # Health check every 30 seconds
        
        # Component endpoints
        self.component_endpoints = {
            "api_server": "http://localhost:8000/health",
            "websocket_server": "ws://localhost:8765",
            "unified_events": "ws://localhost:8766",
            "ai_operations": "http://localhost:8000/api/v1/ai/health",
            "gitlab_integration": "http://localhost:8000/api/v1/gitlab/health",
            "testing_system": "http://localhost:8000/api/v1/testing/health"
        }
        
        # Initialize components
        self._initialize_components()
        
        # Start background tasks
        self.background_tasks = []
    
    def _initialize_components(self):
        """Initialize system components"""
        for name, endpoint in self.component_endpoints.items():
            component = SystemComponent(
                name=name,
                status=ComponentStatus.OFFLINE,
                last_check=datetime.now(timezone.utc).isoformat(),
                metrics={},
                endpoint=endpoint
            )
            self.components[name] = component
            self.dashboard_state.components[name] = component
    
    async def start(self, host="localhost", port=8767):
        """Start the unified dashboard server"""
        logger.info(f"Starting Unified Dashboard on {host}:{port}")
        
        # Start background monitoring
        self.background_tasks = [
            asyncio.create_task(self._health_monitor()),
            asyncio.create_task(self._performance_monitor()),
            asyncio.create_task(self._event_aggregator()),
            asyncio.create_task(self._dashboard_updater())
        ]
        
        # Start WebSocket server
        self.server = await websockets.serve(
            self._handle_client,
            host,
            port
        )
        
        self.running = True
        logger.info("Unified Dashboard is running")
        
        return self.server
    
    async def stop(self):
        """Stop the unified dashboard"""
        self.running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Close server
        if hasattr(self, 'server'):
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("Unified Dashboard stopped")
    
    async def _handle_client(self, websocket, path=None):
        """Handle WebSocket client connections"""
        self.clients.add(websocket)
        logger.info(f"Dashboard client connected. Total clients: {len(self.clients)}")
        
        try:
            # Send initial dashboard state
            await self._send_dashboard_state(websocket)
            
            # Handle client messages
            async for message in websocket:
                await self._handle_client_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error handling dashboard client: {e}")
        finally:
            self.clients.discard(websocket)
            self.dashboard_state.user_sessions = len(self.clients)
            logger.info(f"Dashboard client disconnected. Total clients: {len(self.clients)}")
    
    async def _handle_client_message(self, websocket, message):
        """Handle messages from dashboard clients"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                await websocket.send(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
            
            elif message_type == "get_component_details":
                component_name = data.get("component")
                if component_name in self.components:
                    component = self.components[component_name]
                    await websocket.send(json.dumps({
                        "type": "component_details",
                        "component": asdict(component)
                    }))
            
            elif message_type == "trigger_action":
                action = data.get("action")
                await self._handle_dashboard_action(action, data.get("parameters", {}))
            
            elif message_type == "subscribe":
                # Handle widget subscriptions
                widgets = data.get("widgets", [])
                # Store subscription preferences for this client
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from dashboard client: {message}")
    
    async def _handle_dashboard_action(self, action: str, parameters: Dict[str, Any]):
        """Handle actions triggered from the dashboard"""
        if action == "restart_component":
            component_name = parameters.get("component")
            await self._restart_component(component_name)
        
        elif action == "run_health_check":
            await self._run_comprehensive_health_check()
        
        elif action == "trigger_ai_analysis":
            analysis_type = parameters.get("type", "general")
            await self._trigger_ai_analysis(analysis_type)
        
        elif action == "run_security_scan":
            await self._trigger_security_scan()
        
        elif action == "export_metrics":
            await self._export_system_metrics()
    
    async def _health_monitor(self):
        """Continuously monitor component health"""
        while self.running:
            try:
                await self._check_all_components_health()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(5)
    
    async def _check_all_components_health(self):
        """Check health of all components"""
        import aiohttp
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for name, component in self.components.items():
                try:
                    if component.endpoint and component.endpoint.startswith("http"):
                        async with session.get(component.endpoint) as response:
                            if response.status == 200:
                                data = await response.json()
                                component.status = ComponentStatus.HEALTHY
                                component.metrics = data
                            else:
                                component.status = ComponentStatus.ERROR
                                
                    elif component.endpoint and component.endpoint.startswith("ws"):
                        # For WebSocket endpoints, try to connect briefly
                        try:
                            ws = await websockets.connect(component.endpoint, timeout=2)
                            await ws.close()
                            component.status = ComponentStatus.HEALTHY
                        except:
                            component.status = ComponentStatus.OFFLINE
                    
                    component.last_check = datetime.now(timezone.utc).isoformat()
                    
                except Exception as e:
                    component.status = ComponentStatus.ERROR
                    component.metrics = {"error": str(e)}
                    logger.warning(f"Health check failed for {name}: {e}")
    
    async def _performance_monitor(self):
        """Monitor system performance metrics"""
        while self.running:
            try:
                # Collect performance metrics
                metrics = await self._collect_performance_metrics()
                self.dashboard_state.performance_metrics = metrics
                
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in performance monitor: {e}")
                await asyncio.sleep(5)
    
    async def _collect_performance_metrics(self):
        """Collect comprehensive performance metrics"""
        import psutil
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network metrics
        try:
            network = psutil.net_io_counters()
            network_metrics = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        except:
            network_metrics = {}
        
        # Application metrics
        app_metrics = {
            "active_clients": len(self.clients),
            "components_healthy": sum(1 for c in self.components.values() if c.status == ComponentStatus.HEALTHY),
            "total_components": len(self.components),
            "uptime": time.time() - getattr(self, 'start_time', time.time())
        }
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "memory_total": memory.total,
                "disk_percent": disk.percent,
                "disk_free": disk.free,
                "disk_total": disk.total
            },
            "network": network_metrics,
            "application": app_metrics,
            "health_score": self._calculate_health_score()
        }
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score"""
        if not self.components:
            return 0.0
        
        healthy_components = sum(1 for c in self.components.values() if c.status == ComponentStatus.HEALTHY)
        warning_components = sum(1 for c in self.components.values() if c.status == ComponentStatus.WARNING)
        
        # Health score calculation
        total_components = len(self.components)
        health_score = (healthy_components + (warning_components * 0.5)) / total_components
        
        return round(health_score, 2)
    
    async def _event_aggregator(self):
        """Aggregate events from various sources"""
        while self.running:
            try:
                # Collect recent events
                events = await self._collect_recent_events()
                self.dashboard_state.recent_events = events
                
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in event aggregator: {e}")
                await asyncio.sleep(5)
    
    async def _collect_recent_events(self):
        """Collect recent events from various sources"""
        # Mock event collection for demonstration
        mock_events = [
            {
                "id": uuid.uuid4().hex,
                "type": "ai.analysis.completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "ai_system",
                "message": "Security scan completed - 2 vulnerabilities found",
                "priority": "medium"
            },
            {
                "id": uuid.uuid4().hex,
                "type": "test.suite.completed",
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
                "source": "testing_system",
                "message": "Test suite executed - 45/47 tests passed",
                "priority": "low"
            },
            {
                "id": uuid.uuid4().hex,
                "type": "gitlab.mr.created",
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
                "source": "gitlab_webhook",
                "message": "New merge request: Feature/user-authentication",
                "priority": "medium"
            }
        ]
        
        return mock_events[-20:]  # Last 20 events
    
    async def _dashboard_updater(self):
        """Update dashboard state and broadcast to clients"""
        while self.running:
            try:
                # Update dashboard timestamp
                self.dashboard_state.timestamp = datetime.now(timezone.utc).isoformat()
                self.dashboard_state.user_sessions = len(self.clients)
                
                # Broadcast to all clients
                await self._broadcast_dashboard_state()
                
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in dashboard updater: {e}")
                await asyncio.sleep(5)
    
    async def _broadcast_dashboard_state(self):
        """Broadcast current dashboard state to all clients"""
        if not self.clients:
            return
        
        # Convert dashboard state to dict with proper serialization
        state_dict = asdict(self.dashboard_state)
        
        # Convert component status enums to strings
        for comp_name, comp_data in state_dict.get("components", {}).items():
            if "status" in comp_data:
                comp_data["status"] = comp_data["status"].value if hasattr(comp_data["status"], "value") else str(comp_data["status"])
        
        message = json.dumps({
            "type": "dashboard_update",
            "state": state_dict,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.clients.copy():
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending to dashboard client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.discard(client)
    
    async def _send_dashboard_state(self, websocket):
        """Send current dashboard state to a specific client"""
        # Convert dashboard state to dict with proper serialization
        state_dict = asdict(self.dashboard_state)
        
        # Convert component status enums to strings
        for comp_name, comp_data in state_dict.get("components", {}).items():
            if "status" in comp_data:
                comp_data["status"] = comp_data["status"].value if hasattr(comp_data["status"], "value") else str(comp_data["status"])
        
        message = json.dumps({
            "type": "initial_state",
            "state": state_dict,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        try:
            await websocket.send(message)
        except Exception as e:
            logger.error(f"Error sending initial state: {e}")
    
    async def _restart_component(self, component_name: str):
        """Restart a specific component"""
        if component_name in self.components:
            logger.info(f"Restarting component: {component_name}")
            # Implementation would depend on how components are managed
            # For now, just mark as offline and let health check detect recovery
            self.components[component_name].status = ComponentStatus.OFFLINE
    
    async def _run_comprehensive_health_check(self):
        """Run a comprehensive health check on all components"""
        logger.info("Running comprehensive health check")
        await self._check_all_components_health()
        
        # Broadcast immediate update
        await self._broadcast_dashboard_state()
    
    async def _trigger_ai_analysis(self, analysis_type: str):
        """Trigger an AI analysis operation"""
        logger.info(f"Triggering AI analysis: {analysis_type}")
        
        # Mock triggering AI analysis
        mock_event = {
            "id": uuid.uuid4().hex,
            "type": "ai.analysis.started",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "dashboard_trigger",
            "message": f"AI {analysis_type} analysis started",
            "priority": "medium"
        }
        
        self.dashboard_state.recent_events.insert(0, mock_event)
    
    async def _trigger_security_scan(self):
        """Trigger a security scan"""
        logger.info("Triggering security scan")
        
        mock_event = {
            "id": uuid.uuid4().hex,
            "type": "security.scan.started",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "dashboard_trigger",
            "message": "Security scan initiated from dashboard",
            "priority": "high"
        }
        
        self.dashboard_state.recent_events.insert(0, mock_event)
    
    async def _export_system_metrics(self):
        """Export system metrics"""
        logger.info("Exporting system metrics")
        
        # Create metrics export
        export_data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "dashboard_state": asdict(self.dashboard_state),
            "component_health": {name: asdict(comp) for name, comp in self.components.items()}
        }
        
        # Save to file (in a real implementation)
        export_filename = f"gitaiops_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        logger.info(f"Metrics exported to {export_filename}")
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get a summary of the current dashboard state"""
        return {
            "timestamp": self.dashboard_state.timestamp,
            "health_score": self._calculate_health_score(),
            "active_clients": len(self.clients),
            "components_status": {
                name: comp.status.value for name, comp in self.components.items()
            },
            "recent_events_count": len(self.dashboard_state.recent_events),
            "system_load": self.dashboard_state.performance_metrics.get("system", {}),
            "uptime": time.time() - getattr(self, 'start_time', time.time())
        }

# Global instance
unified_dashboard = UnifiedDashboard()

# Convenience functions
async def start_unified_dashboard(host="localhost", port=8767):
    """Start the unified dashboard"""
    unified_dashboard.start_time = time.time()
    return await unified_dashboard.start(host, port)

async def stop_unified_dashboard():
    """Stop the unified dashboard"""
    await unified_dashboard.stop()

def get_dashboard_summary():
    """Get dashboard summary"""
    return unified_dashboard.get_dashboard_summary()

if __name__ == "__main__":
    async def main():
        # Start the unified dashboard
        await start_unified_dashboard()
        
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            await stop_unified_dashboard()
    
    asyncio.run(main())