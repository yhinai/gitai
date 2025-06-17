"""
Main FastAPI application for GitAIOps platform
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import structlog
import time
import os
from pathlib import Path

from src.core.config import get_settings
from src.core.service_registry import ServiceRegistry
from src.api import gitlab, health, ai_insights, metrics, expert_finder, webhooks

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="GitAIOps Platform",
    description="AI-powered DevOps platform for GitLab integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=round(process_time, 4)
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=round(process_time, 4)
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(gitlab.router, prefix="/api/v1/gitlab", tags=["GitLab"])
app.include_router(ai_insights.router, prefix="/api/v1/ai", tags=["AI Insights"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(expert_finder.router, prefix="/api/v1/experts", tags=["Expert Finder"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

# Serve React dashboard static files
dashboard_path = Path(__file__).parent.parent.parent / "dashboard" / "build"
if dashboard_path.exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_path / "static")), name="static")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "GitAIOps Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "dashboard": "/dashboard"
    }

@app.get("/dashboard")
async def dashboard():
    """Serve the React dashboard"""
    dashboard_file = dashboard_path / "index.html"
    if dashboard_file.exists():
        return FileResponse(str(dashboard_file))
    else:
        raise HTTPException(
            status_code=404, 
            detail="Dashboard not built. Run 'cd dashboard && npm run build' to build the frontend."
        )

# Catch-all route for React Router (SPA)
@app.get("/dashboard/{path:path}")
async def dashboard_spa(path: str):
    """Serve React app for all dashboard routes (SPA support)"""
    dashboard_file = dashboard_path / "index.html"
    if dashboard_file.exists():
        return FileResponse(str(dashboard_file))
    else:
        raise HTTPException(
            status_code=404, 
            detail="Dashboard not built. Run 'cd dashboard && npm run build' to build the frontend."
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("GitAIOps Platform starting up", version="1.0.0")
    
    # Initialize service registry and all services
    try:
        from src.core.service_registry import initialize_services
        from src.core.events import start_event_processing
        
        await initialize_services()
        await start_event_processing()
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("GitAIOps Platform shutting down")
    
    try:
        from src.core.service_registry import shutdown_services
        from src.core.events import stop_event_processing
        
        await stop_event_processing()
        await shutdown_services()
        
        logger.info("All services shutdown successfully")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 