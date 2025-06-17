"""
Service Registry for GitAIOps Platform

Manages service dependencies, health checks, and graceful degradation.
"""
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)

class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceInfo:
    """Service information"""
    name: str
    instance: Any
    health_check: Optional[Callable] = None
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: Optional[datetime] = None
    error_count: int = 0
    dependencies: List[str] = None

class ServiceRegistry:
    """Central service registry with health monitoring"""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.health_check_interval = 30  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Circuit breaker settings
        self.max_errors = 5
        self.error_window = timedelta(minutes=5)
    
    async def register_service(
        self, 
        name: str, 
        instance: Any, 
        health_check: Optional[Callable] = None,
        dependencies: List[str] = None
    ):
        """Register a service with optional health check"""
        self.services[name] = ServiceInfo(
            name=name,
            instance=instance,
            health_check=health_check,
            dependencies=dependencies or []
        )
        
        logger.info(
            "Service registered",
            service=name,
            has_health_check=health_check is not None,
            dependencies=dependencies
        )
    
    async def get_service(self, name: str) -> Optional[Any]:
        """Get service instance if healthy"""
        service_info = self.services.get(name)
        if not service_info:
            return None
        
        # Check if service is healthy
        if service_info.status == ServiceStatus.UNHEALTHY:
            logger.warning("Service unavailable", service=name, status=service_info.status.value)
            return None
        
        return service_info.instance
    
    async def get_service_status(self, name: str) -> ServiceStatus:
        """Get current service status"""
        service_info = self.services.get(name)
        if not service_info:
            return ServiceStatus.UNKNOWN
        return service_info.status
    
    async def is_service_healthy(self, name: str) -> bool:
        """Check if service is healthy"""
        status = await self.get_service_status(name)
        return status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
    
    async def start_health_monitoring(self):
        """Start background health monitoring"""
        if self._running:
            return
        
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_monitor_loop())
        logger.info("Health monitoring started")
    
    async def stop_health_monitoring(self):
        """Stop background health monitoring"""
        if not self._running:
            return
        
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health monitoring stopped")
    
    async def _health_monitor_loop(self):
        """Background health monitoring loop"""
        while self._running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health monitor error", error=str(e))
                await asyncio.sleep(5)  # Brief pause on error
    
    async def _check_all_services(self):
        """Check health of all registered services"""
        for service_name, service_info in self.services.items():
            try:
                await self._check_service_health(service_info)
            except Exception as e:
                logger.error(
                    "Health check failed",
                    service=service_name,
                    error=str(e)
                )
                service_info.status = ServiceStatus.UNHEALTHY
                service_info.error_count += 1
    
    async def _check_service_health(self, service_info: ServiceInfo):
        """Check health of a single service"""
        if not service_info.health_check:
            # No health check defined, assume healthy if instance exists
            service_info.status = ServiceStatus.HEALTHY if service_info.instance else ServiceStatus.UNHEALTHY
            service_info.last_check = datetime.utcnow()
            return
        
        try:
            # Run health check
            is_healthy = await service_info.health_check()
            
            if is_healthy:
                service_info.status = ServiceStatus.HEALTHY
                service_info.error_count = 0
            else:
                service_info.status = ServiceStatus.DEGRADED
                service_info.error_count += 1
            
            service_info.last_check = datetime.utcnow()
            
        except Exception as e:
            logger.warning(
                "Service health check failed",
                service=service_info.name,
                error=str(e)
            )
            service_info.status = ServiceStatus.UNHEALTHY
            service_info.error_count += 1
            service_info.last_check = datetime.utcnow()
        
        # Circuit breaker logic
        if service_info.error_count >= self.max_errors:
            service_info.status = ServiceStatus.UNHEALTHY
            logger.error(
                "Service marked unhealthy due to repeated failures",
                service=service_info.name,
                error_count=service_info.error_count
            )
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        service_statuses = {}
        healthy_count = 0
        total_count = len(self.services)
        
        for name, service_info in self.services.items():
            status_info = {
                "status": service_info.status.value,
                "last_check": service_info.last_check.isoformat() if service_info.last_check else None,
                "error_count": service_info.error_count,
                "dependencies": service_info.dependencies
            }
            service_statuses[name] = status_info
            
            if service_info.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]:
                healthy_count += 1
        
        # Determine overall system status
        if healthy_count == total_count:
            overall_status = "healthy"
        elif healthy_count > total_count * 0.5:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": service_statuses,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_service_dependencies(self, service_name: str) -> List[str]:
        """Get dependencies for a service"""
        service_info = self.services.get(service_name)
        if not service_info:
            return []
        return service_info.dependencies or []
    
    async def check_dependencies_healthy(self, service_name: str) -> bool:
        """Check if all dependencies of a service are healthy"""
        dependencies = await self.get_service_dependencies(service_name)
        
        for dep in dependencies:
            if not await self.is_service_healthy(dep):
                return False
        
        return True

# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None

def get_service_registry() -> ServiceRegistry:
    """Get or create global service registry"""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry

async def initialize_services():
    """Initialize all services and start health monitoring"""
    registry = get_service_registry()
    
    # Import and register services
    try:
        from src.integrations.gitlab_client import get_gitlab_client
        gitlab_client = get_gitlab_client()
        await registry.register_service(
            "gitlab_client",
            gitlab_client,
            health_check=gitlab_client.health_check
        )
    except Exception as e:
        logger.error("Failed to register GitLab client", error=str(e))
    
    try:
        from src.integrations.neo4j_client import get_neo4j_client
        neo4j_client = await get_neo4j_client()
        await registry.register_service(
            "neo4j_client",
            neo4j_client,
            health_check=lambda: neo4j_client._initialized
        )
    except Exception as e:
        logger.warning("Neo4j client not available", error=str(e))
    
    try:
        from src.integrations.gemini_client import get_gemini_client
        gemini_client = get_gemini_client()
        await registry.register_service(
            "gemini_client",
            gemini_client,
            health_check=gemini_client.is_available
        )
    except Exception as e:
        logger.warning("Gemini client not available", error=str(e))
    
    try:
        from src.integrations.openrouter_client import get_openrouter_client
        openrouter_client = get_openrouter_client()
        await registry.register_service(
            "openrouter_client",
            openrouter_client,
            health_check=openrouter_client.is_available
        )
    except Exception as e:
        logger.warning("OpenRouter client not available", error=str(e))
    
    # Register feature services with dependencies
    try:
        from src.features.mr_triage import get_mr_triage_system
        mr_triage = get_mr_triage_system()
        await registry.register_service(
            "mr_triage",
            mr_triage,
            dependencies=["gitlab_client"]
        )
    except Exception as e:
        logger.error("Failed to register MR triage", error=str(e))
    
    try:
        from src.features.codecompass_expert_finder import get_expert_finder
        expert_finder = await get_expert_finder()
        await registry.register_service(
            "expert_finder",
            expert_finder,
            dependencies=["gitlab_client", "neo4j_client"]
        )
    except Exception as e:
        logger.warning("Expert finder not available", error=str(e))
    
    # Start health monitoring
    await registry.start_health_monitoring()
    
    logger.info("Service registry initialized", service_count=len(registry.services))

async def shutdown_services():
    """Shutdown all services and stop health monitoring"""
    registry = get_service_registry()
    await registry.stop_health_monitoring()
    
    # Close service connections
    for service_name, service_info in registry.services.items():
        try:
            if hasattr(service_info.instance, 'close'):
                await service_info.instance.close()
        except Exception as e:
            logger.error(f"Error closing {service_name}", error=str(e))
    
    logger.info("All services shutdown") 