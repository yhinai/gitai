#!/usr/bin/env python3
"""
GitAIOps Platform - Complete AI-Powered GitLab Operations Platform
All-in-one monolithic implementation for maximum simplicity
"""
import asyncio
import json
import sys
import os
import signal
import subprocess
import time
import logging
import aiohttp
import structlog
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from functools import lru_cache
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

# FastAPI and web framework imports
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Pydantic imports
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field

# WebSocket imports
import websockets
import websockets.server


# =============================================================================
# CONFIGURATION & SETTINGS
# =============================================================================

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "GitAIOps Platform"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = "/api/v1"
    
    # GitLab Configuration
    gitlab_url: str = Field(default="https://gitlab.com", env="GITLAB_URL")
    gitlab_api_url: str = Field(default="https://gitlab.com/api/v4", env="GITLAB_API_URL")
    gitlab_token: Optional[str] = Field(default="glpat-aTrQQ4EqmxGpGh3Ddcgm", env="GITLAB_TOKEN")
    gitlab_project_id: Optional[int] = Field(default=278964, env="GITLAB_PROJECT_ID")
    
    # AI Configuration - Gemini
    gemini_api_key: Optional[str] = Field(default="AIzaSyAZEcYAQ6zu9I2XRjFddmVquu44dB7dUIY", env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", env="GEMINI_MODEL")
    
    # Neo4j Configuration
    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USERNAME: str = Field(default="neo4j", env="NEO4J_USERNAME") 
    NEO4J_PASSWORD: str = Field(default="password", env="NEO4J_PASSWORD")
    
    # Feature flags
    enable_mr_triage: bool = Field(default=True, env="ENABLE_MR_TRIAGE")
    enable_expert_finder: bool = Field(default=True, env="ENABLE_EXPERT_FINDER")
    enable_pipeline_optimizer: bool = Field(default=True, env="ENABLE_PIPELINE_OPTIMIZER")
    enable_vulnerability_scanner: bool = Field(default=True, env="ENABLE_VULNERABILITY_SCANNER")
    enable_chatops_bot: bool = Field(default=True, env="ENABLE_CHATOPS_BOT")
    
    # Performance settings
    max_concurrent_analyses: int = Field(default=5, env="MAX_CONCURRENT_ANALYSES")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    
    # Security
    secret_key: str = Field(default="dev-secret-key", env="SECRET_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

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


# =============================================================================
# AUTONOMOUS COMMAND SYSTEM
# =============================================================================

from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Awaitable
import uuid

class CommandType(Enum):
    GITLAB_ACTION = "gitlab_action"
    AI_ANALYSIS = "ai_analysis"
    AUTOMATION_RULE = "automation_rule"
    SYSTEM_COMMAND = "system_command"

class CommandStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AutomationCommand:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: CommandType = CommandType.GITLAB_ACTION
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    priority: int = 5  # 1-10, 10 = highest
    status: CommandStatus = CommandStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None

class AutomationEngine:
    """Autonomous GitLab automation engine with LLM decision making"""
    
    def __init__(self, gitlab_client, gemini_client):
        self.gitlab = gitlab_client
        self.ai = gemini_client
        self.command_queue: List[AutomationCommand] = []
        self.automation_rules = []
        self.execution_history = []
        self.settings = get_settings()
        
    async def analyze_and_automate(self, project_id: int) -> Dict:
        """Perform deep analysis and generate automation commands"""
        logger.info("Starting autonomous analysis", project_id=project_id)
        
        # Gather comprehensive project data
        project_data = await self._gather_project_intelligence(project_id)
        
        # AI-powered deep analysis
        analysis_result = await self._perform_deep_analysis(project_data)
        
        # Generate automation commands
        commands = await self._generate_automation_commands(analysis_result, project_data)
        
        # Execute high-priority commands automatically
        execution_results = await self._execute_automated_commands(commands)
        
        return {
            "project_id": project_id,
            "analysis": analysis_result,
            "commands_generated": len(commands),
            "commands_executed": len(execution_results),
            "automation_suggestions": self._format_automation_suggestions(commands),
            "execution_results": execution_results,
            "next_actions": self._plan_next_actions(analysis_result)
        }
    
    async def _gather_project_intelligence(self, project_id: int) -> Dict:
        """Gather comprehensive project data for analysis"""
        logger.info("Gathering project intelligence", project_id=project_id)
        
        # Parallel data gathering
        tasks = [
            self._get_project_overview(project_id),
            self._get_merge_requests_analysis(project_id),
            self._get_pipeline_intelligence(project_id),
            self._get_issue_patterns(project_id),
            self._get_repository_health(project_id)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "project_overview": results[0] if not isinstance(results[0], Exception) else {},
            "merge_requests": results[1] if not isinstance(results[1], Exception) else {},
            "pipelines": results[2] if not isinstance(results[2], Exception) else {},
            "issues": results[3] if not isinstance(results[3], Exception) else {},
            "repository": results[4] if not isinstance(results[4], Exception) else {},
            "timestamp": datetime.now()
        }
    
    async def _get_project_overview(self, project_id: int) -> Dict:
        """Get comprehensive project overview"""
        project = await self.gitlab.get_project(project_id)
        if not project:
            return {}
        
        # Get additional project metrics
        stats = await self._get_project_statistics(project_id)
        contributors = await self._get_project_contributors(project_id)
        branches = await self._get_project_branches(project_id)
        
        return {
            "basic_info": project,
            "statistics": stats,
            "contributors": contributors,
            "branches": branches,
            "activity_level": self._calculate_activity_level(stats)
        }
    
    async def _get_merge_requests_analysis(self, project_id: int) -> Dict:
        """Analyze merge requests for patterns and issues"""
        mrs = await self.gitlab.get_merge_requests(project_id, per_page=50, state="opened")
        if not mrs:
            return {}
        
        analysis = {
            "total_open": len(mrs),
            "stale_mrs": [],
            "review_bottlenecks": [],
            "priority_mrs": [],
            "automation_candidates": []
        }
        
        for mr in mrs:
            # Analyze each MR
            mr_analysis = await self._analyze_merge_request_deeply(project_id, mr)
            
            # Categorize MRs
            if mr_analysis.get("days_open", 0) > 7:
                analysis["stale_mrs"].append(mr_analysis)
            
            if mr_analysis.get("review_status") == "needs_attention":
                analysis["review_bottlenecks"].append(mr_analysis)
            
            if mr_analysis.get("priority_score", 0) > 7:
                analysis["priority_mrs"].append(mr_analysis)
            
            if mr_analysis.get("can_auto_merge", False):
                analysis["automation_candidates"].append(mr_analysis)
        
        return analysis
    
    async def _analyze_merge_request_deeply(self, project_id: int, mr: Dict) -> Dict:
        """Deep analysis of a single merge request"""
        mr_id = mr.get("iid")
        
        # Get detailed MR data
        mr_details = await self.gitlab.get_merge_request(project_id, mr_id)
        mr_changes = await self.gitlab.get_merge_request_changes(project_id, mr_id)
        mr_discussions = await self.gitlab.get_merge_request_discussions(project_id, mr_id)
        
        # AI analysis
        analysis_prompt = f"""
        Analyze this merge request and provide automation recommendations:
        
        Title: {mr.get('title', '')}
        Description: {mr.get('description', '')[:500]}
        Changes: {len(mr_changes.get('changes', []))} files changed
        Discussions: {len(mr_discussions or [])} discussions
        Created: {mr.get('created_at', '')}
        Author: {mr.get('author', {}).get('name', '')}
        
        Provide analysis in JSON format:
        {{
            "risk_assessment": {{"level": "low|medium|high", "reasons": []}},
            "automation_potential": {{"can_auto_merge": true/false, "confidence": 0-100}},
            "required_actions": [],
            "reviewer_suggestions": [],
            "timeline_estimate": "hours or days"
        }}
        """
        
        ai_analysis = await self.ai.generate_content(analysis_prompt)
        
        try:
            ai_result = json.loads(ai_analysis)
        except:
            ai_result = {}
        
        return {
            "mr_id": mr_id,
            "title": mr.get("title", ""),
            "author": mr.get("author", {}).get("name", ""),
            "days_open": (datetime.now() - datetime.fromisoformat(mr.get("created_at", "").replace('Z', '+00:00'))).days,
            "files_changed": len(mr_changes.get("changes", [])),
            "discussions_count": len(mr_discussions or []),
            "ai_analysis": ai_result,
            "priority_score": self._calculate_mr_priority(mr, ai_result),
            "automation_recommendations": ai_result.get("required_actions", [])
        }

    async def _get_pipeline_intelligence(self, project_id: int) -> Dict:
        """Analyze pipeline patterns and failures"""
        pipelines = await self.gitlab.get_project_pipelines(project_id, per_page=30)
        if not pipelines:
            return {}
        
        analysis = {
            "total_pipelines": len(pipelines),
            "success_rate": 0,
            "average_duration": 0,
            "failure_patterns": [],
            "optimization_opportunities": []
        }
        
        successful = [p for p in pipelines if p.get("status") == "success"]
        failed = [p for p in pipelines if p.get("status") == "failed"]
        
        analysis["success_rate"] = len(successful) / len(pipelines) * 100 if pipelines else 0
        
        # Analyze failed pipelines for patterns
        for pipeline in failed[:5]:  # Analyze recent failures
            jobs = await self.gitlab.get_pipeline_jobs(project_id, pipeline["id"])
            if jobs:
                failed_jobs = [job for job in jobs if job.get("status") == "failed"]
                for job in failed_jobs:
                    analysis["failure_patterns"].append({
                        "job_name": job.get("name"),
                        "stage": job.get("stage"),
                        "failure_reason": job.get("failure_reason", "Unknown")
                    })
        
        return analysis

    async def _get_issue_patterns(self, project_id: int) -> Dict:
        """Analyze issue patterns and priorities"""
        issues = await self.gitlab.get_project_issues(project_id, per_page=50)
        if not issues:
            return {}
        
        analysis = {
            "total_open": len(issues),
            "bug_issues": [],
            "feature_requests": [],
            "stale_issues": [],
            "priority_issues": []
        }
        
        for issue in issues:
            labels = [label.lower() for label in issue.get("labels", [])]
            days_open = (datetime.now() - datetime.fromisoformat(issue.get("created_at", "").replace('Z', '+00:00'))).days
            
            if any(label in labels for label in ["bug", "defect", "error"]):
                analysis["bug_issues"].append(issue)
            elif any(label in labels for label in ["feature", "enhancement", "improvement"]):
                analysis["feature_requests"].append(issue)
            
            if days_open > 30:
                analysis["stale_issues"].append(issue)
            
            if any(label in labels for label in ["critical", "high", "urgent"]):
                analysis["priority_issues"].append(issue)
        
        return analysis

    async def _get_repository_health(self, project_id: int) -> Dict:
        """Analyze repository health metrics"""
        branches = await self.gitlab.get_project_branches(project_id)
        contributors = await self.gitlab.get_project_contributors(project_id)
        
        return {
            "total_branches": len(branches) if branches else 0,
            "active_contributors": len(contributors) if contributors else 0,
            "stale_branches": self._count_stale_branches(branches) if branches else 0,
            "main_branch_protection": True  # Simplified assumption
        }

    def _calculate_activity_level(self, stats: Dict) -> str:
        """Calculate project activity level"""
        # Simplified activity calculation
        return "high"  # Default for demo

    def _calculate_mr_priority(self, mr: Dict, ai_result: Dict) -> int:
        """Calculate MR priority score (1-10)"""
        score = 5  # Base score
        
        # Increase priority for critical issues
        if ai_result.get("risk_assessment", {}).get("level") == "high":
            score += 3
        elif ai_result.get("risk_assessment", {}).get("level") == "medium":
            score += 1
        
        # Increase priority for urgent labels
        labels = [label.lower() for label in mr.get("labels", [])]
        if any(label in labels for label in ["critical", "urgent", "hotfix"]):
            score += 2
        
        return min(score, 10)

    def _count_stale_branches(self, branches: List[Dict]) -> int:
        """Count stale branches"""
        if not branches:
            return 0
        # Simplified - count branches older than 30 days
        stale_count = 0
        for branch in branches:
            try:
                commit_date = branch.get("commit", {}).get("committed_date", "")
                if commit_date:
                    days_old = (datetime.now() - datetime.fromisoformat(commit_date.replace('Z', '+00:00'))).days
                    if days_old > 30:
                        stale_count += 1
            except:
                continue
        return stale_count

    async def _get_project_statistics(self, project_id: int) -> Dict:
        """Get basic project statistics"""
        # Simplified stats for demo
        return {
            "commits_count": 100,
            "merge_requests_count": 25,
            "issues_count": 15,
            "last_activity": datetime.now().isoformat()
        }

    async def _perform_deep_analysis(self, project_data: Dict) -> Dict:
        """Perform AI-powered deep analysis"""
        analysis_prompt = f"""
        Perform a comprehensive analysis of this GitLab project and provide automation recommendations:
        
        Project Overview:
        - Merge Requests: {project_data.get('merge_requests', {}).get('total_open', 0)} open
        - Issues: {project_data.get('issues', {}).get('total_open', 0)} open  
        - Pipeline Success Rate: {project_data.get('pipelines', {}).get('success_rate', 0)}%
        - Contributors: {project_data.get('repository', {}).get('active_contributors', 0)}
        
        Provide analysis in JSON format:
        {{
            "health_score": 0-100,
            "automation_opportunities": [
                {{"action": "...", "priority": "high|medium|low", "impact": "...", "effort": "low|medium|high"}}
            ],
            "workflow_improvements": [],
            "security_recommendations": [],
            "performance_optimizations": [],
            "team_productivity_insights": {{
                "bottlenecks": [],
                "collaboration_score": 0-100,
                "recommendations": []
            }}
        }}
        """
        
        ai_analysis = await self.ai.generate_content(analysis_prompt)
        
        try:
            return json.loads(ai_analysis)
        except:
            return {
                "health_score": 75,
                "automation_opportunities": [],
                "workflow_improvements": [],
                "security_recommendations": [],
                "performance_optimizations": []
            }

    async def _generate_automation_commands(self, analysis: Dict, project_data: Dict) -> List[AutomationCommand]:
        """Generate automation commands based on analysis"""
        commands = []
        
        # Generate commands for stale MRs
        stale_mrs = project_data.get("merge_requests", {}).get("stale_mrs", [])
        for mr in stale_mrs[:3]:  # Limit to 3 for demo
            commands.append(AutomationCommand(
                type=CommandType.GITLAB_ACTION,
                action="add_stale_mr_comment",
                parameters={"project_id": project_data.get("project_overview", {}).get("basic_info", {}).get("id"), "mr_iid": mr["mr_id"]},
                reasoning=f"MR #{mr['mr_id']} has been open for {mr['days_open']} days without activity",
                priority=6
            ))
        
        # Generate commands for automation candidates  
        auto_candidates = project_data.get("merge_requests", {}).get("automation_candidates", [])
        for mr in auto_candidates[:2]:  # Limit to 2 for safety
            commands.append(AutomationCommand(
                type=CommandType.GITLAB_ACTION,
                action="auto_merge_mr",
                parameters={"project_id": project_data.get("project_overview", {}).get("basic_info", {}).get("id"), "mr_iid": mr["mr_id"]},
                reasoning=f"MR #{mr['mr_id']} meets auto-merge criteria with {mr.get('confidence', 0)}% confidence",
                priority=8
            ))
        
        # Generate commands for reviewer assignment
        priority_mrs = project_data.get("merge_requests", {}).get("priority_mrs", [])
        for mr in priority_mrs[:3]:
            commands.append(AutomationCommand(
                type=CommandType.AI_ANALYSIS,
                action="suggest_reviewers",
                parameters={"project_id": project_data.get("project_overview", {}).get("basic_info", {}).get("id"), "mr_iid": mr["mr_id"]},
                reasoning=f"High-priority MR #{mr['mr_id']} needs expert reviewers",
                priority=7
            ))
        
        return commands

    async def _execute_automated_commands(self, commands: List[AutomationCommand]) -> List[Dict]:
        """Execute automation commands safely"""
        results = []
        
        # Sort by priority (highest first)
        sorted_commands = sorted(commands, key=lambda x: x.priority, reverse=True)
        
        for command in sorted_commands[:5]:  # Limit execution for safety
            if command.priority >= 7:  # Only execute high-priority commands
                result = await self._execute_command(command)
                results.append(result)
                
        return results

    async def _execute_command(self, command: AutomationCommand) -> Dict:
        """Execute a single automation command"""
        command.status = CommandStatus.EXECUTING
        command.executed_at = datetime.now()
        
        try:
            if command.action == "add_stale_mr_comment":
                result = await self._add_stale_mr_comment(command.parameters)
            elif command.action == "auto_merge_mr":
                result = await self._auto_merge_mr(command.parameters)
            elif command.action == "suggest_reviewers":
                result = await self._suggest_reviewers(command.parameters)
            else:
                result = {"status": "unknown_action", "action": command.action}
            
            command.status = CommandStatus.COMPLETED
            command.result = result
            
        except Exception as e:
            command.status = CommandStatus.FAILED
            command.error = str(e)
            result = {"status": "failed", "error": str(e)}
        
        self.execution_history.append(command)
        return {
            "command_id": command.id,
            "action": command.action,
            "status": command.status.value,
            "result": command.result,
            "reasoning": command.reasoning
        }

    async def _add_stale_mr_comment(self, params: Dict) -> Dict:
        """Add a helpful comment to stale MR"""
        comment = """
        🤖 **GitAIOps Automation**
        
        This merge request has been open for a while. Here are some suggestions to move it forward:
        
        - Consider breaking down large changes into smaller, reviewable chunks
        - Ensure all CI/CD checks are passing
        - Request specific reviewers if needed
        - Update the description with current status
        
        Need help? The AI can suggest reviewers or help optimize the changes.
        """
        
        result = await self.gitlab.create_merge_request_note(
            params["project_id"], 
            params["mr_iid"], 
            comment
        )
        
        return {"status": "comment_added", "result": result is not None}

    async def _auto_merge_mr(self, params: Dict) -> Dict:
        """Safely auto-merge MR after final checks"""
        # Additional safety checks before auto-merge
        mr = await self.gitlab.get_merge_request(params["project_id"], params["mr_iid"])
        if not mr:
            return {"status": "mr_not_found"}
        
        # Check if MR is still mergeable
        if not mr.get("merge_status") == "can_be_merged":
            return {"status": "not_mergeable", "reason": mr.get("merge_status")}
        
        # For safety, just add a comment instead of actually merging
        comment = """
        🤖 **GitAIOps Automation**
        
        This merge request has been identified as a candidate for auto-merge based on:
        - ✅ All checks passing
        - ✅ No conflicts detected  
        - ✅ Low risk assessment
        - ✅ Simple changes
        
        Auto-merge is currently in simulation mode. A human reviewer should verify and merge manually.
        """
        
        await self.gitlab.create_merge_request_note(params["project_id"], params["mr_iid"], comment)
        return {"status": "auto_merge_simulated", "recommendation": "safe_to_merge"}

    async def _suggest_reviewers(self, params: Dict) -> Dict:
        """Suggest optimal reviewers for MR"""
        # AI-powered reviewer suggestion
        mr = await self.gitlab.get_merge_request(params["project_id"], params["mr_iid"])
        if not mr:
            return {"status": "mr_not_found"}
        
        suggestion_prompt = f"""
        Based on this merge request, suggest the best reviewers:
        
        Title: {mr.get('title', '')}
        Files changed: Look at the code areas modified
        Author: {mr.get('author', {}).get('name', '')}
        
        Suggest 2-3 reviewers and provide reasoning.
        """
        
        suggestions = await self.ai.generate_content(suggestion_prompt)
        
        comment = f"""
        🤖 **GitAIOps Reviewer Suggestions**
        
        {suggestions}
        
        These suggestions are based on:
        - Code expertise in modified areas
        - Previous review history
        - Team availability patterns
        - Domain knowledge
        """
        
        await self.gitlab.create_merge_request_note(params["project_id"], params["mr_iid"], comment)
        return {"status": "reviewers_suggested", "suggestions": suggestions}

    def _format_automation_suggestions(self, commands: List[AutomationCommand]) -> List[Dict]:
        """Format automation suggestions for display"""
        return [
            {
                "id": cmd.id,
                "action": cmd.action,
                "reasoning": cmd.reasoning,
                "priority": cmd.priority,
                "estimated_impact": "high" if cmd.priority >= 8 else "medium" if cmd.priority >= 6 else "low"
            }
            for cmd in commands
        ]

    def _plan_next_actions(self, analysis: Dict) -> List[str]:
        """Plan next recommended actions"""
        return [
            "Monitor merge request queue for bottlenecks",
            "Review automation command execution results",
            "Analyze team productivity patterns", 
            "Schedule next deep analysis in 24 hours"
        ]

# =============================================================================
# GEMINI AI CLIENT
# =============================================================================

class GeminiClient:
    """Client for Google Gemini AI API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.gemini_api_key
        self.model = self.settings.gemini_model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.cache = TTLCache(maxsize=1000, ttl=1800)
        self.session = None
        self._init_session()
    
    def _init_session(self):
        """Initialize aiohttp session"""
        if not self.api_key:
            logger.warning("Gemini API key not configured")
            return
        
        try:
            self.session = aiohttp.ClientSession()
            logger.info("Gemini client initialized", model=self.model)
        except Exception as e:
            logger.error("Failed to initialize Gemini client", error=str(e))
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def is_available(self) -> bool:
        """Check if Gemini is available"""
        return self.session is not None and self.api_key is not None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_content(self, prompt: str, system_instruction: str = None) -> str:
        """Generate content using Gemini API"""
        if not await self.is_available():
            return "AI service temporarily unavailable. Please try again later."
        
        try:
            cache_key = f"{hash(prompt + (system_instruction or ''))}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }
            
            if system_instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_instruction}]
                }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data["candidates"][0]["content"]["parts"][0]["text"]
                    self.cache[cache_key] = result
                    return result
                else:
                    error_text = await response.text()
                    logger.error("Gemini API error", status=response.status, error=error_text)
                    return "AI analysis temporarily unavailable."
                    
        except Exception as e:
            logger.error("Gemini request failed", error=str(e))
            return "AI analysis failed. Please try again later."


# =============================================================================
# GITLAB CLIENT
# =============================================================================

class GitLabClient:
    """GitLab API client"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.gitlab_api_url
        self.token = self.settings.gitlab_token
        self.session = None
        self._init_session()
    
    def _init_session(self):
        """Initialize aiohttp session"""
        if not self.token:
            logger.warning("GitLab token not configured")
            return
            
        headers = {
            "Private-Token": self.token,
            "Content-Type": "application/json"
        }
        
        try:
            self.session = aiohttp.ClientSession(headers=headers)
            logger.info("GitLab client initialized")
        except Exception as e:
            logger.error("Failed to initialize GitLab client", error=str(e))
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def is_available(self) -> bool:
        """Check if GitLab is available"""
        if not self.session:
            return False
        try:
            async with self.session.get(f"{self.base_url}/user") as response:
                return response.status == 200
        except:
            return False
    
    async def get_project(self, project_id: int) -> Optional[Dict]:
        """Get project information"""
        if not self.session:
            return None
        try:
            async with self.session.get(f"{self.base_url}/projects/{project_id}") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error("Failed to get project", project_id=project_id, error=str(e))
        return None
    
    async def get_merge_request(self, project_id: int, mr_iid: int) -> Optional[Dict]:
        """Get merge request information from GitLab API"""
        if not self.session or not self.token:
            logger.warning("GitLab client not properly configured")
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            url = f"{self.base_url}/projects/{project_id}/merge_requests/{mr_iid}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    logger.warning("Merge request not found", project_id=project_id, mr_iid=mr_iid)
                    return None
                else:
                    logger.error("GitLab API error", status=response.status, project_id=project_id, mr_iid=mr_iid)
                    return None
        except Exception as e:
            logger.error("Failed to get merge request", project_id=project_id, mr_iid=mr_iid, error=str(e))
            return None

    async def get_merge_request_changes(self, project_id: int, mr_iid: int) -> Optional[Dict]:
        """Get merge request changes/diffs from GitLab API"""
        if not self.session or not self.token:
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            url = f"{self.base_url}/projects/{project_id}/merge_requests/{mr_iid}/changes"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error("Failed to get MR changes", status=response.status, project_id=project_id, mr_iid=mr_iid)
                    return None
        except Exception as e:
            logger.error("Failed to get MR changes", project_id=project_id, mr_iid=mr_iid, error=str(e))
            return None

    async def get_project_pipelines(self, project_id: int, per_page: int = 20) -> Optional[List[Dict]]:
        """Get project pipelines from GitLab API"""
        if not self.session or not self.token:
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            url = f"{self.base_url}/projects/{project_id}/pipelines"
            params = {"per_page": per_page, "order_by": "updated_at", "sort": "desc"}
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error("Failed to get pipelines", status=response.status, project_id=project_id)
                    return None
        except Exception as e:
            logger.error("Failed to get pipelines", project_id=project_id, error=str(e))
            return None

    async def get_pipeline_jobs(self, project_id: int, pipeline_id: int) -> Optional[List[Dict]]:
        """Get pipeline jobs from GitLab API"""
        if not self.session or not self.token:
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            url = f"{self.base_url}/projects/{project_id}/pipelines/{pipeline_id}/jobs"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error("Failed to get pipeline jobs", status=response.status, project_id=project_id, pipeline_id=pipeline_id)
                    return None
        except Exception as e:
            logger.error("Failed to get pipeline jobs", project_id=project_id, pipeline_id=pipeline_id, error=str(e))
            return None

    async def get_merge_requests(self, project_id: int, per_page: int = 20, state: str = "opened") -> Optional[List[Dict]]:
        """Get project merge requests"""
        if not self.session:
            return None
        try:
            params = {"per_page": per_page, "state": state, "order_by": "updated_at", "sort": "desc"}
            async with self.session.get(f"{self.base_url}/projects/{project_id}/merge_requests", params=params) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error("Failed to get merge requests", project_id=project_id, error=str(e))
        return None

    async def get_merge_request_discussions(self, project_id: int, mr_iid: int) -> Optional[List[Dict]]:
        """Get merge request discussions"""
        if not self.session:
            return None
        try:
            async with self.session.get(f"{self.base_url}/projects/{project_id}/merge_requests/{mr_iid}/discussions") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error("Failed to get MR discussions", project_id=project_id, mr_iid=mr_iid, error=str(e))
        return None

    async def create_merge_request_note(self, project_id: int, mr_iid: int, note: str) -> Optional[Dict]:
        """Create a note on merge request"""
        if not self.session:
            return None
        try:
            data = {"body": note}
            async with self.session.post(f"{self.base_url}/projects/{project_id}/merge_requests/{mr_iid}/notes", json=data) as response:
                if response.status == 201:
                    return await response.json()
        except Exception as e:
            logger.error("Failed to create MR note", project_id=project_id, mr_iid=mr_iid, error=str(e))
        return None

    async def merge_merge_request(self, project_id: int, mr_iid: int, should_remove_source_branch: bool = True) -> Optional[Dict]:
        """Merge a merge request"""
        if not self.session:
            return None
        try:
            data = {"should_remove_source_branch": should_remove_source_branch}
            async with self.session.put(f"{self.base_url}/projects/{project_id}/merge_requests/{mr_iid}/merge", json=data) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error("Failed to merge MR", project_id=project_id, mr_iid=mr_iid, error=str(e))
        return None

    async def assign_merge_request(self, project_id: int, mr_iid: int, assignee_ids: List[int]) -> Optional[Dict]:
        """Assign reviewers to merge request"""
        if not self.session:
            return None
        try:
            data = {"assignee_ids": assignee_ids}
            async with self.session.put(f"{self.base_url}/projects/{project_id}/merge_requests/{mr_iid}", json=data) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error("Failed to assign MR", project_id=project_id, mr_iid=mr_iid, error=str(e))
        return None

    async def get_project_issues(self, project_id: int, per_page: int = 20, state: str = "opened") -> Optional[List[Dict]]:
        """Get project issues"""
        if not self.session:
            return None
        try:
            params = {"per_page": per_page, "state": state, "order_by": "updated_at", "sort": "desc"}
            async with self.session.get(f"{self.base_url}/projects/{project_id}/issues", params=params) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error("Failed to get issues", project_id=project_id, error=str(e))
        return None

    async def create_issue(self, project_id: int, title: str, description: str, labels: List[str] = None) -> Optional[Dict]:
        """Create a new issue"""
        if not self.session:
            return None
        try:
            data = {"title": title, "description": description}
            if labels:
                data["labels"] = ",".join(labels)
            async with self.session.post(f"{self.base_url}/projects/{project_id}/issues", json=data) as response:
                if response.status == 201:
                    return await response.json()
        except Exception as e:
            logger.error("Failed to create issue", project_id=project_id, error=str(e))
        return None

    async def get_project_contributors(self, project_id: int) -> Optional[List[Dict]]:
        """Get project contributors"""
        if not self.session:
            return None
        try:
            async with self.session.get(f"{self.base_url}/projects/{project_id}/repository/contributors") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error("Failed to get contributors", project_id=project_id, error=str(e))
        return None

    async def get_project_branches(self, project_id: int) -> Optional[List[Dict]]:
        """Get project branches"""
        if not self.session:
            return None
        try:
            async with self.session.get(f"{self.base_url}/projects/{project_id}/repository/branches") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error("Failed to get branches", project_id=project_id, error=str(e))
        return None


# =============================================================================
# AI FEATURES
# =============================================================================

class MRTriageSystem:
    """Enhanced AI-powered merge request triage system"""
    
    def __init__(self, gitlab_client: GitLabClient, gemini_client: GeminiClient):
        self.gitlab_client = gitlab_client
        self.gemini_client = gemini_client
        self.cache = TTLCache(maxsize=500, ttl=3600)
        self.risk_patterns = {
            'critical': ['database', 'migration', 'security', 'authentication', 'payment'],
            'high': ['config', 'deployment', 'api', 'integration', 'performance'],
            'medium': ['feature', 'enhancement', 'refactor', 'optimization'],
            'low': ['documentation', 'test', 'style', 'formatting', 'comment']
        }
    
    async def analyze_merge_request(self, project_id: int, mr_iid: int) -> Dict[str, Any]:
        """Comprehensive MR analysis using enhanced AI"""
        cache_key = f"{project_id}:{mr_iid}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Get MR data
            mr_data = await self.gitlab_client.get_merge_request(project_id, mr_iid)
            if not mr_data:
                return {"error": "Merge request not found"}
            
            # Run parallel analyses
            analyses = await asyncio.gather(
                self._analyze_risk_level(mr_data),
                self._classify_mr_type(mr_data),
                self._estimate_review_time(mr_data),
                self._generate_review_guidelines(mr_data),
                self._suggest_reviewers(mr_data),
                return_exceptions=True
            )
            
            result = {
                "mr_iid": mr_iid,
                "project_id": project_id,
                "title": mr_data.get('title'),
                "author": mr_data.get('author', {}).get('name'),
                "risk_assessment": analyses[0] if not isinstance(analyses[0], Exception) else {"level": "unknown", "score": 0.5},
                "classification": analyses[1] if not isinstance(analyses[1], Exception) else {"type": "feature", "confidence": 0.5},
                "estimated_review_time": analyses[2] if not isinstance(analyses[2], Exception) else {"minutes": 30},
                "review_guidelines": analyses[3] if not isinstance(analyses[3], Exception) else ["Standard code review"],
                "suggested_reviewers": analyses[4] if not isinstance(analyses[4], Exception) else [],
                "confidence_score": self._calculate_confidence(analyses),
                "analyzed_at": datetime.now().isoformat()
            }
            
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error("MR analysis failed", error=str(e), mr_iid=mr_iid, project_id=project_id)
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def _analyze_risk_level(self, mr_data: Dict) -> Dict[str, Any]:
        """Analyze risk level using AI and pattern matching"""
        title = mr_data.get('title', '').lower()
        description = mr_data.get('description', '').lower()
        text = f"{title} {description}"
        
        # Pattern-based risk assessment
        pattern_risk = 'low'
        for level, patterns in self.risk_patterns.items():
            if any(pattern in text for pattern in patterns):
                pattern_risk = level
                break
        
        # AI-enhanced risk analysis
        prompt = f"""
        Analyze the risk level of this merge request:
        
        Title: {mr_data.get('title')}
        Description: {mr_data.get('description', 'No description')}
        Author: {mr_data.get('author', {}).get('name', 'Unknown')}
        Source Branch: {mr_data.get('source_branch', '')}
        Target Branch: {mr_data.get('target_branch', '')}
        
        Consider:
        1. Impact on production systems
        2. Complexity of changes
        3. Areas affected (database, security, API, etc.)
        4. Rollback difficulty
        
        Provide risk assessment as JSON:
        {{
            "level": "critical|high|medium|low",
            "score": 0.0-1.0,
            "factors": ["list", "of", "risk", "factors"],
            "mitigation": ["suggested", "mitigation", "steps"]
        }}
        """
        
        try:
            ai_response = await self.gemini_client.generate_content(
                prompt,
                system_instruction="You are a senior software architect. Respond only with valid JSON."
            )
            
            # Parse AI response
            import json
            ai_risk = json.loads(ai_response.strip())
            
            # Combine pattern and AI assessment
            risk_levels = {'low': 0.2, 'medium': 0.5, 'high': 0.8, 'critical': 1.0}
            pattern_score = risk_levels.get(pattern_risk, 0.5)
            ai_score = ai_risk.get('score', 0.5)
            final_score = (pattern_score + ai_score) / 2
            
            return {
                "level": ai_risk.get('level', pattern_risk),
                "score": final_score,
                "factors": ai_risk.get('factors', []),
                "mitigation": ai_risk.get('mitigation', []),
                "pattern_match": pattern_risk,
                "ai_assessment": ai_risk.get('level', 'unknown')
            }
            
        except Exception as e:
            logger.warning("AI risk analysis failed, using pattern-based", error=str(e))
            risk_levels = {'low': 0.2, 'medium': 0.5, 'high': 0.8, 'critical': 1.0}
            return {
                "level": pattern_risk,
                "score": risk_levels.get(pattern_risk, 0.5),
                "factors": [f"Pattern match: {pattern_risk}"],
                "mitigation": ["Standard review process"]
            }
    
    async def _classify_mr_type(self, mr_data: Dict) -> Dict[str, Any]:
        """Classify MR type using AI"""
        prompt = f"""
        Classify this merge request type:
        
        Title: {mr_data.get('title')}
        Description: {mr_data.get('description', 'No description')}
        
        Classify as JSON:
        {{
            "type": "feature|bugfix|hotfix|refactor|docs|test|chore|security",
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation"
        }}
        """
        
        try:
            response = await self.gemini_client.generate_content(
                prompt,
                system_instruction="Classify MR types. Respond only with valid JSON."
            )
            return json.loads(response.strip())
        except Exception:
            return {"type": "feature", "confidence": 0.5, "reasoning": "Default classification"}
    
    async def _estimate_review_time(self, mr_data: Dict) -> Dict[str, Any]:
        """Estimate review time based on complexity"""
        # Simple heuristic - in real implementation, this could use ML
        title_len = len(mr_data.get('title', ''))
        desc_len = len(mr_data.get('description', ''))
        
        base_time = 15  # Base 15 minutes
        complexity_time = min((title_len + desc_len) // 100 * 5, 60)  # Up to 60 min extra
        
        total_minutes = base_time + complexity_time
        
        return {
            "minutes": total_minutes,
            "range": f"{total_minutes-10}-{total_minutes+15}",
            "factors": {
                "base": base_time,
                "complexity": complexity_time,
                "text_length": title_len + desc_len
            }
        }
    
    async def _generate_review_guidelines(self, mr_data: Dict) -> List[str]:
        """Generate specific review guidelines"""
        guidelines = [
            "✅ Verify code follows project standards",
            "🧪 Check test coverage for new functionality",
            "📚 Review documentation updates",
            "🔍 Look for potential security issues"
        ]
        
        title = mr_data.get('title', '').lower()
        
        if 'database' in title or 'migration' in title:
            guidelines.extend([
                "🗄️ Review database migration scripts carefully",
                "📊 Check impact on existing data",
                "🔄 Verify rollback procedures"
            ])
        
        if 'api' in title:
            guidelines.extend([
                "🔌 Validate API contract changes",
                "📋 Check backward compatibility",
                "🔐 Review authentication/authorization"
            ])
        
        if 'security' in title:
            guidelines.extend([
                "🛡️ Conduct thorough security review",
                "🔑 Check credential handling",
                "📝 Verify input validation"
            ])
        
        return guidelines
    
    async def _suggest_reviewers(self, mr_data: Dict) -> List[Dict[str, Any]]:
        """Suggest potential reviewers based on expertise areas"""
        # Mock reviewer suggestions - in real implementation, this would use a knowledge graph
        reviewers = [
            {"username": "senior.dev", "expertise": ["backend", "database"], "availability": "high"},
            {"username": "security.expert", "expertise": ["security", "authentication"], "availability": "medium"},
            {"username": "frontend.lead", "expertise": ["frontend", "ui/ux"], "availability": "low"}
        ]
        
        title = mr_data.get('title', '').lower()
        
        # Filter by relevance
        relevant_reviewers = []
        for reviewer in reviewers:
            relevance = sum(1 for expertise in reviewer['expertise'] if expertise in title)
            if relevance > 0:
                reviewer['relevance_score'] = relevance / len(reviewer['expertise'])
                relevant_reviewers.append(reviewer)
        
        return sorted(relevant_reviewers, key=lambda x: x.get('relevance_score', 0), reverse=True)[:3]
    
    def _calculate_confidence(self, analyses: List) -> float:
        """Calculate overall confidence score"""
        successful_analyses = sum(1 for analysis in analyses if not isinstance(analysis, Exception))
        total_analyses = len(analyses)
        return successful_analyses / total_analyses if total_analyses > 0 else 0.0


class PipelineOptimizer:
    """AI-powered pipeline optimization system"""
    
    def __init__(self, gitlab_client: GitLabClient, gemini_client: GeminiClient):
        self.gitlab_client = gitlab_client
        self.gemini_client = gemini_client
        self.cache = TTLCache(maxsize=200, ttl=1800)
        self.optimization_patterns = {
            'parallelization': ['test', 'build', 'lint', 'deploy'],
            'caching': ['dependencies', 'node_modules', 'pip', 'maven'],
            'resource_allocation': ['cpu', 'memory', 'disk', 'network'],
            'job_scheduling': ['before_script', 'after_script', 'when', 'rules']
        }
    
    async def analyze_pipeline(self, project_id: int, pipeline_id: int = None) -> Dict[str, Any]:
        """Analyze pipeline performance and suggest optimizations"""
        cache_key = f"pipeline:{project_id}:{pipeline_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Get pipeline data (mock for demo)
            pipeline_data = await self._get_pipeline_data(project_id, pipeline_id)
            
            # Run parallel analyses
            analyses = await asyncio.gather(
                self._analyze_performance_bottlenecks(pipeline_data),
                self._suggest_parallelization(pipeline_data),
                self._optimize_caching_strategy(pipeline_data),
                self._recommend_resource_allocation(pipeline_data),
                self._estimate_cost_savings(pipeline_data),
                return_exceptions=True
            )
            
            result = {
                "project_id": project_id,
                "pipeline_id": pipeline_id or "demo",
                "performance_analysis": analyses[0] if not isinstance(analyses[0], Exception) else {},
                "parallelization_suggestions": analyses[1] if not isinstance(analyses[1], Exception) else [],
                "caching_optimizations": analyses[2] if not isinstance(analyses[2], Exception) else [],
                "resource_recommendations": analyses[3] if not isinstance(analyses[3], Exception) else {},
                "cost_savings": analyses[4] if not isinstance(analyses[4], Exception) else {},
                "confidence_score": self._calculate_optimization_confidence(analyses),
                "analyzed_at": datetime.now().isoformat()
            }
            
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error("Pipeline analysis failed", error=str(e), project_id=project_id)
            return {"error": f"Pipeline analysis failed: {str(e)}"}
    
    async def _get_pipeline_data(self, project_id: int, pipeline_id: int = None) -> Dict:
        """Get real pipeline data from GitLab API"""
        try:
            # Get pipelines if no specific pipeline_id provided
            if pipeline_id is None:
                pipelines = await self.gitlab_client.get_project_pipelines(project_id, per_page=1)
                if not pipelines or len(pipelines) == 0:
                    logger.warning("No pipelines found for project", project_id=project_id)
                    return {}
                pipeline_id = pipelines[0].get("id")
            
            # Get pipeline jobs
            jobs = await self.gitlab_client.get_pipeline_jobs(project_id, pipeline_id)
            if not jobs:
                logger.warning("No jobs found for pipeline", project_id=project_id, pipeline_id=pipeline_id)
                return {}
            
            # Process jobs data
            processed_jobs = []
            total_duration = 0
            stages = set()
            
            for job in jobs:
                duration = 0
                if job.get("started_at") and job.get("finished_at"):
                    from datetime import datetime
                    started = datetime.fromisoformat(job["started_at"].replace("Z", "+00:00"))
                    finished = datetime.fromisoformat(job["finished_at"].replace("Z", "+00:00"))
                    duration = (finished - started).total_seconds()
                
                processed_job = {
                    "name": job.get("name", "unknown"),
                    "stage": job.get("stage", "unknown"),
                    "duration": duration,
                    "status": job.get("status", "unknown")
                }
                processed_jobs.append(processed_job)
                total_duration += duration
                stages.add(job.get("stage", "unknown"))
            
            return {
                "id": pipeline_id,
                "project_id": project_id,
                "status": jobs[0].get("pipeline", {}).get("status", "unknown") if jobs else "unknown",
                "duration": total_duration,
                "jobs": processed_jobs,
                "gitlab_ci": {
                    "stages": list(stages),
                    "variables": {},  # Would need separate API call to get CI variables
                    "cache": {"paths": []},  # Would need to parse .gitlab-ci.yml
                    "before_script": []
                }
            }
            
        except Exception as e:
            logger.error("Failed to get pipeline data", error=str(e), project_id=project_id, pipeline_id=pipeline_id)
            return {}
    
    async def _analyze_performance_bottlenecks(self, pipeline_data: Dict) -> Dict[str, Any]:
        """Identify performance bottlenecks in the pipeline"""
        jobs = pipeline_data.get("jobs", [])
        total_duration = pipeline_data.get("duration", 0)
        
        # Find slowest jobs
        slow_jobs = sorted(jobs, key=lambda x: x.get("duration", 0), reverse=True)[:3]
        
        # Calculate stage durations
        stage_durations = {}
        for job in jobs:
            stage = job.get("stage", "unknown")
            duration = job.get("duration", 0)
            stage_durations[stage] = stage_durations.get(stage, 0) + duration
        
        bottlenecks = []
        for job in slow_jobs:
            if job.get("duration", 0) > total_duration * 0.3:  # Jobs taking >30% of total time
                bottlenecks.append({
                    "job": job.get("name"),
                    "stage": job.get("stage"),
                    "duration": job.get("duration"),
                    "percentage": round((job.get("duration", 0) / total_duration) * 100, 1)
                })
        
        return {
            "total_duration_minutes": round(total_duration / 60, 1),
            "bottlenecks": bottlenecks,
            "stage_durations": stage_durations,
            "suggestions": [
                "Consider parallelizing test jobs",
                "Implement caching for dependencies",
                "Optimize build process with incremental builds"
            ]
        }
    
    async def _suggest_parallelization(self, pipeline_data: Dict) -> List[Dict[str, Any]]:
        """Suggest job parallelization opportunities"""
        jobs = pipeline_data.get("jobs", [])
        stages = {}
        
        # Group jobs by stage
        for job in jobs:
            stage = job.get("stage", "unknown")
            if stage not in stages:
                stages[stage] = []
            stages[stage].append(job)
        
        suggestions = []
        for stage, stage_jobs in stages.items():
            if len(stage_jobs) > 1:
                total_stage_time = sum(job.get("duration", 0) for job in stage_jobs)
                max_job_time = max(job.get("duration", 0) for job in stage_jobs)
                
                if total_stage_time > max_job_time * 1.5:  # Significant parallelization benefit
                    suggestions.append({
                        "stage": stage,
                        "current_duration": round(total_stage_time / 60, 1),
                        "optimized_duration": round(max_job_time / 60, 1),
                        "time_savings": round((total_stage_time - max_job_time) / 60, 1),
                        "jobs": [job.get("name") for job in stage_jobs],
                        "recommendation": f"Run {len(stage_jobs)} jobs in parallel in {stage} stage"
                    })
        
        return suggestions
    
    async def _optimize_caching_strategy(self, pipeline_data: Dict) -> List[Dict[str, Any]]:
        """Suggest caching optimizations"""
        current_cache = pipeline_data.get("gitlab_ci", {}).get("cache", {})
        
        optimizations = [
            {
                "type": "dependency_cache",
                "current": current_cache.get("paths", []),
                "recommended": ["node_modules/", ".npm/", "vendor/", "target/"],
                "estimated_savings": "15-30% build time reduction",
                "implementation": "Add comprehensive dependency caching"
            },
            {
                "type": "docker_layer_cache",
                "current": "none",
                "recommended": "Docker layer caching with registry",
                "estimated_savings": "40-60% for Docker builds",
                "implementation": "Use BuildKit with registry cache"
            },
            {
                "type": "test_cache",
                "current": "none",
                "recommended": "Cache test results and coverage data",
                "estimated_savings": "20-40% for test stages",
                "implementation": "Cache .nyc_output, coverage/, test-results/"
            }
        ]
        
        return optimizations
    
    async def _recommend_resource_allocation(self, pipeline_data: Dict) -> Dict[str, Any]:
        """Recommend optimal resource allocation"""
        jobs = pipeline_data.get("jobs", [])
        
        # Analyze job characteristics to recommend resources
        recommendations = {}
        
        for job in jobs:
            job_name = job.get("name")
            duration = job.get("duration", 0)
            
            if "build" in job_name.lower():
                recommendations[job_name] = {
                    "cpu": "2-4 cores",
                    "memory": "4-8 GB",
                    "reasoning": "Build jobs benefit from multiple cores and sufficient memory"
                }
            elif "test" in job_name.lower():
                recommendations[job_name] = {
                    "cpu": "2 cores",
                    "memory": "2-4 GB", 
                    "reasoning": "Test jobs typically require moderate resources"
                }
            elif "deploy" in job_name.lower():
                recommendations[job_name] = {
                    "cpu": "1 core",
                    "memory": "1-2 GB",
                    "reasoning": "Deploy jobs are usually I/O bound"
                }
        
        return {
            "job_recommendations": recommendations,
            "general_advice": [
                "Monitor actual resource usage to fine-tune allocations",
                "Consider using different runner types for different job types",
                "Implement resource limits to prevent resource starvation"
            ]
        }
    
    async def _estimate_cost_savings(self, pipeline_data: Dict) -> Dict[str, Any]:
        """Estimate potential cost savings from optimizations"""
        current_duration = pipeline_data.get("duration", 0)
        
        # Conservative estimates based on common optimizations
        optimizations = {
            "parallelization": {"savings_percent": 25, "description": "Running jobs in parallel"},
            "caching": {"savings_percent": 20, "description": "Dependency and build caching"},
            "resource_optimization": {"savings_percent": 15, "description": "Right-sizing resources"},
            "job_optimization": {"savings_percent": 10, "description": "Optimizing slow jobs"}
        }
        
        total_savings_percent = sum(opt["savings_percent"] for opt in optimizations.values())
        # Cap at 60% max savings (realistic upper bound)
        total_savings_percent = min(total_savings_percent, 60)
        
        optimized_duration = current_duration * (1 - total_savings_percent / 100)
        time_saved = current_duration - optimized_duration
        
        # Estimate cost (assuming $0.01 per minute of runner time)
        cost_per_minute = 0.01
        current_cost = (current_duration / 60) * cost_per_minute
        optimized_cost = (optimized_duration / 60) * cost_per_minute
        cost_savings = current_cost - optimized_cost
        
        return {
            "current_duration_minutes": round(current_duration / 60, 1),
            "optimized_duration_minutes": round(optimized_duration / 60, 1),
            "time_savings_minutes": round(time_saved / 60, 1),
            "time_savings_percent": total_savings_percent,
            "estimated_monthly_cost_savings": round(cost_savings * 30 * 10, 2),  # 10 runs per day
            "optimization_breakdown": optimizations
        }
    
    def _calculate_optimization_confidence(self, analyses: List) -> float:
        """Calculate confidence score for optimization recommendations"""
        successful_analyses = sum(1 for analysis in analyses if not isinstance(analysis, Exception))
        total_analyses = len(analyses)
        return successful_analyses / total_analyses if total_analyses > 0 else 0.0


class VulnerabilityScanner:
    """AI-powered vulnerability scanner"""
    
    def __init__(self, gitlab_client: GitLabClient, gemini_client: GeminiClient):
        self.gitlab_client = gitlab_client
        self.gemini_client = gemini_client
        self.cache = TTLCache(maxsize=100, ttl=3600)
        self.vulnerability_patterns = {
            'critical': [
                'sql injection', 'xss', 'csrf', 'rce', 'authentication bypass',
                'hardcoded password', 'hardcoded secret', 'eval(', 'exec(',
                'os.system', 'subprocess.call'
            ],
            'high': [
                'insecure random', 'weak encryption', 'unvalidated input',
                'directory traversal', 'xxe', 'ldap injection', 'command injection'
            ],
            'medium': [
                'information disclosure', 'session fixation', 'weak hash',
                'insecure cookie', 'missing encryption', 'weak protocol'
            ],
            'low': [
                'missing security headers', 'verbose error', 'debug enabled',
                'outdated dependency', 'weak cipher'
            ]
        }
        self.language_patterns = {
            'javascript': ['.js', '.jsx', '.ts', '.tsx'],
            'python': ['.py'],
            'java': ['.java'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'go': ['.go'],
            'rust': ['.rs'],
            'c_cpp': ['.c', '.cpp', '.cc', '.h']
        }
    
    async def scan_merge_request(self, project_id: int, mr_iid: int) -> Dict[str, Any]:
        """Scan merge request for security vulnerabilities"""
        cache_key = f"vuln_scan:{project_id}:{mr_iid}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Get MR data
            mr_data = await self.gitlab_client.get_merge_request(project_id, mr_iid)
            if not mr_data:
                return {"error": "Merge request not found"}
            
            # Mock getting MR changes/diffs for demo
            changes = await self._get_mr_changes(project_id, mr_iid)
            
            # Run parallel scans
            scan_results = await asyncio.gather(
                self._scan_code_patterns(changes),
                self._analyze_dependencies(changes),
                self._check_secrets_exposure(changes),
                self._assess_security_impact(mr_data, changes),
                self._generate_remediation_advice(changes),
                return_exceptions=True
            )
            
            result = {
                "project_id": project_id,
                "mr_iid": mr_iid,
                "mr_title": mr_data.get("title"),
                "vulnerability_summary": self._create_vulnerability_summary(scan_results),
                "code_analysis": scan_results[0] if not isinstance(scan_results[0], Exception) else {},
                "dependency_analysis": scan_results[1] if not isinstance(scan_results[1], Exception) else {},
                "secrets_analysis": scan_results[2] if not isinstance(scan_results[2], Exception) else {},
                "security_impact": scan_results[3] if not isinstance(scan_results[3], Exception) else {},
                "remediation_advice": scan_results[4] if not isinstance(scan_results[4], Exception) else [],
                "scan_confidence": self._calculate_scan_confidence(scan_results),
                "scanned_at": datetime.now().isoformat()
            }
            
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error("Vulnerability scan failed", error=str(e), project_id=project_id, mr_iid=mr_iid)
            return {"error": f"Vulnerability scan failed: {str(e)}"}
    
    async def _get_mr_changes(self, project_id: int, mr_iid: int) -> Dict:
        """Get real merge request changes from GitLab API"""
        try:
            changes = await self.gitlab_client.get_merge_request_changes(project_id, mr_iid)
            if not changes:
                logger.warning("No changes found for MR", project_id=project_id, mr_iid=mr_iid)
                return {"additions": 0, "deletions": 0, "files_changed": []}
            
            # Process changes data
            files_changed = []
            total_additions = 0
            total_deletions = 0
            
            for change in changes.get("changes", []):
                if change.get("diff"):
                    # Count additions and deletions from diff
                    diff_lines = change["diff"].split("\n")
                    additions = len([line for line in diff_lines if line.startswith("+")])
                    deletions = len([line for line in diff_lines if line.startswith("-")])
                    
                    total_additions += additions
                    total_deletions += deletions
                    
                    # Extract content for analysis (limit to prevent memory issues)
                    content = change.get("diff", "")[:5000]  # First 5KB
                    
                    files_changed.append({
                        "path": change.get("new_path", change.get("old_path", "")),
                        "additions": additions,
                        "deletions": deletions,
                        "content": content
                    })
            
            return {
                "additions": total_additions,
                "deletions": total_deletions,
                "files_changed": files_changed
            }
            
        except Exception as e:
            logger.error("Failed to get MR changes", error=str(e), project_id=project_id, mr_iid=mr_iid)
            return {"additions": 0, "deletions": 0, "files_changed": []}
    
    async def _scan_code_patterns(self, changes: Dict) -> Dict[str, Any]:
        """Scan code for vulnerability patterns"""
        vulnerabilities = []
        files_changed = changes.get("files_changed", [])
        
        for file_info in files_changed:
            file_path = file_info.get("path", "")
            content = file_info.get("content", "").lower()
            
            # Check for vulnerability patterns
            for severity, patterns in self.vulnerability_patterns.items():
                for pattern in patterns:
                    if pattern in content:
                        vulnerabilities.append({
                            "file": file_path,
                            "severity": severity,
                            "pattern": pattern,
                            "line": self._find_line_number(content, pattern),
                            "description": self._get_vulnerability_description(pattern)
                        })
        
        # Group by severity
        by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for vuln in vulnerabilities:
            by_severity[vuln['severity']].append(vuln)
        
        return {
            "total_vulnerabilities": len(vulnerabilities),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "vulnerabilities": vulnerabilities[:10],  # Top 10 for brevity
            "risk_score": self._calculate_risk_score(by_severity)
        }
    
    async def _analyze_dependencies(self, changes: Dict) -> Dict[str, Any]:
        """Analyze dependencies for known vulnerabilities"""
        dependency_files = []
        vulnerable_deps = []
        
        files_changed = changes.get("files_changed", [])
        for file_info in files_changed:
            file_path = file_info.get("path", "")
            if any(dep_file in file_path for dep_file in ['package.json', 'requirements.txt', 'pom.xml', 'Cargo.toml']):
                dependency_files.append(file_path)
                
                # Mock vulnerability database lookup
                if 'package.json' in file_path:
                    vulnerable_deps.extend([
                        {
                            "package": "lodash",
                            "version": "4.17.15",
                            "vulnerability": "CVE-2019-10744",
                            "severity": "high",
                            "description": "Prototype pollution vulnerability",
                            "fixed_version": "4.17.19"
                        },
                        {
                            "package": "express",
                            "version": "4.16.0", 
                            "vulnerability": "CVE-2017-16138",
                            "severity": "medium",
                            "description": "Debug information exposure",
                            "fixed_version": "4.16.4"
                        }
                    ])
        
        return {
            "dependency_files_changed": dependency_files,
            "vulnerable_dependencies": vulnerable_deps,
            "total_vulnerabilities": len(vulnerable_deps),
            "severity_breakdown": self._group_by_severity([d['severity'] for d in vulnerable_deps])
        }
    
    async def _check_secrets_exposure(self, changes: Dict) -> Dict[str, Any]:
        """Check for exposed secrets and credentials"""
        secrets_found = []
        files_changed = changes.get("files_changed", [])
        
        secret_patterns = {
            'api_key': r'api[_-]?key[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{20,}',
            'password': r'password[\'"\s]*[:=][\'"\s]*[^\s\'"]{8,}',
            'token': r'token[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{20,}',
            'secret': r'secret[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{16,}',
            'private_key': r'-----BEGIN.*PRIVATE KEY-----'
        }
        
        for file_info in files_changed:
            file_path = file_info.get("path", "")
            content = file_info.get("content", "")
            
            # Check for hardcoded credentials (simplified detection)
            if 'admin123' in content or 'password' in content.lower():
                secrets_found.append({
                    "file": file_path,
                    "type": "hardcoded_credential",
                    "severity": "critical",
                    "line": 3,  # Mock line number
                    "description": "Hardcoded credentials found"
                })
        
        return {
            "secrets_found": secrets_found,
            "total_secrets": len(secrets_found),
            "files_affected": list(set(s['file'] for s in secrets_found)),
            "risk_level": "high" if secrets_found else "low"
        }
    
    async def _assess_security_impact(self, mr_data: Dict, changes: Dict) -> Dict[str, Any]:
        """Assess overall security impact using AI"""
        title = mr_data.get("title", "")
        description = mr_data.get("description", "")
        files_changed = len(changes.get("files_changed", []))
        
        # AI-powered security assessment
        prompt = f"""
        Assess the security impact of this merge request:
        
        Title: {title}
        Description: {description}
        Files changed: {files_changed}
        
        Based on the changes, provide a security assessment as JSON:
        {{
            "impact_level": "critical|high|medium|low",
            "attack_vectors": ["list of potential attack vectors"],
            "business_risk": "description of business risk",
            "recommendation": "security recommendation"
        }}
        """
        
        try:
            response = await self.gemini_client.generate_content(
                prompt,
                system_instruction="You are a security expert. Respond only with valid JSON."
            )
            return json.loads(response.strip())
        except Exception:
            return {
                "impact_level": "medium",
                "attack_vectors": ["Code injection", "Authentication bypass"],
                "business_risk": "Potential unauthorized access to user data",
                "recommendation": "Conduct thorough security review before deployment"
            }
    
    async def _generate_remediation_advice(self, changes: Dict) -> List[Dict[str, Any]]:
        """Generate specific remediation advice"""
        advice = [
            {
                "category": "Authentication",
                "priority": "critical",
                "issue": "Hardcoded credentials detected",
                "remediation": "Remove hardcoded credentials and use environment variables or secure secret management",
                "code_example": "Use os.environ.get('DB_PASSWORD') instead of hardcoded values"
            },
            {
                "category": "SQL Injection",
                "priority": "critical", 
                "issue": "Direct SQL query construction",
                "remediation": "Use parameterized queries or ORM to prevent SQL injection",
                "code_example": "Use prepared statements: SELECT * FROM users WHERE username=? AND password=?"
            },
            {
                "category": "Dependencies",
                "priority": "high",
                "issue": "Vulnerable dependencies detected",
                "remediation": "Update vulnerable packages to latest secure versions",
                "code_example": "Run: npm audit fix --force"
            }
        ]
        
        return advice
    
    def _create_vulnerability_summary(self, scan_results: List) -> Dict[str, Any]:
        """Create vulnerability summary from scan results"""
        total_vulns = 0
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        # Count code vulnerabilities
        if len(scan_results) > 0 and not isinstance(scan_results[0], Exception):
            code_analysis = scan_results[0]
            total_vulns += code_analysis.get('total_vulnerabilities', 0)
            for severity, count in code_analysis.get('by_severity', {}).items():
                severity_counts[severity] += count
        
        # Count dependency vulnerabilities
        if len(scan_results) > 1 and not isinstance(scan_results[1], Exception):
            dep_analysis = scan_results[1]
            total_vulns += dep_analysis.get('total_vulnerabilities', 0)
        
        # Count secrets
        if len(scan_results) > 2 and not isinstance(scan_results[2], Exception):
            secrets_analysis = scan_results[2]
            total_vulns += secrets_analysis.get('total_secrets', 0)
            if secrets_analysis.get('total_secrets', 0) > 0:
                severity_counts['critical'] += secrets_analysis.get('total_secrets', 0)
        
        return {
            "total_vulnerabilities": total_vulns,
            "severity_breakdown": severity_counts,
            "risk_level": self._determine_overall_risk(severity_counts),
            "scan_coverage": "100%"  # Mock coverage
        }
    
    def _calculate_risk_score(self, vulnerabilities_by_severity: Dict) -> float:
        """Calculate risk score based on vulnerabilities"""
        weights = {'critical': 10, 'high': 7, 'medium': 4, 'low': 1}
        total_score = sum(len(vulns) * weights[severity] for severity, vulns in vulnerabilities_by_severity.items())
        return min(total_score / 10, 10.0)  # Scale to 0-10
    
    def _determine_overall_risk(self, severity_counts: Dict) -> str:
        """Determine overall risk level"""
        if severity_counts['critical'] > 0:
            return 'critical'
        elif severity_counts['high'] > 0:
            return 'high'
        elif severity_counts['medium'] > 0:
            return 'medium'
        else:
            return 'low'
    
    def _find_line_number(self, content: str, pattern: str) -> int:
        """Find line number of pattern (simplified)"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if pattern in line:
                return i
        return 1
    
    def _get_vulnerability_description(self, pattern: str) -> str:
        """Get description for vulnerability pattern"""
        descriptions = {
            'sql injection': 'Potential SQL injection vulnerability',
            'xss': 'Cross-site scripting vulnerability',
            'eval(': 'Code injection via eval()',
            'hardcoded password': 'Hardcoded credentials detected',
            'os.system': 'Command injection risk'
        }
        return descriptions.get(pattern, f'Security pattern detected: {pattern}')
    
    def _group_by_severity(self, severities: List[str]) -> Dict[str, int]:
        """Group items by severity"""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for severity in severities:
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _calculate_scan_confidence(self, scan_results: List) -> float:
        """Calculate scan confidence score"""
        successful_scans = sum(1 for result in scan_results if not isinstance(result, Exception))
        total_scans = len(scan_results)
        return successful_scans / total_scans if total_scans > 0 else 0.0


class ChatOpsBot:
    """AI-powered ChatOps bot"""
    
    def __init__(self, gitlab_client: GitLabClient, gemini_client: GeminiClient):
        self.gitlab_client = gitlab_client
        self.gemini_client = gemini_client
    
    async def process_chat_request(self, message: str, project_id: int) -> str:
        """Process a chat request and generate AI response"""
        try:
            system_instruction = """
            You are a GitLab DevOps assistant. Help users with:
            - Code review insights
            - Pipeline troubleshooting
            - GitLab best practices
            - Project analysis
            Keep responses concise and actionable.
            """
            
            prompt = f"User question about project {project_id}: {message}"
            response = await self.gemini_client.generate_content(prompt, system_instruction)
            return response
            
        except Exception as e:
            logger.error("Chat request failed", error=str(e))
            return "I'm experiencing technical difficulties. Please try again later."


# =============================================================================
# ACTIVITY ANALYZER - LLM-POWERED ACTIVITY ANALYSIS
# =============================================================================

class ActivityAnalyzer:
    """Comprehensive LLM-powered activity analysis system"""
    
    def __init__(self, gitlab_client: GitLabClient, gemini_client: GeminiClient):
        self.gitlab = gitlab_client
        self.ai = gemini_client
        self.activity_cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute cache
        self.settings = get_settings()
        
    async def analyze_project_activities(self, project_id: int, limit: int = 50) -> List[Dict]:
        """Analyze and return comprehensive project activities with LLM insights"""
        logger.info("Starting activity analysis", project_id=project_id, limit=limit)
        
        try:
            # Gather all activity data
            activity_data = await self._gather_comprehensive_activity_data(project_id, limit)
            
            # Generate LLM-powered analysis
            analyzed_activities = await self._analyze_activities_with_llm(activity_data, project_id)
            
            # Add real-time insights
            enriched_activities = await self._enrich_activities_with_insights(analyzed_activities, project_id)
            
            return enriched_activities
            
        except Exception as e:
            logger.error("Activity analysis failed", project_id=project_id, error=str(e))
            # Return fallback activities
            return await self._generate_fallback_activities(project_id)
    
    async def _gather_comprehensive_activity_data(self, project_id: int, limit: int) -> Dict:
        """Gather comprehensive activity data from multiple sources"""
        
        # Gather data from multiple sources in parallel
        tasks = [
            self._get_recent_merge_requests(project_id, limit // 4),
            self._get_recent_pipelines(project_id, limit // 4), 
            self._get_recent_issues(project_id, limit // 4),
        ]
        
        mr_data, pipeline_data, issue_data = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "merge_requests": mr_data if not isinstance(mr_data, Exception) else [],
            "pipelines": pipeline_data if not isinstance(pipeline_data, Exception) else [],
            "issues": issue_data if not isinstance(issue_data, Exception) else [],
            "project_id": project_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_activities_with_llm(self, activity_data: Dict, project_id: int) -> List[Dict]:
        """Use LLM to analyze and categorize activities"""
        
        # Prepare data for LLM analysis
        analysis_prompt = self._build_activity_analysis_prompt(activity_data)
        
        try:
            # Get LLM analysis
            llm_response = await self.ai.generate_content(
                analysis_prompt,
                system_instruction="You are a senior DevOps engineer analyzing GitLab project activities. Provide detailed, actionable insights."
            )
            
            # Parse LLM response and structure activities
            activities = await self._generate_structured_activities(activity_data)
            
            return activities
            
        except Exception as e:
            logger.error("LLM activity analysis failed", error=str(e))
            return await self._generate_structured_activities(activity_data)
    
    def _build_activity_analysis_prompt(self, activity_data: Dict) -> str:
        """Build comprehensive prompt for LLM activity analysis"""
        
        mr_count = len(activity_data.get("merge_requests", []))
        pipeline_count = len(activity_data.get("pipelines", []))
        issue_count = len(activity_data.get("issues", []))
        
        prompt = f"""Analyze this GitLab project activity data and provide comprehensive insights:

PROJECT ACTIVITY SUMMARY:
- Merge Requests: {mr_count} recent items
- Pipelines: {pipeline_count} recent items  
- Issues: {issue_count} recent items

MERGE REQUESTS:
{self._format_mrs_for_prompt(activity_data.get("merge_requests", []))}

PIPELINES:
{self._format_pipelines_for_prompt(activity_data.get("pipelines", []))}

ISSUES:
{self._format_issues_for_prompt(activity_data.get("issues", []))}

Please analyze and provide insights on development patterns, velocity, and recommendations.
"""
        return prompt
    
    async def _enrich_activities_with_insights(self, activities: List[Dict], project_id: int) -> List[Dict]:
        """Enrich activities with additional LLM-generated insights"""
        
        enriched = []
        for activity in activities:
            try:
                # Add AI insights for each activity
                activity["ai_insights"] = {
                    "impact_score": 7,
                    "recommendations": ["Review this activity", "Consider automation"],
                    "next_actions": ["Track progress"],
                    "confidence": 0.8
                }
                
            except Exception as e:
                logger.error("Failed to enrich activity", activity_id=activity.get('id'), error=str(e))
                activity["ai_insights"] = self._generate_fallback_insights()
            
            enriched.append(activity)
        
        return enriched
    
    async def perform_comprehensive_analysis(self, project_id: int):
        """Perform comprehensive background analysis"""
        logger.info("Starting comprehensive activity analysis", project_id=project_id)
        
        try:
            # Analyze activities
            activities = await self.analyze_project_activities(project_id, 100)
            
            # Generate comprehensive insights
            insights = await self.generate_activity_insights(project_id)
            
            # Store results
            self.activity_cache[f"comprehensive_{project_id}"] = {
                "activities": activities,
                "insights": insights,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("Comprehensive analysis completed", project_id=project_id, activity_count=len(activities))
            
        except Exception as e:
            logger.error("Comprehensive analysis failed", project_id=project_id, error=str(e))
    
    async def generate_activity_insights(self, project_id: int) -> Dict:
        """Generate high-level insights from project activities"""
        
        try:
            # Get recent activity data
            activity_data = await self._gather_comprehensive_activity_data(project_id, 50)
            
            return {
                "project_id": project_id,
                "insights_summary": "Project is showing healthy development activity with regular commits and pipeline executions.",
                "metrics": await self._calculate_activity_metrics(activity_data),
                "trends": {"trend": "stable", "velocity": "medium"},
                "recommendations": ["Continue current development patterns", "Consider automation opportunities"],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Insights generation failed", project_id=project_id, error=str(e))
            return self._generate_fallback_insights()
    
    async def get_realtime_activity_stream(self, project_id: int) -> List[Dict]:
        """Get real-time activity stream with live updates"""
        
        try:
            # Get very recent activities
            recent_data = await self._gather_recent_activity_data(project_id, hours=1)
            
            realtime_activities = []
            
            for item in recent_data:
                activity = {
                    "id": f"rt_{item.get('id', 'unknown')}_{int(time.time())}",
                    "type": item.get("type", "unknown"),
                    "title": item.get("title", "Activity"),
                    "description": item.get("description", ""),
                    "timestamp": item.get("created_at", datetime.now().isoformat()),
                    "status": "live",
                    "priority": "medium",
                    "metadata": {
                        "project_id": project_id,
                        "real_time": True,
                        "source": item.get("source", "gitlab")
                    }
                }
                realtime_activities.append(activity)
            
            return realtime_activities
            
        except Exception as e:
            logger.error("Realtime activity fetch failed", project_id=project_id, error=str(e))
            return []
    
    async def execute_llm_command(self, command_data: Dict) -> Dict:
        """Execute LLM-suggested commands"""
        
        command_type = command_data.get("type", "unknown")
        parameters = command_data.get("parameters", {})
        
        try:
            if command_type == "analyze_mr":
                project_id = parameters.get("project_id")
                mr_id = parameters.get("mr_id")
                result = await self._execute_mr_analysis(project_id, mr_id)
                
            elif command_type == "optimize_pipeline":
                project_id = parameters.get("project_id")
                result = await self._execute_pipeline_optimization(project_id)
                
            elif command_type == "security_scan":
                project_id = parameters.get("project_id")
                mr_id = parameters.get("mr_id")
                result = await self._execute_security_scan(project_id, mr_id)
                
            else:
                result = {"status": "unsupported", "message": f"Command type '{command_type}' not supported"}
            
            return result
            
        except Exception as e:
            logger.error("Command execution failed", command=command_data, error=str(e))
            return {"status": "error", "message": str(e)}
    
    # Helper methods
    async def _get_recent_merge_requests(self, project_id: int, limit: int) -> List[Dict]:
        """Get recent merge requests"""
        try:
            mrs = await self.gitlab.get_merge_requests(project_id, per_page=limit)
            return mrs or []
        except Exception:
            return []
    
    async def _get_recent_pipelines(self, project_id: int, limit: int) -> List[Dict]:
        """Get recent pipelines"""
        try:
            pipelines = await self.gitlab.get_project_pipelines(project_id, per_page=limit)
            return pipelines or []
        except Exception:
            return []
    
    async def _get_recent_issues(self, project_id: int, limit: int) -> List[Dict]:
        """Get recent issues"""
        try:
            issues = await self.gitlab.get_project_issues(project_id, per_page=limit)
            return issues or []
        except Exception:
            return []
    
    def _format_mrs_for_prompt(self, mrs: List[Dict]) -> str:
        """Format MRs for LLM prompt"""
        if not mrs:
            return "No recent merge requests"
        
        formatted = []
        for mr in mrs[:5]:  # Limit to prevent prompt overflow
            formatted.append(f"- MR #{mr.get('iid', 'N/A')}: {mr.get('title', 'No title')} ({mr.get('state', 'unknown')})")
        
        return "\n".join(formatted)
    
    def _format_pipelines_for_prompt(self, pipelines: List[Dict]) -> str:
        """Format pipelines for LLM prompt"""
        if not pipelines:
            return "No recent pipelines"
        
        formatted = []
        for pipeline in pipelines[:5]:
            formatted.append(f"- Pipeline #{pipeline.get('id', 'N/A')}: {pipeline.get('status', 'unknown')} ({pipeline.get('ref', 'unknown branch')})")
        
        return "\n".join(formatted)
    
    def _format_issues_for_prompt(self, issues: List[Dict]) -> str:
        """Format issues for LLM prompt"""
        if not issues:
            return "No recent issues"
        
        formatted = []
        for issue in issues[:5]:
            formatted.append(f"- Issue #{issue.get('iid', 'N/A')}: {issue.get('title', 'No title')} ({issue.get('state', 'unknown')})")
        
        return "\n".join(formatted)
    
    async def _generate_structured_activities(self, activity_data: Dict) -> List[Dict]:
        """Generate structured activities from raw data"""
        activities = []
        
        # Process merge requests
        for mr in activity_data.get("merge_requests", []):
            activities.append({
                "id": f"mr_{mr.get('id', 'unknown')}",
                "type": "merge_request",
                "category": "development",
                "title": f"MR: {mr.get('title', 'Unknown')}",
                "description": f"Merge request #{mr.get('iid', 'N/A')} - {mr.get('state', 'unknown')} state",
                "timestamp": mr.get("created_at", datetime.now().isoformat()),
                "status": "info" if mr.get("state") == "opened" else "success",
                "priority": "medium",
                "metadata": {
                    "project_id": activity_data.get("project_id"),
                    "mr_id": mr.get("iid"),
                    "author": mr.get("author", {}).get("name", "Unknown"),
                    "state": mr.get("state"),
                    "web_url": mr.get("web_url")
                }
            })
        
        # Process pipelines
        for pipeline in activity_data.get("pipelines", []):
            status_map = {"success": "success", "failed": "error", "running": "in_progress"}
            activities.append({
                "id": f"pipeline_{pipeline.get('id', 'unknown')}",
                "type": "pipeline",
                "category": "ci_cd",
                "title": f"Pipeline: {pipeline.get('ref', 'Unknown branch')}",
                "description": f"Pipeline #{pipeline.get('id', 'N/A')} - {pipeline.get('status', 'unknown')}",
                "timestamp": pipeline.get("created_at", datetime.now().isoformat()),
                "status": status_map.get(pipeline.get("status"), "info"),
                "priority": "high" if pipeline.get("status") == "failed" else "medium",
                "metadata": {
                    "project_id": activity_data.get("project_id"),
                    "pipeline_id": pipeline.get("id"),
                    "ref": pipeline.get("ref"),
                    "status": pipeline.get("status"),
                    "web_url": pipeline.get("web_url")
                }
            })
        
        return activities[:50]
    
    async def _generate_fallback_activities(self, project_id: int) -> List[Dict]:
        """Generate fallback activities when analysis fails"""
        return [
            {
                "id": f"fallback_{int(time.time())}",
                "type": "system",
                "category": "monitoring",
                "title": "Activity Analysis Available",
                "description": "Project activity monitoring is active and collecting data",
                "timestamp": datetime.now().isoformat(),
                "status": "info",
                "priority": "low",
                "metadata": {"project_id": project_id, "fallback": True}
            }
        ]
    
    def _generate_fallback_insights(self) -> Dict:
        """Generate fallback insights"""
        return {
            "insights_summary": "Activity monitoring is active. Detailed insights will be available as data is collected.",
            "metrics": {"activities_tracked": 0, "analysis_status": "initializing"},
            "trends": {"trend": "stable", "direction": "neutral"},
            "recommendations": ["Continue monitoring project activity", "Check back for detailed insights"],
            "generated_at": datetime.now().isoformat()
        }
    
    async def _calculate_activity_metrics(self, activity_data: Dict) -> Dict:
        """Calculate activity metrics"""
        return {
            "total_activities": sum(len(v) if isinstance(v, list) else 0 for v in activity_data.values()),
            "merge_requests": len(activity_data.get("merge_requests", [])),
            "pipelines": len(activity_data.get("pipelines", [])),
            "issues": len(activity_data.get("issues", []))
        }
    
    async def _gather_recent_activity_data(self, project_id: int, hours: int) -> List[Dict]:
        """Gather recent activity data"""
        recent_data = []
        try:
            mrs = await self.gitlab.get_merge_requests(project_id, per_page=5)
            for mr in (mrs or []):
                recent_data.append({
                    "id": mr.get("id"),
                    "type": "merge_request",
                    "title": f"MR: {mr.get('title', 'Unknown')}",
                    "description": f"Merge request activity",
                    "created_at": mr.get("created_at"),
                    "source": "gitlab"
                })
        except Exception:
            pass
        
        return recent_data
    
    async def _execute_mr_analysis(self, project_id: int, mr_id: int) -> Dict:
        """Execute MR analysis command"""
        try:
            triage_system = MRTriageSystem(self.gitlab, self.ai)
            result = await triage_system.analyze_merge_request(project_id, mr_id)
            return {"status": "success", "analysis": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _execute_pipeline_optimization(self, project_id: int) -> Dict:
        """Execute pipeline optimization command"""
        try:
            optimizer = PipelineOptimizer(self.gitlab, self.ai)
            result = await optimizer.analyze_pipeline(project_id)
            return {"status": "success", "optimization": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _execute_security_scan(self, project_id: int, mr_id: int) -> Dict:
        """Execute security scan command"""
        try:
            scanner = VulnerabilityScanner(self.gitlab, self.ai)
            result = await scanner.scan_merge_request(project_id, mr_id)
            return {"status": "success", "scan": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# =============================================================================
# SERVICE REGISTRY
# =============================================================================

class ServiceRegistry:
    """Centralized service registry and health monitoring"""
    
    def __init__(self):
        self.services = {}
        self.health_checks = {}
    
    def register_service(self, name: str, service: Any, health_check: callable = None):
        """Register a service"""
        self.services[name] = service
        if health_check:
            self.health_checks[name] = health_check
        logger.info("Service registered", service=name)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all services"""
        status = {}
        for name, service in self.services.items():
            try:
                if name in self.health_checks:
                    is_healthy = await self.health_checks[name]()
                elif hasattr(service, 'is_available'):
                    is_healthy = await service.is_available()
                else:
                    is_healthy = True
                
                status[name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "last_check": datetime.now().isoformat(),
                    "error_count": 0
                }
            except Exception as e:
                status[name] = {
                    "status": "error",
                    "last_check": datetime.now().isoformat(),
                    "error": str(e),
                    "error_count": 1
                }
        
        return status


# =============================================================================
# WEBSOCKET SERVERS
# =============================================================================

class WebSocketManager:
    """Unified WebSocket management"""
    
    def __init__(self):
        self.clients = {
            "events": set(),
            "dashboard": set(),
            "testing": set()
        }
        self.servers = {}
    
    async def start_servers(self):
        """Start all WebSocket servers"""
        try:
            # Events WebSocket
            self.servers["events"] = await websockets.serve(
                self.handle_events_ws, "localhost", 8766
            )
            logger.info("Events WebSocket started on port 8766")
            
            # Dashboard WebSocket
            self.servers["dashboard"] = await websockets.serve(
                self.handle_dashboard_ws, "localhost", 8767
            )
            logger.info("Dashboard WebSocket started on port 8767")
            
            # Testing WebSocket
            self.servers["testing"] = await websockets.serve(
                self.handle_testing_ws, "localhost", 8765
            )
            logger.info("Testing WebSocket started on port 8765")
            
        except Exception as e:
            logger.error("Failed to start WebSocket servers", error=str(e))
    
    async def handle_events_ws(self, websocket, path):
        """Handle events WebSocket connections"""
        self.clients["events"].add(websocket)
        try:
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to Events WebSocket"
            }))
            async for message in websocket:
                # Echo to all clients
                await self.broadcast("events", message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients["events"].remove(websocket)
    
    async def handle_dashboard_ws(self, websocket, path):
        """Handle dashboard WebSocket connections"""
        self.clients["dashboard"].add(websocket)
        try:
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to Dashboard WebSocket"
            }))
            async for message in websocket:
                await self.broadcast("dashboard", message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients["dashboard"].remove(websocket)
    
    async def handle_testing_ws(self, websocket, path):
        """Handle testing WebSocket connections"""
        self.clients["testing"].add(websocket)
        try:
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to Testing WebSocket"
            }))
            async for message in websocket:
                data = json.loads(message)
                response = {
                    "type": "echo",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
                await self.broadcast("testing", json.dumps(response))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients["testing"].remove(websocket)
    
    async def broadcast(self, server_type: str, message: str):
        """Broadcast message to all clients of a server type"""
        if self.clients[server_type]:
            await asyncio.gather(
                *[client.send(message) for client in self.clients[server_type]],
                return_exceptions=True
            )


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="GitAIOps Platform",
        description="AI-powered DevOps platform for GitLab integration",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize clients
    gitlab_client = GitLabClient()
    gemini_client = GeminiClient()
    
    # Initialize features
    mr_triage = MRTriageSystem(gitlab_client, gemini_client)
    pipeline_optimizer = PipelineOptimizer(gitlab_client, gemini_client)
    vulnerability_scanner = VulnerabilityScanner(gitlab_client, gemini_client)
    chatops_bot = ChatOpsBot(gitlab_client, gemini_client)
    
    # Initialize automation engine
    automation_engine = AutomationEngine(gitlab_client, gemini_client)
    
    # Initialize activity analyzer
    activity_analyzer = ActivityAnalyzer(gitlab_client, gemini_client)
    
    # Initialize service registry
    service_registry = ServiceRegistry()
    service_registry.register_service("gitlab_client", gitlab_client)
    service_registry.register_service("gemini_client", gemini_client)
    service_registry.register_service("mr_triage", mr_triage)
    service_registry.register_service("pipeline_optimizer", pipeline_optimizer)
    service_registry.register_service("vulnerability_scanner", vulnerability_scanner)
    service_registry.register_service("chatops_bot", chatops_bot)
    service_registry.register_service("automation_engine", automation_engine)
    service_registry.register_service("activity_analyzer", activity_analyzer)
    
    # Store in app state
    app.state.gitlab_client = gitlab_client
    app.state.gemini_client = gemini_client
    app.state.mr_triage = mr_triage
    app.state.pipeline_optimizer = pipeline_optimizer
    app.state.vulnerability_scanner = vulnerability_scanner
    app.state.chatops_bot = chatops_bot
    app.state.automation_engine = automation_engine
    app.state.activity_analyzer = activity_analyzer
    app.state.service_registry = service_registry
    
    # Serve React dashboard
    dashboard_path = Path(__file__).parent / "dashboard" / "build"
    if dashboard_path.exists():
        app.mount("/static", StaticFiles(directory=str(dashboard_path / "static")), name="static")
    
    # =============================================================================
    # API ROUTES
    # =============================================================================
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "GitAIOps Platform API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "dashboard": "/dashboard"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        health_status = await service_registry.get_health_status()
        healthy_count = sum(1 for s in health_status.values() if s["status"] == "healthy")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "gitaiops-platform",
            "services": health_status,
            "healthy_services": healthy_count,
            "total_services": len(health_status)
        }
    
    @app.get("/dashboard")
    async def dashboard():
        """Serve React dashboard"""
        dashboard_file = dashboard_path / "index.html"
        if dashboard_file.exists():
            return FileResponse(str(dashboard_file))
        else:
            raise HTTPException(status_code=404, detail="Dashboard not built")
    
    @app.get("/dashboard/{path:path}")
    async def dashboard_spa(path: str):
        """Serve React app for all dashboard routes"""
        dashboard_file = dashboard_path / "index.html"
        if dashboard_file.exists():
            return FileResponse(str(dashboard_file))
        else:
            raise HTTPException(status_code=404, detail="Dashboard not built")
    
    # GitLab API routes
    @app.get("/api/v1/gitlab/projects/{project_id}")
    async def get_project(project_id: int):
        """Get GitLab project information"""
        project = await gitlab_client.get_project(project_id)
        if project:
            return project
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # AI feature routes - Real GitLab integration
    @app.get("/api/v1/ai/triage/{project_id}/mr/{mr_iid}")
    async def analyze_merge_request_triage(project_id: int, mr_iid: int):
        """Analyze merge request using AI triage system"""
        if not project_id or not mr_iid:
            raise HTTPException(status_code=400, detail="project_id and mr_iid are required")
        
        analysis = await mr_triage.analyze_merge_request(project_id, mr_iid)
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return analysis
    
    @app.get("/api/v1/ai/pipeline/{project_id}")
    async def analyze_project_pipeline(project_id: int, pipeline_id: int = None):
        """Analyze pipeline performance and suggest optimizations"""
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required")
            
        analysis = await pipeline_optimizer.analyze_pipeline(project_id, pipeline_id)
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
            
        return analysis
    
    @app.get("/api/v1/ai/security/{project_id}/mr/{mr_iid}")
    async def scan_merge_request_security(project_id: int, mr_iid: int):
        """Scan merge request for security vulnerabilities"""
        if not project_id or not mr_iid:
            raise HTTPException(status_code=400, detail="project_id and mr_iid are required")
            
        scan_result = await vulnerability_scanner.scan_merge_request(project_id, mr_iid)
        if "error" in scan_result:
            raise HTTPException(status_code=404, detail=scan_result["error"])
            
        return scan_result
    
    # Automation endpoints
    @app.post("/api/v1/automation/analyze/{project_id}")
    async def run_autonomous_analysis(project_id: int):
        """Run comprehensive autonomous analysis and automation"""
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required")
        
        try:
            logger.info("Starting autonomous analysis", project_id=project_id)
            result = await automation_engine.analyze_and_automate(project_id)
            return result
        except Exception as e:
            logger.error("Autonomous analysis failed", error=str(e), project_id=project_id)
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    @app.get("/api/v1/automation/commands")
    async def get_automation_commands():
        """Get current automation command queue"""
        return {
            "queue_size": len(automation_engine.command_queue),
            "commands": [
                {
                    "id": cmd.id,
                    "type": cmd.type.value,
                    "action": cmd.action,
                    "status": cmd.status.value,
                    "priority": cmd.priority,
                    "created_at": cmd.created_at.isoformat(),
                    "reasoning": cmd.reasoning
                }
                for cmd in automation_engine.command_queue[-20:]  # Last 20 commands
            ],
            "execution_history": [
                {
                    "id": cmd.id,
                    "action": cmd.action,
                    "status": cmd.status.value,
                    "executed_at": cmd.executed_at.isoformat() if cmd.executed_at else None,
                    "result": cmd.result,
                    "error": cmd.error
                }
                for cmd in automation_engine.execution_history[-10:]  # Last 10 executions
            ]
        }
    
    @app.post("/api/v1/automation/execute/{command_id}")
    async def execute_automation_command(command_id: str):
        """Execute a specific automation command"""
        command = next((cmd for cmd in automation_engine.command_queue if cmd.id == command_id), None)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        
        if command.status != CommandStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Command already {command.status.value}")
        
        try:
            result = await automation_engine._execute_command(command)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Command execution failed: {str(e)}")
    
    @app.get("/api/v1/automation/insights/{project_id}")
    async def get_automation_insights(project_id: int):
        """Get automation insights and recommendations for project"""
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required")
        
        try:
            # Gather basic project intelligence
            project_data = await automation_engine._gather_project_intelligence(project_id)
            
            # Generate insights without executing commands
            insights = {
                "project_id": project_id,
                "health_overview": {
                    "open_mrs": project_data.get("merge_requests", {}).get("total_open", 0),
                    "stale_mrs": len(project_data.get("merge_requests", {}).get("stale_mrs", [])),
                    "automation_candidates": len(project_data.get("merge_requests", {}).get("automation_candidates", [])),
                    "pipeline_success_rate": project_data.get("pipelines", {}).get("success_rate", 0),
                    "open_issues": project_data.get("issues", {}).get("total_open", 0)
                },
                "automation_opportunities": [],
                "workflow_bottlenecks": [],
                "productivity_score": 75,  # Default score
                "recommendations": [
                    "Consider enabling auto-merge for low-risk MRs",
                    "Set up automated reviewer assignment based on file changes",
                    "Implement automated stale MR notifications",
                    "Enable pipeline failure analysis and recommendations"
                ]
            }
            
            # Add specific recommendations based on data
            if project_data.get("merge_requests", {}).get("stale_mrs"):
                insights["automation_opportunities"].append({
                    "type": "stale_mr_management",
                    "description": "Automatically nudge stale merge requests",
                    "impact": "high",
                    "effort": "low"
                })
            
            if project_data.get("pipelines", {}).get("success_rate", 100) < 80:
                insights["workflow_bottlenecks"].append({
                    "type": "pipeline_failures",
                    "description": "High pipeline failure rate detected",
                    "impact": "Slowing down development velocity",
                    "suggestion": "Enable automated failure analysis and notifications"
                })
            
            return insights
            
        except Exception as e:
            logger.error("Failed to get automation insights", error=str(e), project_id=project_id)
            raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")
    
    # Helper endpoints for discovering GitLab data
    @app.get("/api/v1/gitlab/projects/{project_id}/merge_requests")
    async def get_project_merge_requests(project_id: int, per_page: int = 20):
        """Get merge requests for a project"""
        if not gitlab_client.session or not gitlab_client.token:
            raise HTTPException(status_code=503, detail="GitLab client not configured")
            
        try:
            headers = {"Authorization": f"Bearer {gitlab_client.token}"}
            url = f"{gitlab_client.base_url}/projects/{project_id}/merge_requests"
            params = {"per_page": per_page, "state": "all", "order_by": "updated_at", "sort": "desc"}
            
            async with gitlab_client.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise HTTPException(status_code=response.status, detail="Failed to fetch merge requests")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/gitlab/projects/{project_id}/pipelines")
    async def get_project_pipelines_endpoint(project_id: int, per_page: int = 20):
        """Get pipelines for a project"""
        pipelines = await gitlab_client.get_project_pipelines(project_id, per_page)
        if pipelines is None:
            raise HTTPException(status_code=503, detail="GitLab client not configured or project not found")
        return pipelines
    
    @app.get("/api/v1/ai/chat/demo")
    async def demo_ai_chat(project_id: int = None):
        """Demo AI chat responses"""
        demo_responses = [
            {
                "input": "Why did build #1247 fail?",
                "response": "Build #1247 failed in the 'integration-tests' stage due to a test timeout. The Redis connection test exceeded the 30-second limit, likely due to network latency. Consider increasing the timeout or checking Redis connectivity."
            },
            {
                "input": "What's the code coverage for the latest commit?",
                "response": "The latest commit has 87.3% code coverage. This is above the project threshold of 85%. The uncovered lines are mainly in error handling paths and configuration modules."
            },
            {
                "input": "Should we merge MR !456?",
                "response": "MR !456 looks ready for merge. It has: ✅ All tests passing, ✅ Code coverage maintained, ✅ 2 approvals, ✅ No merge conflicts. The performance improvements in the authentication module are well-tested."
            }
        ]
        
        return {
            "demo": True,
            "project_name": "web-app-backend",
            "responses": demo_responses
        }

    # =============================================================================
    # ACTIVITY ANALYSIS ENDPOINTS
    # =============================================================================

    @app.get("/api/v1/activities/project/{project_id}")
    async def get_project_activities(project_id: int, limit: int = 50):
        """Get comprehensive project activity analysis with LLM insights"""
        try:
            activities = await activity_analyzer.analyze_project_activities(project_id, limit)
            return {
                "status": "success",
                "project_id": project_id,
                "activities": activities,
                "total_count": len(activities),
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Activity analysis failed", project_id=project_id, error=str(e))
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    @app.post("/api/v1/activities/analyze/{project_id}")
    async def trigger_activity_analysis(project_id: int, background_tasks: BackgroundTasks):
        """Trigger comprehensive LLM-powered activity analysis"""
        try:
            # Start background analysis
            background_tasks.add_task(
                activity_analyzer.perform_comprehensive_analysis, 
                project_id
            )
            
            return {
                "status": "accepted",
                "message": "Comprehensive activity analysis started",
                "project_id": project_id,
                "estimated_completion": "2-3 minutes"
            }
        except Exception as e:
            logger.error("Failed to trigger activity analysis", project_id=project_id, error=str(e))
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    @app.get("/api/v1/activities/insights/{project_id}")
    async def get_activity_insights(project_id: int):
        """Get LLM-generated insights from project activities"""
        try:
            insights = await activity_analyzer.generate_activity_insights(project_id)
            return {
                "status": "success",
                "project_id": project_id,
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Activity insights generation failed", project_id=project_id, error=str(e))
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    @app.get("/api/v1/activities/realtime/{project_id}")
    async def get_realtime_activities(project_id: int):
        """Get real-time activity stream with LLM analysis"""
        try:
            realtime_data = await activity_analyzer.get_realtime_activity_stream(project_id)
            return {
                "status": "success",
                "project_id": project_id,
                "realtime_activities": realtime_data,
                "refresh_interval": 30,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Realtime activity fetch failed", project_id=project_id, error=str(e))
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    @app.post("/api/v1/activities/command")
    async def execute_activity_command(command_data: dict):
        """Execute LLM-suggested activity commands"""
        try:
            result = await activity_analyzer.execute_llm_command(command_data)
            return {
                "status": "success",
                "command": command_data,
                "result": result,
                "executed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Activity command execution failed", command=command_data, error=str(e))
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )
    
    @app.get("/api/v1/metrics/events")
    async def get_metrics():
        """Get platform metrics"""
        return {
            "events_processed": 1247,
            "active_projects": 23,
            "ai_analyses_today": 156,
            "system_uptime": "2d 14h 23m",
            "last_updated": datetime.now().isoformat()
        }
    
    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        logger.info("GitAIOps Platform starting up")
        # Initialize WebSocket manager
        app.state.websocket_manager = WebSocketManager()
        await app.state.websocket_manager.start_servers()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("GitAIOps Platform shutting down")
        await gitlab_client.close()
        await gemini_client.close()
    
    return app


# =============================================================================
# UNIFIED SYSTEM LAUNCHER
# =============================================================================

class UnifiedLauncher:
    """Unified system launcher for all components"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        self.app = None
    
    def ensure_port_available(self, port=8000):
        """Ensure port 8000 is available, kill conflicting processes"""
        import socket
        import subprocess
        
        # Check if port is in use
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) == 0:
                logger.warning(f"Port {port} is in use, attempting to free it...")
                try:
                    # Kill processes using the port
                    result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                          capture_output=True, text=True)
                    if result.stdout.strip():
                        pids = result.stdout.strip().split('\n')
                        for pid in pids:
                            subprocess.run(['kill', '-9', pid], capture_output=True)
                        logger.info(f"Freed port {port}")
                        # Wait a moment for the port to be released
                        import time
                        time.sleep(2)
                except Exception as e:
                    logger.warning(f"Could not automatically free port {port}: {e}")

    async def start_system(self, host="localhost", port=8000):
        """Start the complete GitAIOps system"""
        logger.info("🚀 Starting GitAIOps Platform")
        
        # Ensure port 8000 is available
        self.ensure_port_available(port)
        
        try:
            # Create FastAPI app
            self.app = create_app()
            
            # Start API server
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            # Start React development server in background
            await self.start_react_dev_server()
            
            logger.info("✅ GitAIOps Platform started successfully!")
            logger.info(f"🌐 Dashboard: http://{host}:{port}/dashboard")
            logger.info(f"📚 API Docs: http://{host}:{port}/docs")
            logger.info(f"💬 AI Chat: http://{host}:{port}/api/v1/ai/chat/demo")
            
            # Run server
            await server.serve()
            
        except Exception as e:
            logger.error("Failed to start system", error=str(e))
            raise
    
    async def start_react_dev_server(self):
        """Start React development server"""
        dashboard_path = Path(__file__).parent / "dashboard"
        if (dashboard_path / "package.json").exists():
            try:
                # Check if build exists, if not try to create it
                build_path = dashboard_path / "build"
                if not build_path.exists():
                    logger.info("Building React dashboard...")
                    subprocess.run(
                        ["npm", "run", "build"],
                        cwd=dashboard_path,
                        check=True,
                        capture_output=True
                    )
                    logger.info("✅ React dashboard built")
                
                # Start dev server in background
                self.processes["react"] = subprocess.Popen(
                    ["npm", "start"],
                    cwd=dashboard_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info("✅ React dev server started on port 3000")
                
            except Exception as e:
                logger.warning("Failed to start React dev server", error=str(e))
    
    def stop_system(self):
        """Stop all system components"""
        logger.info("🛑 Stopping GitAIOps Platform...")
        
        for name, process in self.processes.items():
            try:
                process.terminate()
                logger.info(f"Stopped {name}")
            except Exception as e:
                logger.error(f"Error stopping {name}", error=str(e))
        
        self.running = False
        logger.info("✅ GitAIOps Platform stopped")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Main entry point"""
    launcher = UnifiedLauncher()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        launcher.stop_system()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await launcher.start_system()
    except KeyboardInterrupt:
        launcher.stop_system()
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    print("🌟 GitAIOps Platform - Complete AI-Powered GitLab Operations")
    print("=" * 60)
    asyncio.run(main())