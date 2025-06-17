#!/usr/bin/env python3
"""
GitAIOps EnrichMCP System Startup Script
Starts the complete EnrichMCP server with real-time testing dashboard
"""
import asyncio
import subprocess
import time
import sys
import os
import signal
from pathlib import Path
import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import psutil

# Setup
console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnrichMCPSystemManager:
    def __init__(self):
        self.processes = {}
        self.running = False
        self.project_root = Path(__file__).parent
        
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        console.print("\n[bold blue]🔍 Checking Dependencies[/bold blue]")
        
        checks = [
            ("Python 3.11+", sys.version_info >= (3, 11)),
            ("EnrichMCP", self._check_package("enrichmcp")),
            ("FastAPI", self._check_package("fastapi")), 
            ("React Dashboard", (self.project_root / "dashboard" / "node_modules").exists()),
            ("Requirements", (self.project_root / "requirements.txt").exists()),
        ]
        
        table = Table()
        table.add_column("Dependency", style="cyan")
        table.add_column("Status", style="white")
        
        all_good = True
        for name, status in checks:
            if status:
                table.add_row(name, "[green]✓ Available[/green]")
            else:
                table.add_row(name, "[red]✗ Missing[/red]")
                all_good = False
        
        console.print(table)
        
        if not all_good:
            console.print("\n[red]❌ Some dependencies are missing. Please install them first.[/red]")
            console.print("\n[yellow]Installation commands:[/yellow]")
            console.print("pip install -r requirements.txt")
            console.print("cd dashboard && npm install")
            return False
        
        console.print("\n[green]✅ All dependencies are available![/green]")
        return True
    
    def _check_package(self, package_name):
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
    
    async def start_enrichmcp_server(self):
        """Start the EnrichMCP server"""
        console.print("\n[bold blue]🚀 Starting EnrichMCP Server[/bold blue]")
        
        server_script = self.project_root / "src" / "enrichmcp_server.py"
        if not server_script.exists():
            console.print(f"[red]❌ EnrichMCP server script not found at {server_script}[/red]")
            return False
        
        try:
            # Start EnrichMCP server
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(server_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            self.processes['enrichmcp'] = process
            console.print("[green]✅ EnrichMCP Server started[/green]")
            
            # Wait a moment for server to initialize
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to start EnrichMCP server: {e}[/red]")
            return False
    
    async def start_unified_dashboard(self):
        """Start the unified dashboard backend"""
        console.print("\n[bold blue]🎯 Starting Unified Dashboard[/bold blue]")
        
        dashboard_script = self.project_root / "start_unified_system.py"
        if not dashboard_script.exists():
            console.print(f"[red]❌ Unified dashboard script not found at {dashboard_script}[/red]")
            return False
        
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(dashboard_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            self.processes['unified_dashboard'] = process
            console.print("[green]✅ Unified Dashboard started[/green]")
            
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to start unified dashboard: {e}[/red]")
            return False
    
    async def start_react_dashboard(self):
        """Start the React dashboard frontend"""
        console.print("\n[bold blue]⚛️ Starting React Dashboard[/bold blue]")
        
        dashboard_dir = self.project_root / "dashboard"
        if not dashboard_dir.exists():
            console.print(f"[red]❌ Dashboard directory not found at {dashboard_dir}[/red]")
            return False
        
        package_json = dashboard_dir / "package.json"
        if not package_json.exists():
            console.print(f"[red]❌ package.json not found in {dashboard_dir}[/red]")
            return False
        
        try:
            # Check if node_modules exists
            node_modules = dashboard_dir / "node_modules"
            if not node_modules.exists():
                console.print("[yellow]📦 Installing npm dependencies...[/yellow]")
                install_process = await asyncio.create_subprocess_exec(
                    "npm", "install",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=dashboard_dir
                )
                await install_process.wait()
                console.print("[green]✅ Dependencies installed[/green]")
            
            # Start React development server
            process = await asyncio.create_subprocess_exec(
                "npm", "start",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=dashboard_dir
            )
            
            self.processes['react_dashboard'] = process
            console.print("[green]✅ React Dashboard started[/green]")
            
            await asyncio.sleep(3)
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to start React dashboard: {e}[/red]")
            return False
    
    async def start_realtime_testing(self):
        """Start real-time testing server"""
        console.print("\n[bold blue]🧪 Starting Real-time Testing[/bold blue]")
        
        testing_script = self.project_root / "scripts" / "start_realtime_testing.py"
        if not testing_script.exists():
            console.print(f"[red]❌ Real-time testing script not found at {testing_script}[/red]")
            return False
        
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(testing_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            self.processes['realtime_testing'] = process
            console.print("[green]✅ Real-time Testing started[/green]")
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to start real-time testing: {e}[/red]")
            return False
    
    def display_system_status(self):
        """Display the current system status"""
        table = Table(title="🚀 GitAIOps EnrichMCP System Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Port", style="yellow")
        table.add_column("URL", style="blue")
        
        services = [
            ("EnrichMCP Server", "enrichmcp", "8001", "http://localhost:8001"),
            ("Unified Dashboard", "unified_dashboard", "8767", "ws://localhost:8767"),
            ("React Dashboard", "react_dashboard", "3000", "http://localhost:3000"),
            ("Real-time Testing", "realtime_testing", "8765", "ws://localhost:8765"),
        ]
        
        for name, key, port, url in services:
            if key in self.processes:
                process = self.processes[key]
                if process.returncode is None:
                    status = "[green]🟢 Running[/green]"
                else:
                    status = "[red]🔴 Stopped[/red]"
            else:
                status = "[gray]⚪ Not started[/gray]"
            
            table.add_row(name, status, port, url)
        
        console.print(table)
        
        # Show quick access URLs
        console.print("\n[bold yellow]📋 Quick Access URLs:[/bold yellow]")
        console.print("• Main Dashboard: [link]http://localhost:3000[/link]")
        console.print("• EnrichMCP API: [link]http://localhost:8001/docs[/link]")
        console.print("• System Health: [link]http://localhost:8001/health[/link]")
        
        console.print("\n[bold green]🎯 To start testing, use the Real-time Testing panel in the dashboard![/bold green]")
    
    async def monitor_processes(self):
        """Monitor all running processes"""
        console.print("\n[bold blue]📊 Monitoring System...[/bold blue]")
        
        while self.running:
            try:
                # Check process health
                dead_processes = []
                for name, process in self.processes.items():
                    if process.returncode is not None:
                        dead_processes.append(name)
                
                if dead_processes:
                    console.print(f"[red]⚠️ Detected dead processes: {', '.join(dead_processes)}[/red]")
                
                await asyncio.sleep(5)
                
            except Exception as e:
                console.print(f"[red]❌ Monitoring error: {e}[/red]")
                await asyncio.sleep(5)
    
    async def start_system(self):
        """Start the complete EnrichMCP system"""
        console.print(Panel.fit(
            "[bold blue]🚀 GitAIOps EnrichMCP System Startup[/bold blue]\n"
            "[white]Starting comprehensive AI-powered DevOps platform with real-time testing[/white]",
            border_style="blue"
        ))
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        self.running = True
        
        # Start services in order
        services = [
            ("EnrichMCP Server", self.start_enrichmcp_server),
            ("Unified Dashboard", self.start_unified_dashboard),
            ("Real-time Testing", self.start_realtime_testing),
            ("React Dashboard", self.start_react_dashboard),
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for service_name, start_func in services:
                task = progress.add_task(f"Starting {service_name}...", total=None)
                
                success = await start_func()
                if not success:
                    progress.update(task, description=f"❌ Failed to start {service_name}")
                    console.print(f"[red]❌ System startup failed at {service_name}[/red]")
                    return False
                
                progress.update(task, description=f"✅ {service_name} started")
                progress.remove_task(task)
        
        console.print("\n[bold green]🎉 All services started successfully![/bold green]")
        
        # Display system status
        self.display_system_status()
        
        # Start monitoring
        monitor_task = asyncio.create_task(self.monitor_processes())
        
        try:
            console.print("\n[bold yellow]Press Ctrl+C to stop all services[/bold yellow]")
            await monitor_task
        except KeyboardInterrupt:
            console.print("\n[yellow]🛑 Stopping all services...[/yellow]")
            await self.stop_system()
    
    async def stop_system(self):
        """Stop all running processes"""
        self.running = False
        
        for name, process in self.processes.items():
            try:
                if process.returncode is None:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5)
                    console.print(f"[green]✅ Stopped {name}[/green]")
            except asyncio.TimeoutError:
                console.print(f"[yellow]⚠️ Force killing {name}[/yellow]")
                process.kill()
            except Exception as e:
                console.print(f"[red]❌ Error stopping {name}: {e}[/red]")
        
        console.print("\n[bold blue]👋 GitAIOps EnrichMCP System stopped[/bold blue]")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    console.print("\n[yellow]🛑 Received shutdown signal[/yellow]")
    sys.exit(0)

async def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start system manager
    manager = EnrichMCPSystemManager()
    await manager.start_system()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ System error: {e}[/red]")
        sys.exit(1)