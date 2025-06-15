# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Running the Platform
```bash
# Primary method - uses conda environment and installs dependencies
./run.sh

# Alternative method (if run.sh fails)
PYTHONPATH=. uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

# Quick health check
python test.py

# Test specific features
python scripts/test_chatops.py
```

### Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run with explicit Python path
PYTHONPATH=. python src/main.py

# Test GitLab integration
python test_gitlab_integration.py

# API demonstration
python scripts/demo_api.py
```

### Testing AI Features
```bash
# Test all AI endpoints
curl http://localhost:8080/api/v1/ai/triage/demo
curl http://localhost:8080/api/v1/ai/optimize/demo
curl http://localhost:8080/api/v1/ai/scan/demo
curl http://localhost:8080/api/v1/ai/chat/demo

# Interactive ChatOps testing
curl -X POST http://localhost:8080/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "project_id": 278964, "message": "help"}'
```

## High-Level Architecture

### Core Application Structure
- **FastAPI Application** (`src/main.py`): Main application with lifespan management, middleware, and route registration
- **Event-Driven Architecture** (`src/core/events.py`): Async event queue with 5 workers, priority-based processing, and retry logic
- **Configuration System** (`src/core/config.py`): Pydantic-based settings with environment variable support
- **Structured Logging** (`src/core/logging.py`): JSON logging with request tracking and performance metrics

### AI-Powered Features
The platform implements four main AI features that work together:

1. **MR Triage System** (`src/features/mr_triage.py`): 
   - Risk assessment with security pattern detection
   - Complexity analysis and review time estimation
   - Automatic labeling and reviewer suggestions

2. **Pipeline Optimizer** (`src/features/pipeline_optimizer.py`):
   - Performance analysis with bottleneck detection
   - ML-based optimization recommendations
   - Cost and efficiency improvements

3. **Vulnerability Scanner** (`src/features/vulnerability_scanner.py`):
   - Multi-language dependency parsing
   - OSV database integration for vulnerability detection
   - CycloneDX SBOM generation

4. **ChatOps Bot** (`src/features/chatops_bot.py`):
   - Natural language command processing
   - Integration with all other AI features
   - Intelligent error diagnosis and fix suggestions

### GitLab Integration Layer
- **GitLab API Client** (`src/integrations/gitlab_client.py`): Async client with rate limiting, caching, and circuit breaker patterns
- **Webhook Processing** (`src/api/webhooks.py`): Secure webhook receiver with signature validation and event routing
- **Event Processors**: Automatic MR analysis and pipeline optimization triggered by GitLab events

### API Design
All AI features are exposed through REST endpoints in `src/api/ai_insights.py`:
- `/api/v1/ai/triage/*` - MR triage endpoints
- `/api/v1/ai/optimize/*` - Pipeline optimization endpoints  
- `/api/v1/ai/scan/*` - Vulnerability scanning endpoints
- `/api/v1/ai/chat/*` - ChatOps bot endpoints

Each feature provides:
- Demo endpoints for testing without authentication
- Stats endpoints for monitoring
- Production endpoints for real GitLab integration

### Configuration Requirements
Essential environment variables (see `.env.example`):
- `GITLAB_TOKEN` - Required for GitLab API access
- `GITLAB_WEBHOOK_SECRET` - Required for webhook signature validation
- `PYTHONPATH` - Must include project root for imports

### Caching Strategy
- **Analysis Results**: 1-2 hour TTL for expensive AI operations
- **GitLab API**: Rate limiting with exponential backoff
- **Conversation History**: 1 hour TTL for ChatOps interactions

### Error Handling Patterns
- **Graceful Degradation**: AI features fail safely without breaking webhook processing
- **Retry Logic**: Exponential backoff for external API calls
- **Circuit Breakers**: Prevent cascade failures in GitLab integration
- **Comprehensive Logging**: Structured logs with request correlation IDs

### Testing Philosophy
- `test.py` - Basic platform health check
- `scripts/test_chatops.py` - Comprehensive ChatOps functionality testing
- Demo endpoints - Test AI features without external dependencies
- Real GitLab integration uses public projects (GitLab CE project ID: 278964)

### Performance Characteristics
- Event processing: ~50-100ms average
- MR triage analysis: ~800ms for full assessment
- Pipeline optimization: ~1-2s with recommendations
- Vulnerability scanning: ~2-5s with SBOM generation
- ChatOps responses: ~300-500ms for intelligent analysis

The platform is production-ready with all four core AI features implemented and tested.