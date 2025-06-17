# GitAIOps EnrichMCP Setup Guide

🚀 **Enhanced AI-powered DevOps platform with EnrichMCP integration and real-time testing dashboard**

## Overview

This guide will help you set up the complete GitAIOps EnrichMCP system with:
- **EnrichMCP Server**: Advanced MCP server with LLM capabilities, file operations, and system commands
- **Real-time Testing Dashboard**: Interactive testing interface with top popup notifications
- **Unified Dashboard**: Comprehensive system monitoring and control center
- **React Frontend**: Modern web interface with live updates

## Prerequisites

### Required Software
- Python 3.11+ 
- Node.js 16+ and npm
- Git

### Required Python Packages
```bash
pip install -r requirements.txt
```

Key dependencies:
- `enrichmcp>=1.0.0` - Core MCP framework
- `fastapi>=0.109.0` - API framework
- `uvicorn[standard]>=0.27.0` - ASGI server
- `websockets>=12.0` - WebSocket support
- `rich>=13.7.0` - Terminal formatting

### Required Node.js Packages
```bash
cd dashboard
npm install
```

## Quick Start

### Option 1: Automated Startup (Recommended)
```bash
python start_enrichmcp_system.py
```

This script will:
1. ✅ Check all dependencies
2. 🚀 Start EnrichMCP server (port 8001)
3. 🎯 Start unified dashboard backend (port 8767)
4. 🧪 Start real-time testing server (port 8765)
5. ⚛️ Start React frontend (port 3000)
6. 📊 Display system status and monitoring

### Option 2: Manual Startup

#### 1. Start EnrichMCP Server
```bash
cd src
python enrichmcp_server.py
```
- Runs on: `http://localhost:8001`
- API docs: `http://localhost:8001/docs`

#### 2. Start Unified Dashboard Backend
```bash
python start_unified_system.py
```
- WebSocket: `ws://localhost:8767`

#### 3. Start Real-time Testing Server
```bash
cd scripts
python start_realtime_testing.py
```
- WebSocket: `ws://localhost:8765`

#### 4. Start React Dashboard
```bash
cd dashboard
npm start
```
- Frontend: `http://localhost:3000`

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Dashboard (3000)                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐  │
│  │ Unified Dash    │ │ Testing Panel   │ │ Top Popup    │  │
│  │                 │ │                 │ │ Notifications│  │
│  └─────────────────┘ └─────────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Unified Dashboard│ │ EnrichMCP Server│ │ Testing Server  │
│ Backend (8767)   │ │    (8001)       │ │    (8765)       │
│                 │ │                 │ │                 │
│ • System Monitor│ │ • Git Ops       │ │ • Real-time     │
│ • Events        │ │ • File Ops      │ │   Test Runner   │
│ • Metrics       │ │ • LLM Chat      │ │ • WebSocket     │
│ • WebSocket     │ │ • Bash Commands │ │ • Live Results  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Features

### 🔧 EnrichMCP Server Features
- **Git Operations**: Repository info, commits, branches, file tracking
- **File Management**: Read, write, append files with safety features  
- **System Commands**: Execute bash commands and Python scripts
- **LLM Integration**: Chat and code analysis with AI models
- **Real-time Testing**: Run and monitor test suites
- **Project Analysis**: Comprehensive summaries and search

### 🎯 Real-time Testing Dashboard
- **Top Popup Notifications**: Persistent testing status at screen top
- **Live Test Monitoring**: Real-time progress and results
- **Multi-test Support**: Unit, integration, e2e, performance, security
- **Interactive Controls**: Start, stop, configure test runs
- **Live Activity Feed**: Streaming test logs and events
- **Visual Progress**: Progress bars and status indicators

### 📊 Unified Dashboard
- **System Health**: CPU, memory, component status
- **Live Events**: Real-time system events and alerts
- **Quick Actions**: One-click operations and triggers
- **Performance Metrics**: System and application monitoring
- **Interactive Controls**: Trigger health checks and analyses

## Usage Examples

