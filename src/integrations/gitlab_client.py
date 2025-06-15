"""
GitLab API client for interacting with GitLab projects, MRs, and pipelines
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
from cachetools import TTLCache

from src.core.config import get_settings

logger = structlog.get_logger(__name__)

class GitLabAPIError(Exception):
    """GitLab API error"""
    pass

class GitLabClient:
    """Async GitLab API client"""
    
    def __init__(self, base_url: str = None, token: str = None):
        settings = get_settings()
        self.base_url = base_url or settings.gitlab_url
        self.token = token or settings.gitlab_token
        self.api_base = f"{self.base_url}/api/v4"
        
        # Cache for frequently accessed data
        self.cache = TTLCache(maxsize=1000, ttl=300)  # 5 min cache
        
        # Rate limiting
        self.rate_limit_remaining = 2000
        self.rate_limit_reset = datetime.utcnow()
        
        # Session will be created when needed
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.token}" if self.token else None,
                "User-Agent": "GitAIOps-Platform/1.0.0"
            }
            headers = {k: v for k, v in headers.items() if v is not None}
            
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self._session
    
    async def close(self):
        """Close the client session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to GitLab API with retry logic"""
        
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        session = await self._get_session()
        
        logger.debug(
            "Making GitLab API request",
            method=method,
            url=url,
            **{k: v for k, v in kwargs.items() if k != 'json'}
        )
        
        try:
            async with session.request(method, url, **kwargs) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(
                    response.headers.get("RateLimit-Remaining", 2000)
                )
                reset_time = response.headers.get("RateLimit-ResetTime")
                if reset_time:
                    self.rate_limit_reset = datetime.fromtimestamp(int(reset_time))
                
                # Check rate limit
                if self.rate_limit_remaining < 10:
                    wait_time = (self.rate_limit_reset - datetime.utcnow()).total_seconds()
                    if wait_time > 0:
                        logger.warning(
                            "Rate limit approaching, waiting",
                            wait_time=wait_time
                        )
                        await asyncio.sleep(min(wait_time, 60))
                
                if response.status == 404:
                    return None
                elif response.status >= 400:
                    error_text = await response.text()
                    raise GitLabAPIError(
                        f"GitLab API error {response.status}: {error_text}"
                    )
                
                if response.content_type == 'application/json':
                    return await response.json()
                else:
                    return {"text": await response.text()}
                    
        except aiohttp.ClientError as e:
            logger.error("GitLab API request failed", error=str(e), url=url)
            raise GitLabAPIError(f"Request failed: {e}")
    
    async def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project information"""
        cache_key = f"project_{project_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        project = await self._make_request("GET", f"projects/{project_id}")
        if project:
            self.cache[cache_key] = project
        return project
    
    async def get_merge_request(
        self, 
        project_id: int, 
        mr_iid: int
    ) -> Optional[Dict[str, Any]]:
        """Get merge request details"""
        cache_key = f"mr_{project_id}_{mr_iid}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        mr = await self._make_request(
            "GET", 
            f"projects/{project_id}/merge_requests/{mr_iid}"
        )
        if mr:
            self.cache[cache_key] = mr
        return mr
    
    async def get_merge_request_changes(
        self, 
        project_id: int, 
        mr_iid: int
    ) -> Optional[Dict[str, Any]]:
        """Get merge request changes/diff"""
        return await self._make_request(
            "GET",
            f"projects/{project_id}/merge_requests/{mr_iid}/changes"
        )
    
    async def list_merge_requests(
        self,
        project_id: int,
        state: str = "opened",
        per_page: int = 20
    ) -> List[Dict[str, Any]]:
        """List merge requests for a project"""
        params = {
            "state": state,
            "per_page": per_page,
            "order_by": "updated_at",
            "sort": "desc"
        }
        
        mrs = await self._make_request(
            "GET",
            f"projects/{project_id}/merge_requests",
            params=params
        )
        return mrs or []
    
    async def create_merge_request_note(
        self,
        project_id: int,
        mr_iid: int,
        body: str
    ) -> Optional[Dict[str, Any]]:
        """Create a note/comment on a merge request"""
        data = {"body": body}
        
        return await self._make_request(
            "POST",
            f"projects/{project_id}/merge_requests/{mr_iid}/notes",
            json=data
        )
    
    async def update_merge_request(
        self,
        project_id: int,
        mr_iid: int,
        **updates
    ) -> Optional[Dict[str, Any]]:
        """Update merge request (title, description, labels, etc.)"""
        return await self._make_request(
            "PUT",
            f"projects/{project_id}/merge_requests/{mr_iid}",
            json=updates
        )
    
    async def get_pipeline(
        self, 
        project_id: int, 
        pipeline_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get pipeline details"""
        cache_key = f"pipeline_{project_id}_{pipeline_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        pipeline = await self._make_request(
            "GET",
            f"projects/{project_id}/pipelines/{pipeline_id}"
        )
        if pipeline:
            self.cache[cache_key] = pipeline
        return pipeline
    
    async def get_pipeline_jobs(
        self,
        project_id: int,
        pipeline_id: int
    ) -> List[Dict[str, Any]]:
        """Get jobs for a pipeline"""
        jobs = await self._make_request(
            "GET",
            f"projects/{project_id}/pipelines/{pipeline_id}/jobs"
        )
        return jobs or []
    
    async def get_job_log(
        self,
        project_id: int,
        job_id: int
    ) -> Optional[str]:
        """Get job log/trace"""
        log_data = await self._make_request(
            "GET",
            f"projects/{project_id}/jobs/{job_id}/trace"
        )
        return log_data.get("text") if log_data else None
    
    async def retry_pipeline(
        self,
        project_id: int,
        pipeline_id: int
    ) -> Optional[Dict[str, Any]]:
        """Retry a failed pipeline"""
        return await self._make_request(
            "POST",
            f"projects/{project_id}/pipelines/{pipeline_id}/retry"
        )
    
    async def cancel_pipeline(
        self,
        project_id: int,
        pipeline_id: int
    ) -> Optional[Dict[str, Any]]:
        """Cancel a running pipeline"""
        return await self._make_request(
            "POST",
            f"projects/{project_id}/pipelines/{pipeline_id}/cancel"
        )
    
    async def list_project_pipelines(
        self,
        project_id: int,
        ref: str = None,
        status: str = None,
        per_page: int = 20
    ) -> List[Dict[str, Any]]:
        """List pipelines for a project"""
        params = {
            "per_page": per_page,
            "order_by": "updated_at",
            "sort": "desc"
        }
        
        if ref:
            params["ref"] = ref
        if status:
            params["status"] = status
        
        pipelines = await self._make_request(
            "GET",
            f"projects/{project_id}/pipelines",
            params=params
        )
        return pipelines or []
    
    async def get_user(self, user_id: int = None) -> Optional[Dict[str, Any]]:
        """Get user information (current user if no ID provided)"""
        endpoint = f"users/{user_id}" if user_id else "user"
        cache_key = f"user_{user_id or 'current'}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        user = await self._make_request("GET", endpoint)
        if user:
            self.cache[cache_key] = user
        return user
    
    async def search_projects(
        self,
        search: str,
        per_page: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for projects"""
        params = {
            "search": search,
            "per_page": per_page,
            "simple": True
        }
        
        projects = await self._make_request(
            "GET",
            "projects",
            params=params
        )
        return projects or []
    
    async def get_project_members(
        self,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """Get project members"""
        cache_key = f"members_{project_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        members = await self._make_request(
            "GET",
            f"projects/{project_id}/members/all"
        )
        if members:
            self.cache[cache_key] = members
        return members or []
    
    async def get_project_repository_tree(
        self,
        project_id: int,
        path: str = "",
        ref: str = "main"
    ) -> List[Dict[str, Any]]:
        """Get repository file tree"""
        params = {
            "path": path,
            "ref": ref,
            "recursive": False
        }
        
        tree = await self._make_request(
            "GET",
            f"projects/{project_id}/repository/tree",
            params=params
        )
        return tree or []
    
    async def get_file_content(
        self,
        project_id: int,
        file_path: str,
        ref: str = "main"
    ) -> Optional[str]:
        """Get file content from repository"""
        import base64
        
        params = {"ref": ref}
        file_data = await self._make_request(
            "GET",
            f"projects/{project_id}/repository/files/{file_path.replace('/', '%2F')}",
            params=params
        )
        
        if file_data and "content" in file_data:
            try:
                return base64.b64decode(file_data["content"]).decode('utf-8')
            except Exception as e:
                logger.error("Failed to decode file content", error=str(e))
                return None
        return None
    
    async def health_check(self) -> bool:
        """Check if GitLab API is accessible"""
        try:
            user = await self.get_user()
            return user is not None
        except Exception as e:
            logger.error("GitLab health check failed", error=str(e))
            return False

# Global client instance
_gitlab_client: Optional[GitLabClient] = None

def get_gitlab_client() -> GitLabClient:
    """Get or create GitLab client instance"""
    global _gitlab_client
    if _gitlab_client is None:
        _gitlab_client = GitLabClient()
    return _gitlab_client

async def close_gitlab_client():
    """Close GitLab client"""
    global _gitlab_client
    if _gitlab_client:
        await _gitlab_client.close()
        _gitlab_client = None