"""
Event processing system with async queuing and workers
"""
import asyncio
import json
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import structlog
from cachetools import TTLCache
import uuid

logger = structlog.get_logger(__name__)

class EventType(Enum):
    """Event types"""
    MERGE_REQUEST = "merge_request"
    PIPELINE = "pipeline"
    PUSH = "push"
    ISSUE = "issue"
    DEPLOYMENT = "deployment"
    BUILD_FAILURE = "build_failure"
    VULNERABILITY_DETECTED = "vulnerability_detected"

class EventPriority(Enum):
    """Event priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Event:
    """Event data structure"""
    id: str
    event_type: EventType
    priority: EventPriority
    project_id: int
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    max_retries: int = 3
    processed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class EventProcessor:
    """Base class for event processors"""
    
    def __init__(self, event_type: EventType):
        self.event_type = event_type
        self.processed_count = 0
        self.failed_count = 0
    
    async def process(self, event: Event) -> bool:
        """Process an event. Return True if successful, False if failed."""
        raise NotImplementedError("Subclasses must implement process method")
    
    async def can_process(self, event: Event) -> bool:
        """Check if this processor can handle the event"""
        return event.event_type == self.event_type

class MergeRequestProcessor(EventProcessor):
    """Process merge request events"""
    
    def __init__(self):
        super().__init__(EventType.MERGE_REQUEST)
        # Import here to avoid circular imports
        from src.features.mr_triage import get_mr_triage_system
        self.triage_system = get_mr_triage_system()
    
    async def process(self, event: Event) -> bool:
        """Process merge request event"""
        try:
            mr_data = event.data.get("object_attributes", {})
            action = mr_data.get("action", "unknown")
            mr_iid = mr_data.get("iid")
            
            logger.info(
                "Processing MR event",
                event_id=event.id,
                action=action,
                mr_id=mr_data.get("id"),
                mr_iid=mr_iid,
                title=mr_data.get("title", "")[:50]
            )
            
            # Only analyze opened/reopened MRs to avoid duplicate analysis
            if action in ["opened", "reopened"] and mr_iid:
                try:
                    analysis = await self.triage_system.analyze_merge_request(
                        project_id=event.project_id,
                        mr_iid=mr_iid
                    )
                    
                    logger.info(
                        "MR triage analysis completed",
                        event_id=event.id,
                        mr_iid=mr_iid,
                        risk_level=analysis.risk_level.value,
                        mr_type=analysis.mr_type.value,
                        estimated_hours=analysis.estimated_review_hours
                    )
                    
                    # TODO: Apply labels and create review assignments automatically
                    # await self._apply_analysis_results(event.project_id, mr_iid, analysis)
                    
                except Exception as e:
                    logger.warning(
                        "MR triage analysis failed",
                        event_id=event.id,
                        mr_iid=mr_iid,
                        error=str(e)
                    )
                    # Don't fail the entire event processing if triage fails
            
            self.processed_count += 1
            return True
            
        except Exception as e:
            logger.error(
                "Failed to process MR event",
                event_id=event.id,
                error=str(e),
                exc_info=True
            )
            self.failed_count += 1
            return False

class PipelineProcessor(EventProcessor):
    """Process pipeline events"""
    
    def __init__(self):
        super().__init__(EventType.PIPELINE)
        # Import here to avoid circular imports
        from src.features.pipeline_optimizer import get_pipeline_optimizer
        self.optimizer = get_pipeline_optimizer()
    
    async def process(self, event: Event) -> bool:
        """Process pipeline event"""
        try:
            pipeline_data = event.data.get("object_attributes", {})
            status = pipeline_data.get("status")
            pipeline_id = pipeline_data.get("id")
            
            logger.info(
                "Processing pipeline event",
                event_id=event.id,
                status=status,
                pipeline_id=pipeline_id
            )
            
            # Analyze pipeline if it's completed (success or failed)
            if status in ["success", "failed"] and pipeline_id:
                try:
                    analysis = await self.optimizer.analyze_pipeline_performance(
                        project_id=event.project_id,
                        pipeline_id=pipeline_id
                    )
                    
                    logger.info(
                        "Pipeline optimization analysis completed",
                        event_id=event.id,
                        pipeline_id=pipeline_id,
                        optimization_score=analysis.overall_score,
                        recommendations_count=len(analysis.recommendations)
                    )
                    
                    # TODO: Automatically apply low-risk optimizations
                    # TODO: Create optimization MRs for high-impact recommendations
                    
                except Exception as e:
                    logger.warning(
                        "Pipeline optimization analysis failed",
                        event_id=event.id,
                        pipeline_id=pipeline_id,
                        error=str(e)
                    )
                    # Don't fail the entire event processing if optimization fails
            
            self.processed_count += 1
            return True
            
        except Exception as e:
            logger.error(
                "Failed to process pipeline event",
                event_id=event.id,
                error=str(e),
                exc_info=True
            )
            self.failed_count += 1
            return False

class EventQueue:
    """Priority-based event queue with async processing"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.queues = {
            EventPriority.CRITICAL: asyncio.Queue(),
            EventPriority.HIGH: asyncio.Queue(),
            EventPriority.MEDIUM: asyncio.Queue(),
            EventPriority.LOW: asyncio.Queue(),
        }
        self.processors: List[EventProcessor] = []
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.stats = {
            "total_processed": 0,
            "total_failed": 0,
            "events_by_type": {},
            "avg_processing_time": 0.0
        }
        
        # Event history for debugging
        self.event_history = TTLCache(maxsize=1000, ttl=3600)  # 1 hour
    
    def add_processor(self, processor: EventProcessor):
        """Add an event processor"""
        self.processors.append(processor)
        logger.info(
            "Added event processor",
            processor_type=processor.event_type.value,
            total_processors=len(self.processors)
        )
    
    async def enqueue(self, event: Event):
        """Add event to appropriate priority queue"""
        queue = self.queues[event.priority]
        await queue.put(event)
        
        # Update stats
        self.stats["events_by_type"][event.event_type.value] = \
            self.stats["events_by_type"].get(event.event_type.value, 0) + 1
        
        # Store in history
        self.event_history[event.id] = {
            "event": event,
            "queued_at": datetime.utcnow()
        }
        
        logger.info(
            "Event queued",
            event_id=event.id,
            event_type=event.event_type.value,
            priority=event.priority.value,
            queue_size=queue.qsize()
        )
    
    async def start_workers(self):
        """Start worker tasks"""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting event processing workers", worker_count=self.max_workers)
        
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def stop_workers(self):
        """Stop worker tasks"""
        if not self.running:
            return
        
        logger.info("Stopping event processing workers")
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
    
    async def _worker(self, worker_name: str):
        """Worker task that processes events"""
        logger.info("Event worker started", worker_name=worker_name)
        
        try:
            while self.running:
                event = await self._get_next_event()
                if event is None:
                    await asyncio.sleep(0.1)
                    continue
                
                start_time = datetime.utcnow()
                success = await self._process_event(event)
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Update event history
                if event.id in self.event_history:
                    self.event_history[event.id]["processed_at"] = datetime.utcnow()
                    self.event_history[event.id]["success"] = success
                    self.event_history[event.id]["processing_time"] = processing_time
                
                # Update stats
                if success:
                    self.stats["total_processed"] += 1
                    event.processed_at = datetime.utcnow()
                else:
                    self.stats["total_failed"] += 1
                    event.failed_at = datetime.utcnow()
                    
                    # Retry if not exceeded max retries
                    if event.retry_count < event.max_retries:
                        event.retry_count += 1
                        logger.info(
                            "Retrying event",
                            event_id=event.id,
                            retry_count=event.retry_count,
                            max_retries=event.max_retries
                        )
                        await asyncio.sleep(2 ** event.retry_count)  # Exponential backoff
                        await self.enqueue(event)
                
                # Update average processing time
                total_events = self.stats["total_processed"] + self.stats["total_failed"]
                if total_events > 0:
                    self.stats["avg_processing_time"] = \
                        (self.stats["avg_processing_time"] * (total_events - 1) + processing_time) / total_events
                        
        except asyncio.CancelledError:
            logger.info("Event worker cancelled", worker_name=worker_name)
        except Exception as e:
            logger.error(
                "Event worker error",
                worker_name=worker_name,
                error=str(e),
                exc_info=True
            )
    
    async def _get_next_event(self) -> Optional[Event]:
        """Get next event from highest priority queue"""
        # Check queues in priority order
        for priority in [EventPriority.CRITICAL, EventPriority.HIGH, 
                        EventPriority.MEDIUM, EventPriority.LOW]:
            queue = self.queues[priority]
            if not queue.empty():
                try:
                    return await asyncio.wait_for(queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
        return None
    
    async def _process_event(self, event: Event) -> bool:
        """Process event with appropriate processor"""
        for processor in self.processors:
            if await processor.can_process(event):
                try:
                    return await processor.process(event)
                except Exception as e:
                    logger.error(
                        "Processor error",
                        event_id=event.id,
                        processor_type=processor.event_type.value,
                        error=str(e),
                        exc_info=True
                    )
                    event.error_message = str(e)
                    return False
        
        logger.warning(
            "No processor found for event",
            event_id=event.id,
            event_type=event.event_type.value
        )
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        queue_sizes = {
            priority.name: queue.qsize() 
            for priority, queue in self.queues.items()
        }
        
        processor_stats = {
            processor.event_type.value: {
                "processed": processor.processed_count,
                "failed": processor.failed_count
            }
            for processor in self.processors
        }
        
        return {
            "queue_sizes": queue_sizes,
            "total_queue_size": sum(queue_sizes.values()),
            "worker_count": len(self.workers),
            "running": self.running,
            "stats": self.stats,
            "processor_stats": processor_stats
        }
    
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent events from history"""
        events = []
        for event_id, event_data in list(self.event_history.items())[-limit:]:
            event = event_data["event"]
            events.append({
                "id": event.id,
                "type": event.event_type.value,
                "priority": event.priority.value,
                "project_id": event.project_id,
                "created_at": event.created_at.isoformat(),
                "processed_at": event_data.get("processed_at", "").isoformat() if event_data.get("processed_at") else None,
                "success": event_data.get("success"),
                "processing_time": event_data.get("processing_time"),
                "retry_count": event.retry_count
            })
        return events

# Global event queue instance
_event_queue: Optional[EventQueue] = None

def get_event_queue() -> EventQueue:
    """Get or create global event queue"""
    global _event_queue
    if _event_queue is None:
        _event_queue = EventQueue()
        
        # Add default processors
        _event_queue.add_processor(MergeRequestProcessor())
        _event_queue.add_processor(PipelineProcessor())
        
    return _event_queue

async def start_event_processing():
    """Start the event processing system"""
    queue = get_event_queue()
    await queue.start_workers()

async def stop_event_processing():
    """Stop the event processing system"""
    queue = get_event_queue()
    await queue.stop_workers()