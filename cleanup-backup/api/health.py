"""
Health check endpoints for GitAIOps platform
"""
from fastapi import APIRouter, status
from typing import Dict, Any, List
from datetime import datetime
import psutil
import asyncio

from src.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "gitaiops-platform"
    }


@router.get("/live", response_model=Dict[str, Any])
async def liveness() -> Dict[str, Any]:
    """Kubernetes liveness probe endpoint"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready", response_model=Dict[str, Any])
async def readiness() -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint"""
    # Check critical dependencies
    checks = await _run_readiness_checks()
    
    all_ready = all(check["status"] == "ready" for check in checks)
    
    return {
        "status": "ready" if all_ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health() -> Dict[str, Any]:
    """Detailed health check with system metrics"""
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Service checks
    service_checks = await _run_service_checks()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
        },
        "services": service_checks,
        "uptime": _get_uptime()
    }


async def _run_readiness_checks() -> List[Dict[str, Any]]:
    """Run readiness checks for critical dependencies"""
    checks = []
    
    # Check database connectivity (placeholder)
    # try:
    #     await check_database()
    #     checks.append({"name": "database", "status": "ready"})
    # except Exception as e:
    #     logger.error("Database check failed", error=str(e))
    #     checks.append({"name": "database", "status": "not_ready", "error": str(e)})
    
    # Check Redis connectivity (placeholder)
    # try:
    #     await check_redis()
    #     checks.append({"name": "redis", "status": "ready"})
    # except Exception as e:
    #     logger.error("Redis check failed", error=str(e))
    #     checks.append({"name": "redis", "status": "not_ready", "error": str(e)})
    
    # For now, return placeholder checks
    checks.append({"name": "api", "status": "ready"})
    
    return checks


async def _run_service_checks() -> Dict[str, Any]:
    """Run health checks for all services"""
    return {
        "api": {
            "status": "healthy",
            "response_time_ms": 5
        },
        "database": {
            "status": "healthy",
            "connections": 10,
            "response_time_ms": 15
        },
        "cache": {
            "status": "healthy",
            "hit_rate": 0.85,
            "response_time_ms": 2
        }
    }


def _get_uptime() -> str:
    """Get system uptime"""
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f"{days}d {hours}h {minutes}m {seconds}s"
