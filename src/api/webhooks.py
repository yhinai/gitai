"""
GitLab webhook endpoints for event processing
"""
import hashlib
import hmac
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog

from src.core.config import get_settings
from src.core.events import get_event_queue, Event, EventType, EventPriority

logger = structlog.get_logger(__name__)
router = APIRouter()

# Webhook event models
class WebhookEvent(BaseModel):
    """Base webhook event model"""
    id: str
    event_type: str
    project_id: int
    created_at: datetime
    data: Dict[str, Any]

class MergeRequestEvent(BaseModel):
    """Merge request event model"""
    action: str  # opened, updated, merged, closed
    merge_request: Dict[str, Any]
    project: Dict[str, Any]
    user: Dict[str, Any]

class PipelineEvent(BaseModel):
    """Pipeline event model"""
    object_kind: str
    object_attributes: Dict[str, Any]
    project: Dict[str, Any]
    user: Dict[str, Any]

class PushEvent(BaseModel):
    """Push event model"""
    project: Dict[str, Any]
    commits: list
    total_commits_count: int
    repository: Dict[str, Any]

# Event processing now handled by the event queue system

def verify_gitlab_signature(request: Request, secret: str) -> bool:
    """Verify GitLab webhook signature"""
    gitlab_token = request.headers.get("X-Gitlab-Token")
    if not gitlab_token:
        return False
    
    # GitLab uses simple token verification
    return hmac.compare_digest(secret, gitlab_token)

async def get_request_body(request: Request) -> Dict[str, Any]:
    """Get and parse request body"""
    try:
        body = await request.body()
        return json.loads(body.decode('utf-8'))
    except Exception as e:
        logger.error("Failed to parse request body", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON body")

def determine_event_type(data: Dict[str, Any]) -> str:
    """Determine event type from webhook data"""
    if "object_kind" in data:
        return data["object_kind"]
    elif "event_type" in data:
        return data["event_type"]
    else:
        # Try to infer from structure
        if "merge_request" in data:
            return "merge_request"
        elif "pipeline" in data:
            return "pipeline"
        elif "commits" in data:
            return "push"
        else:
            return "unknown"

def determine_event_priority(data: Dict[str, Any], event_type: EventType) -> EventPriority:
    """Determine event priority based on content"""
    if event_type == EventType.PIPELINE:
        status = data.get("object_attributes", {}).get("status")
        if status == "failed":
            return EventPriority.HIGH
        elif status in ["running", "pending"]:
            return EventPriority.MEDIUM
        else:
            return EventPriority.LOW
    
    elif event_type == EventType.MERGE_REQUEST:
        action = data.get("object_attributes", {}).get("action")
        if action in ["opened", "reopened"]:
            return EventPriority.MEDIUM
        elif action == "merged":
            return EventPriority.HIGH
        else:
            return EventPriority.LOW
    
    elif event_type == EventType.PUSH:
        # Check if push contains security-related changes
        commits = data.get("commits", [])
        for commit in commits:
            message = commit.get("message", "").lower()
            if any(keyword in message for keyword in ["security", "vulnerability", "fix"]):
                return EventPriority.HIGH
        return EventPriority.LOW
    
    return EventPriority.LOW

async def process_webhook_event(webhook_event: WebhookEvent):
    """Process webhook event by adding to event queue"""
    # Determine event type
    try:
        if webhook_event.event_type == "merge_request":
            event_type = EventType.MERGE_REQUEST
        elif webhook_event.event_type == "pipeline":
            event_type = EventType.PIPELINE
        elif webhook_event.event_type == "push":
            event_type = EventType.PUSH
        else:
            logger.warning("Unknown event type", event_type=webhook_event.event_type)
            return
        
        # Determine priority based on content
        priority = determine_event_priority(webhook_event.data, event_type)
        
        # Create event for processing queue
        event = Event(
            id=webhook_event.id,
            event_type=event_type,
            priority=priority,
            project_id=webhook_event.project_id,
            data=webhook_event.data
        )
        
        # Add to processing queue
        queue = get_event_queue()
        await queue.enqueue(event)
        
        logger.info(
            "Event queued for processing",
            event_id=event.id,
            event_type=event_type.value,
            priority=priority.value,
            project_id=event.project_id
        )
        
    except Exception as e:
        logger.error(
            "Failed to queue webhook event",
            event_type=webhook_event.event_type,
            project_id=webhook_event.project_id,
            event_id=webhook_event.id,
            error=str(e),
            exc_info=True
        )

# Old processing functions removed - now using event queue system

@router.post("/gitlab")
async def receive_gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    settings = Depends(get_settings)
):
    """Receive and process GitLab webhooks"""
    
    # Verify signature if secret is configured
    if settings.gitlab_webhook_secret:
        if not verify_gitlab_signature(request, settings.gitlab_webhook_secret):
            logger.warning(
                "Invalid webhook signature",
                client_ip=request.client.host if request.client else None
            )
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse request body
    data = await get_request_body(request)
    
    # Determine event type
    event_type = determine_event_type(data)
    
    # Create event
    event = WebhookEvent(
        id=f"{event_type}_{str(uuid.uuid4())[:8]}",
        event_type=event_type,
        project_id=data.get("project", {}).get("id", 0),
        created_at=datetime.utcnow(),
        data=data
    )
    
    # Process in background
    background_tasks.add_task(process_webhook_event, event)
    
    logger.info(
        "Webhook received",
        event_type=event_type,
        project_id=event.project_id,
        event_id=event.id
    )
    
    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "event_id": event.id,
            "event_type": event_type
        }
    )

@router.get("/events")
async def list_recent_events():
    """List recent webhook events"""
    queue = get_event_queue()
    return {
        "events": queue.get_recent_events(limit=10),
        "stats": queue.get_stats()
    }

@router.get("/queue/stats")
async def get_queue_stats():
    """Get event queue statistics"""
    queue = get_event_queue()
    return queue.get_stats()

@router.get("/health")
async def webhook_health():
    """Webhook system health check"""
    queue = get_event_queue()
    stats = queue.get_stats()
    
    return {
        "status": "healthy" if stats["running"] else "stopped",
        "queue_size": stats["total_queue_size"],
        "workers": stats["worker_count"],
        "total_processed": stats["stats"]["total_processed"],
        "total_failed": stats["stats"]["total_failed"]
    }