### Starting Tests with Top Popup
1. Open React dashboard: `http://localhost:3000`
2. Click the "Testing Popup" quick action button
3. Use the popup controls to start/stop tests
4. Monitor progress in the persistent top notification bar

### Using EnrichMCP API
```python
# Example: Get repository information
curl -X GET "http://localhost:8001/repository/info" \
     -H "accept: application/json"

# Example: Execute bash command  
curl -X POST "http://localhost:8001/execute/bash" \
     -H "Content-Type: application/json" \
     -d '{"command": "git status", "working_directory": "."}'

# Example: Chat with LLM
curl -X POST "http://localhost:8001/llm/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Analyze this code", "model": "gpt-4"}'
```

### WebSocket Connections
```javascript
// Connect to unified dashboard
const ws1 = new WebSocket('ws://localhost:8767');

// Connect to testing server  
const ws2 = new WebSocket('ws://localhost:8765');

// Send test command
ws2.send(JSON.stringify({
  type: 'run_tests',
  testTypes: ['integration', 'unit']
}));
```

## Configuration

### Environment Variables
```bash
# Optional: Configure LLM providers
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"

# Optional: Custom ports
export ENRICHMCP_PORT=8001
export DASHBOARD_PORT=8767
export TESTING_PORT=8765
export REACT_PORT=3000
```

### Test Configuration
Modify test types and settings in:
- `src/testing/realtime_test_runner.py`
- `dashboard/src/components/RealtimeTestingPanel.tsx`

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
lsof -i :8001
lsof -i :3000

# Kill the process
kill -9 <PID>
```

#### Dependencies Missing
```bash
# Reinstall Python dependencies
pip install -r requirements.txt --force-reinstall

# Reinstall Node dependencies  
cd dashboard
rm -rf node_modules package-lock.json
npm install
```

#### WebSocket Connection Failed
1. Ensure all backend services are running
2. Check firewall settings
3. Verify ports are not blocked
4. Check browser console for errors

#### EnrichMCP Import Errors
```bash
# Verify EnrichMCP installation
pip show enrichmcp

# If missing, install directly
pip install enrichmcp>=1.0.0
```

### Logs and Monitoring

#### View Logs
```bash
# EnrichMCP server logs
tail -f logs/enrichmcp.log

# System logs with startup script
python start_enrichmcp_system.py
```

#### Health Checks
- EnrichMCP Health: `http://localhost:8001/health`
- System Status: Check dashboard at `http://localhost:3000`

## Advanced Usage

### Custom Test Types
Add new test types in `RealtimeTestingPanel.tsx`:
```typescript
const testTypes = ['unit', 'integration', 'e2e', 'performance', 'security', 'custom'];
```

### LLM Model Configuration
Configure different models in `enrichmcp_server.py`:
```python
# Available models: gpt-4, gpt-3.5-turbo, claude-3, etc.
await chat_with_llm(
    message="Your prompt", 
    model="gpt-4",
    context="Additional context"
)
```

### Custom Actions
Add quick actions in `UnifiedDashboard.tsx`:
```typescript
<button onClick={() => triggerAction('custom_action', { param: 'value' })}>
  Custom Action
</button>
```

## API Reference

### EnrichMCP Endpoints
- `GET /health` - Health check
- `GET /repository/info` - Get Git repository info
- `POST /execute/bash` - Execute bash command
- `POST /execute/python` - Execute Python script
- `POST /llm/chat` - Chat with LLM
- `POST /llm/analyze` - Analyze code with LLM
- `GET /tests/suites` - Get test suites
- `POST /tests/run` - Run test suite

### WebSocket Events
```typescript
// Unified Dashboard Events
{type: 'dashboard_update', state: DashboardState}
{type: 'trigger_action', action: string, parameters: any}

// Testing Events  
{type: 'test_state', ...TestState}
{type: 'run_tests', testTypes: string[]}
{type: 'test_run_started', run_id: string}
{type: 'test_completed', test_name: string, status: string}
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

🚀 **Ready to revolutionize your DevOps workflow with AI-powered automation!**

For support, create an issue or contact the development team.