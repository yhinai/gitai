#!/usr/bin/env python3
"""
Unified GitAIOps Platform Startup Script
Launches all components of the unified real-time system
"""
import asyncio
import sys
import signal
import subprocess
import time
from pathlib import Path
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedSystemLauncher:
    """Launch and manage all GitAIOps platform components"""
    
    def __init__(self):
        self.processes = {}
        self.servers = {}
        self.running = False
        self.base_path = Path(__file__).parent
    
    async def start_component(self, name: str, module_path: str, host: str = "localhost", port: int = None):
        """Start a component server"""
        try:
            logger.info(f"Starting {name}...")
            
            if name == "api_server":
                # Start FastAPI server
                cmd = [
                    sys.executable, "-m", "uvicorn",
                    "src.api.main:app",
                    "--host", host,
                    "--port", str(port),
                    "--reload"
                ]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=self.base_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                self.processes[name] = process
                
            elif name == "dashboard":
                # Start React development server
                dashboard_path = self.base_path / "dashboard"
                if (dashboard_path / "package.json").exists():
                    cmd = ["npm", "start"]
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        cwd=dashboard_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    self.processes[name] = process
                else:
                    logger.warning(f"Dashboard package.json not found at {dashboard_path}")
                    
            else:
                # Start Python module directly
                try:
                    if name == "unified_events":
                        from src.core.unified_event_system import start_unified_system
                        server = await start_unified_system(host, port)
                        self.servers[name] = server
                        logger.info(f"✅ {name} started successfully on {host}:{port}")
                    elif name == "unified_dashboard":
                        from src.core.unified_dashboard import start_unified_dashboard
                        server = await start_unified_dashboard(host, port)
                        self.servers[name] = server
                        logger.info(f"✅ {name} started successfully on {host}:{port}")
                    elif name == "websocket_testing":
                        from src.testing.websocket_server import TestingWebSocketServer
                        server_instance = TestingWebSocketServer()
                        server = await server_instance.start(host, port)
                        self.servers[name] = server
                        logger.info(f"✅ {name} started successfully on {host}:{port}")
                    else:
                        logger.error(f"❌ Unknown component: {name}")
                        return False
                except ImportError as e:
                    logger.error(f"❌ Failed to import {name}: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to start {name}: {e}")
            return False
            
        return True
    
    async def start_all_components(self):
        """Start all GitAIOps platform components"""
        
        print("\n" + "="*60)
        print("🚀 Starting GitAIOps Unified Platform")
        print("="*60)
        
        # Component configuration
        components = [
            {
                "name": "unified_events",
                "module": "src.core.unified_event_system",
                "host": "localhost",
                "port": 8766,
                "description": "Real-time event system and WebSocket server"
            },
            {
                "name": "unified_dashboard",
                "module": "src.core.unified_dashboard",
                "host": "localhost", 
                "port": 8767,
                "description": "Unified dashboard with real-time monitoring"
            },
            {
                "name": "websocket_testing",
                "module": "src.testing.websocket_server",
                "host": "localhost",
                "port": 8765,
                "description": "Real-time testing WebSocket server"
            },
            {
                "name": "api_server",
                "module": "src.api.main",
                "host": "localhost",
                "port": 8000,
                "description": "Main FastAPI application server"
            },
            {
                "name": "dashboard",
                "module": "dashboard",
                "host": "localhost",
                "port": 3000,
                "description": "React dashboard frontend"
            }
        ]
        
        # Start components in order
        for component in components:
            print(f"\n📦 {component['description']}")
            success = await self.start_component(
                component["name"],
                component["module"],
                component["host"],
                component["port"]
            )
            
            if success:
                print(f"   ✅ {component['name']} -> http://{component['host']}:{component['port']}")
            else:
                print(f"   ❌ Failed to start {component['name']}")
            
            # Small delay between starts
            await asyncio.sleep(1)
        
        self.running = True
        
        print("\n" + "="*60)
        print("🎉 GitAIOps Unified Platform Started Successfully!")
        print("="*60)
        print("\n📍 Access Points:")
        print("   🌐 Main Dashboard:      http://localhost:8000/dashboard")
        print("   🎛️  Unified Dashboard:   http://localhost:8767 (WebSocket)")
        print("   🔧 API Documentation:   http://localhost:8000/docs")
        print("   ⚡ Real-time Events:    ws://localhost:8766")
        print("   🧪 Testing WebSocket:   ws://localhost:8765")
        print("   📱 React Frontend:      http://localhost:3000")
        
        print("\n🤖 AI Operations:")
        print("   🔍 MR Triage:           AI-powered merge request analysis")
        print("   💬 AI Assistant:        Interactive chat for project insights")
        print("   🛡️  Security Scan:       Real-time vulnerability detection")
        print("   ⚡ Performance:         Code optimization analysis")
        
        print("\n📊 Real-time Features:")
        print("   🔄 Live Updates:        All dashboards update in real-time")
        print("   📡 Event Broadcasting:  Unified event system across platform")
        print("   🎯 Smart Automation:    Intelligent workflow orchestration")
        print("   📈 Health Monitoring:   System performance and component health")
        
        print(f"\n⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔥 Platform is now running in unified real-time mode!")
        print("\n" + "="*60)
    
    async def health_check(self):
        """Perform health check on all components"""
        print("\n🏥 Running health check...")
        
        health_status = {}
        
        # Check WebSocket servers
        for name, server in self.servers.items():
            try:
                if hasattr(server, 'is_serving') and server.is_serving():
                    health_status[name] = "✅ Healthy"
                else:
                    health_status[name] = "⚠️  Unknown"
            except:
                health_status[name] = "❌ Error"
        
        # Check processes
        for name, process in self.processes.items():
            try:
                if process.returncode is None:
                    health_status[name] = "✅ Running"
                else:
                    health_status[name] = "❌ Stopped"
            except:
                health_status[name] = "❌ Error"
        
        print("\n📊 Component Health Status:")
        for name, status in health_status.items():
            print(f"   {name}: {status}")
        
        return health_status
    
    async def stop_all_components(self):
        """Stop all components gracefully"""
        print("\n🛑 Shutting down GitAIOps Unified Platform...")
        
        # Stop servers
        for name, server in self.servers.items():
            try:
                print(f"   Stopping {name}...")
                if hasattr(server, 'close'):
                    server.close()
                    if hasattr(server, 'wait_closed'):
                        await server.wait_closed()
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
        
        # Terminate processes
        for name, process in self.processes.items():
            try:
                print(f"   Terminating {name}...")
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                print(f"   Force killing {name}...")
                process.kill()
            except Exception as e:
                logger.error(f"Error terminating {name}: {e}")
        
        self.running = False
        print("✅ All components stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n📧 Received signal {signum}")
            asyncio.create_task(self.stop_all_components())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main entry point"""
    launcher = UnifiedSystemLauncher()
    launcher.setup_signal_handlers()
    
    try:
        # Start all components
        await launcher.start_all_components()
        
        # Keep running and perform periodic health checks
        while launcher.running:
            await asyncio.sleep(30)  # Health check every 30 seconds
            try:
                await launcher.health_check()
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    except KeyboardInterrupt:
        print("\n⌨️  Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await launcher.stop_all_components()

if __name__ == "__main__":
    print("🌟 GitAIOps Unified Platform Launcher")
    print("=====================================")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)