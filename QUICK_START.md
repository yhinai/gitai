# Quick Start Guide

Get GitAIOps Platform running in 5 minutes.

## Prerequisites

- Python 3.12+
- Conda/Miniconda
- Git

## 1. Clone & Setup Environment

```bash
git clone <repository-url>
cd gitaiops-platform
conda env create -f environment.yml
conda activate gitaiops
```

## 2. Quick Setup (Automated)

```bash
chmod +x scripts/quick-setup.sh
./scripts/quick-setup.sh
```

## 3. Start the Platform

```bash
conda activate gitaiops
PYTHONPATH=. python -m uvicorn src.api.main:app --reload --port 8000
```

## 4. Verify Installation

Open your browser to:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/
- **Main Dashboard**: http://localhost:8000/

## 5. Test Core Features

```bash
# Run integration tests
conda activate gitaiops
python scripts/integration_test.py
```

## What's Included

- ✅ **Claude Sonnet 4 AI** - Advanced decision-making
- ✅ **GitLab Integration** - Real project analysis  
- ✅ **Event Processing** - Real-time monitoring
- ✅ **Service Registry** - Component management
- ✅ **API Documentation** - Interactive Swagger UI

## Next Steps

- See [README.md](README.md) for detailed features
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Explore API endpoints at `/docs`

## Support

If you encounter issues, check the troubleshooting guide or review the logs for specific error messages. 