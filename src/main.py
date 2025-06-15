"""
Main FastAPI application for GitAIOps platform
"""
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import time
from typing import Dict, Any
from pathlib import Path
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY, CollectorRegistry
from fastapi.responses import PlainTextResponse

from src.core.config import get_settings, get_environment_config
from src.core.logging import setup_logging, get_logger
from src.core.events import start_event_processing, stop_event_processing
from src.api import health, webhooks, gitlab, ai_insights, expert_finder
from src.api import metrics as metrics_api


# Metrics - Initialize with fallback handling
REQUEST_COUNT = None
REQUEST_LATENCY = None

def get_or_create_counter():
    global REQUEST_COUNT
    if REQUEST_COUNT is None:
        try:
            REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
        except ValueError:
            # Metric already exists, find it
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, '_name') and collector._name == 'http_requests_total':
                    REQUEST_COUNT = collector
                    break
    return REQUEST_COUNT

def get_or_create_histogram():
    global REQUEST_LATENCY
    if REQUEST_LATENCY is None:
        try:
            REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
        except ValueError:
            # Metric already exists, find it
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, '_name') and collector._name == 'http_request_duration_seconds':
                    REQUEST_LATENCY = collector
                    break
    return REQUEST_LATENCY

# Logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting GitAIOps platform", version=settings.app_version)
    setup_logging()
    
    # Start event processing system
    await start_event_processing()
    logger.info("Event processing system started")
    
    # Initialize services here
    # await initialize_database()
    # await initialize_ai_models()
    
    yield
    
    # Shutdown
    logger.info("Shutting down GitAIOps platform")
    await stop_event_processing()
    logger.info("Event processing system stopped")
    # await cleanup_resources()


# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered DevOps Automation Platform",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://gitlab.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time header and collect metrics"""
    start_time = time.time()
    
    # Log request
    logger.info(
        "request_received",
        method=request.method,
        url=str(request.url),
        client=request.client.host if request.client else None
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Version"] = settings.app_version
        
        # Collect metrics
        counter = get_or_create_counter()
        histogram = get_or_create_histogram()
        if counter:
            counter.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
        if histogram:
            histogram.observe(process_time)
        
        # Log response
        logger.info(
            "request_completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time
        )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "request_failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=process_time,
            exc_info=True
        )
        
        counter = get_or_create_counter()
        if counter:
            counter.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error"}
        )


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.error("Value error", error=str(exc), url=str(request.url))
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), url=str(request.url), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"}
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "operational"
    }


# Metrics endpoint
@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest())


# Include routers
app.include_router(
    health.router,
    prefix=f"{settings.api_prefix}/health",
    tags=["health"]
)

app.include_router(
    webhooks.router,
    prefix=f"{settings.api_prefix}/webhooks",
    tags=["webhooks"]
)

app.include_router(
    gitlab.router,
    prefix=f"{settings.api_prefix}/gitlab",
    tags=["gitlab"]
)

app.include_router(
    ai_insights.router,
    prefix=f"{settings.api_prefix}/ai",
    tags=["ai"]
)

app.include_router(
    expert_finder.router,
    prefix=f"{settings.api_prefix}/codecompass",
    tags=["codecompass", "experts"]
)

app.include_router(
    metrics_api.router,
    prefix=f"{settings.api_prefix}/metrics",
    tags=["metrics", "monitoring"]
)

# Mount the React dashboard
dashboard_path = Path(__file__).parent.parent / "dashboard" / "build"
if dashboard_path.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_path), html=True), name="dashboard")
    logger.info("Dashboard mounted at /dashboard")
    
    # Add a redirect from root to dashboard for convenience
    @app.get("/app")
    async def redirect_to_dashboard():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/dashboard/")
else:
    logger.warning("Dashboard build directory not found")

# Serve the test HTML file
@app.get("/test_live_demo.html")
async def serve_test_demo():
    """Serve the live demo test page"""
    from fastapi.responses import FileResponse
    test_file_path = Path(__file__).parent.parent / "test_live_demo.html"
    if test_file_path.exists():
        return FileResponse(test_file_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Test demo file not found")


if __name__ == "__main__":
    import uvicorn
    
    env_config = get_environment_config(settings.environment)
    
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=env_config.get("reload", False),
        log_level=settings.log_level.lower()
    )
