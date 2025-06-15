"""
GitLab integration API endpoints
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import structlog

from src.integrations.gitlab_client import get_gitlab_client, GitLabAPIError
from src.core.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()

class ProjectInfo(BaseModel):
    """Project information response"""
    id: int
    name: str
    path: str
    description: Optional[str]
    web_url: str
    last_activity_at: Optional[str]

class MergeRequestInfo(BaseModel):
    """Merge request information response"""
    id: int
    iid: int
    title: str
    description: Optional[str]
    state: str
    web_url: str
    author: Dict[str, Any]
    target_branch: str
    source_branch: str
    created_at: str
    updated_at: str

class PipelineInfo(BaseModel):
    """Pipeline information response"""
    id: int
    status: str
    ref: str
    web_url: str
    created_at: str
    updated_at: str

@router.get("/health")
async def gitlab_health():
    """Check GitLab API connectivity"""
    client = get_gitlab_client()
    
    try:
        is_healthy = await client.health_check()
        if is_healthy:
            user = await client.get_user()
            return {
                "status": "healthy",
                "connected": True,
                "user": user.get("username") if user else None
            }
        else:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": "Cannot connect to GitLab API"
            }
    except GitLabAPIError as e:
        logger.error("GitLab health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }

@router.get("/projects/{project_id}", response_model=ProjectInfo)
async def get_project(project_id: int):
    """Get project information"""
    client = get_gitlab_client()
    
    try:
        project = await client.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectInfo(
            id=project["id"],
            name=project["name"],
            path=project["path"],
            description=project.get("description"),
            web_url=project["web_url"],
            last_activity_at=project.get("last_activity_at")
        )
    except GitLabAPIError as e:
        logger.error("Failed to get project", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/merge_requests")
async def list_merge_requests(
    project_id: int,
    state: str = Query("opened", description="MR state: opened, closed, merged"),
    per_page: int = Query(20, le=100, description="Number of results per page")
):
    """List merge requests for a project"""
    client = get_gitlab_client()
    
    try:
        mrs = await client.list_merge_requests(
            project_id=project_id,
            state=state,
            per_page=per_page
        )
        
        return {
            "merge_requests": [
                MergeRequestInfo(
                    id=mr["id"],
                    iid=mr["iid"],
                    title=mr["title"],
                    description=mr.get("description"),
                    state=mr["state"],
                    web_url=mr["web_url"],
                    author=mr["author"],
                    target_branch=mr["target_branch"],
                    source_branch=mr["source_branch"],
                    created_at=mr["created_at"],
                    updated_at=mr["updated_at"]
                )
                for mr in mrs
            ],
            "total": len(mrs)
        }
    except GitLabAPIError as e:
        logger.error(
            "Failed to list merge requests",
            project_id=project_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/merge_requests/{mr_iid}")
async def get_merge_request(project_id: int, mr_iid: int):
    """Get detailed merge request information"""
    client = get_gitlab_client()
    
    try:
        # Get MR details
        mr = await client.get_merge_request(project_id, mr_iid)
        if not mr:
            raise HTTPException(status_code=404, detail="Merge request not found")
        
        # Get changes/diff
        changes = await client.get_merge_request_changes(project_id, mr_iid)
        
        return {
            "merge_request": mr,
            "changes": changes.get("changes", []) if changes else [],
            "stats": {
                "additions": mr.get("changes_count", 0),
                "deletions": mr.get("changes_count", 0),
                "files_changed": len(changes.get("changes", [])) if changes else 0
            }
        }
    except GitLabAPIError as e:
        logger.error(
            "Failed to get merge request",
            project_id=project_id,
            mr_iid=mr_iid,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/merge_requests/{mr_iid}/notes")
async def create_mr_note(
    project_id: int,
    mr_iid: int,
    note_data: Dict[str, str]
):
    """Create a note/comment on a merge request"""
    client = get_gitlab_client()
    
    if "body" not in note_data:
        raise HTTPException(status_code=400, detail="Note body is required")
    
    try:
        note = await client.create_merge_request_note(
            project_id=project_id,
            mr_iid=mr_iid,
            body=note_data["body"]
        )
        
        return {
            "status": "created",
            "note": note
        }
    except GitLabAPIError as e:
        logger.error(
            "Failed to create MR note",
            project_id=project_id,
            mr_iid=mr_iid,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/pipelines")
async def list_pipelines(
    project_id: int,
    ref: Optional[str] = Query(None, description="Filter by git ref"),
    status: Optional[str] = Query(None, description="Filter by pipeline status"),
    per_page: int = Query(20, le=100, description="Number of results per page")
):
    """List pipelines for a project"""
    client = get_gitlab_client()
    
    try:
        pipelines = await client.list_project_pipelines(
            project_id=project_id,
            ref=ref,
            status=status,
            per_page=per_page
        )
        
        return {
            "pipelines": [
                PipelineInfo(
                    id=pipeline["id"],
                    status=pipeline["status"],
                    ref=pipeline["ref"],
                    web_url=pipeline["web_url"],
                    created_at=pipeline["created_at"],
                    updated_at=pipeline["updated_at"]
                )
                for pipeline in pipelines
            ],
            "total": len(pipelines)
        }
    except GitLabAPIError as e:
        logger.error(
            "Failed to list pipelines",
            project_id=project_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/pipelines/{pipeline_id}")
async def get_pipeline(project_id: int, pipeline_id: int):
    """Get detailed pipeline information"""
    client = get_gitlab_client()
    
    try:
        # Get pipeline details
        pipeline = await client.get_pipeline(project_id, pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        # Get pipeline jobs
        jobs = await client.get_pipeline_jobs(project_id, pipeline_id)
        
        return {
            "pipeline": pipeline,
            "jobs": jobs,
            "stats": {
                "total_jobs": len(jobs),
                "failed_jobs": len([j for j in jobs if j["status"] == "failed"]),
                "passed_jobs": len([j for j in jobs if j["status"] == "success"]),
                "duration": pipeline.get("duration")
            }
        }
    except GitLabAPIError as e:
        logger.error(
            "Failed to get pipeline",
            project_id=project_id,
            pipeline_id=pipeline_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/pipelines/{pipeline_id}/retry")
async def retry_pipeline(project_id: int, pipeline_id: int):
    """Retry a failed pipeline"""
    client = get_gitlab_client()
    
    try:
        result = await client.retry_pipeline(project_id, pipeline_id)
        return {
            "status": "retried",
            "pipeline": result
        }
    except GitLabAPIError as e:
        logger.error(
            "Failed to retry pipeline",
            project_id=project_id,
            pipeline_id=pipeline_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/jobs/{job_id}/log")
async def get_job_log(project_id: int, job_id: int):
    """Get job log/trace"""
    client = get_gitlab_client()
    
    try:
        log = await client.get_job_log(project_id, job_id)
        if log is None:
            raise HTTPException(status_code=404, detail="Job log not found")
        
        return {
            "log": log,
            "lines": len(log.split('\n')) if log else 0
        }
    except GitLabAPIError as e:
        logger.error(
            "Failed to get job log",
            project_id=project_id,
            job_id=job_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/projects")
async def search_projects(
    q: str = Query(..., description="Search query"),
    per_page: int = Query(20, le=100, description="Number of results per page")
):
    """Search for projects"""
    client = get_gitlab_client()
    
    try:
        projects = await client.search_projects(search=q, per_page=per_page)
        
        return {
            "projects": [
                ProjectInfo(
                    id=project["id"],
                    name=project["name"],
                    path=project["path"],
                    description=project.get("description"),
                    web_url=project["web_url"],
                    last_activity_at=project.get("last_activity_at")
                )
                for project in projects
            ],
            "total": len(projects),
            "query": q
        }
    except GitLabAPIError as e:
        logger.error("Failed to search projects", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))