# GitAIOps Platform

**AI-Powered GitLab Operations** - Real GitLab integration with production-ready AI analysis

## 🚀 Quick Start

```bash
python start.py
```

**Server starts on port 8000** (automatically frees port if busy)

Access your dashboard at: http://localhost:8000/dashboard

## ✨ What You Get

- **🤖 Gemini AI** - Real merge request analysis
- **🛡️ Security Scanner** - Vulnerability detection in real MRs
- **⚡ Pipeline Optimizer** - Real pipeline performance analysis
- **📊 Real-time Dashboard** - Live GitLab monitoring  
- **🔧 Real GitLab API** - No mock data, all real integration

## 📋 Requirements

- Python 3.12+
- Node.js (for dashboard)
- GitLab API token (configured in environment)

## 🎯 Real GitLab Integration

### Configure your GitLab credentials:
```bash
export GITLAB_TOKEN="your-gitlab-token"
export GITLAB_URL="https://gitlab.com"  # or your GitLab instance
export GEMINI_API_KEY="your-gemini-key"
```

### API Endpoints (Real Data Only)

| Feature | Endpoint | Example |
|---------|----------|---------|
| **Health Check** | `GET /health` | http://localhost:8000/health |
| **Dashboard** | `GET /dashboard` | http://localhost:8000/dashboard |
| **API Docs** | `GET /docs` | http://localhost:8000/docs |

### AI Analysis Endpoints

| Analysis Type | Endpoint | Description |
|---------------|----------|-------------|
| **MR Triage** | `GET /api/v1/ai/triage/{project_id}/mr/{mr_iid}` | AI-powered merge request analysis |
| **Security Scan** | `GET /api/v1/ai/security/{project_id}/mr/{mr_iid}` | Vulnerability scanning |
| **Pipeline Analysis** | `GET /api/v1/ai/pipeline/{project_id}` | Pipeline optimization suggestions |

### 🧠 NEW: Activity Analysis Endpoints (LLM-Powered)

| Feature | Endpoint | Description |
|---------|----------|-------------|
| **Project Activities** | `GET /api/v1/activities/project/{project_id}` | Comprehensive LLM analysis of all project activities |
| **Trigger Analysis** | `POST /api/v1/activities/analyze/{project_id}` | Start comprehensive background activity analysis |
| **Activity Insights** | `GET /api/v1/activities/insights/{project_id}` | LLM-generated strategic insights and recommendations |
| **Real-time Stream** | `GET /api/v1/activities/realtime/{project_id}` | Live activity stream with AI analysis |
| **Execute Commands** | `POST /api/v1/activities/command` | Execute LLM-suggested automation commands |

### GitLab Data Endpoints

| Data Type | Endpoint | Description |
|-----------|----------|-------------|
| **Project Info** | `GET /api/v1/gitlab/projects/{project_id}` | Get project details |
| **Merge Requests** | `GET /api/v1/gitlab/projects/{project_id}/merge_requests` | List project MRs |
| **Pipelines** | `GET /api/v1/gitlab/projects/{project_id}/pipelines` | List project pipelines |

## 🔍 Real Usage Examples

### Analyze a Merge Request
```bash
# Get project's merge requests
curl "http://localhost:8000/api/v1/gitlab/projects/70835889/merge_requests"

# Analyze specific MR with AI
curl "http://localhost:8000/api/v1/ai/triage/70835889/mr/2"
```

### Security Scan
```bash
# Scan MR for vulnerabilities
curl "http://localhost:8000/api/v1/ai/security/70835889/mr/2"
```

### Pipeline Optimization
```bash
# Analyze pipeline performance
curl "http://localhost:8000/api/v1/ai/pipeline/70835889"
```

### 🚀 NEW: Activity Analysis with LLM

```bash
# Get comprehensive project activities with AI insights
curl "http://localhost:8000/api/v1/activities/project/70835889"

# Trigger comprehensive background analysis
curl -X POST "http://localhost:8000/api/v1/activities/analyze/70835889"

# Get strategic insights and recommendations
curl "http://localhost:8000/api/v1/activities/insights/70835889"

# Get real-time activity stream
curl "http://localhost:8000/api/v1/activities/realtime/70835889"

# Execute LLM-suggested commands
curl -X POST "http://localhost:8000/api/v1/activities/command" \
  -H "Content-Type: application/json" \
  -d '{"type": "analyze_mr", "parameters": {"project_id": 70835889, "mr_id": 2}}'
```

## 🏗️ Architecture

- **`gitaiops.py`** - Complete backend (FastAPI + Real GitLab API + AI)
- **`start.py`** - Auto-setup and launcher (always port 8000)
- **`dashboard/`** - React frontend
- **`templates/`** - CI/CD templates

## 🛠️ Development

**Test system health:**
```bash
curl http://localhost:8000/health
```

**Manual start:**
```bash
python -m uvicorn gitaiops:create_app --reload --port 8000
```

**Check real GitLab connectivity:**
```bash
curl "http://localhost:8000/api/v1/gitlab/projects/{your-project-id}"
```

## ⚙️ Configuration

All configuration via environment variables:

```bash
# GitLab Configuration
GITLAB_TOKEN=glpat-xxxxxxxxxxxxx
GITLAB_URL=https://gitlab.com
GITLAB_API_URL=https://gitlab.com/api/v4

# AI Configuration  
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxx
GEMINI_MODEL=gemini-2.0-flash

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## 🚀 Features

✅ **Real GitLab Integration** - No mock data, actual API calls
✅ **AI MR Triage** - Risk assessment, review time estimation, expert suggestions  
✅ **Security Scanner** - Pattern detection, dependency analysis, secrets scanning
✅ **Pipeline Optimizer** - Performance analysis, cost savings estimation
✅ **🧠 LLM Activity Analysis** - Comprehensive project activity insights with Gemini
✅ **🤖 Intelligent Command Execution** - LLM-powered automation and recommendations
✅ **📊 Real-time Activity Monitoring** - Live activity streams with AI analysis
✅ **🎯 Strategic Insights** - High-level project health and velocity analysis
✅ **Auto Port Management** - Always uses port 8000, kills conflicts
✅ **Production Ready** - Health monitoring, error handling, caching

---

**GitAIOps** - Real AI for Real GitLab Projects 🚀