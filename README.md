# GitAIOps Platform

**AI-Powered GitLab Operations** - Complete platform in 2 files

## 🚀 Quick Start

```bash
python start.py
```

**That's it!** Access your dashboard at: http://localhost:8000/dashboard

## ✨ What You Get

- **🤖 Gemini AI** - Smart merge request analysis
- **📊 Real-time Dashboard** - Live GitLab monitoring  
- **💬 AI Chat** - DevOps assistant
- **⚡ WebSocket API** - Real-time updates
- **🔧 Auto-setup** - Zero configuration needed

## 📋 Requirements

- Python 3.12+
- Node.js (for dashboard)

## 🎯 Features

| Feature | Endpoint |
|---------|----------|
| Dashboard | http://localhost:8000/dashboard |
| API Docs | http://localhost:8000/docs |
| AI Chat | http://localhost:8000/api/v1/ai/chat/demo |
| MR Triage | http://localhost:8000/api/v1/ai/triage/demo |
| Health Check | http://localhost:8000/health |

## 🏗️ Architecture

- **`gitaiops.py`** - Complete backend (FastAPI + AI + WebSocket)
- **`start.py`** - Auto-setup and launcher
- **`dashboard/`** - React frontend
- **`templates/`** - CI/CD templates

## 🛠️ Development

**Run tests:**
```bash
python -c "from gitaiops import *; print('✅ All imports work')"
```

**Manual start:**
```bash
python -m uvicorn gitaiops:create_app --reload --port 8000
```

---

**GitAIOps** - Maximum power, minimum complexity 🚀