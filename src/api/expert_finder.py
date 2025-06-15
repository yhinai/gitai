"""
Expert Finder API Routes

RESTful API for CodeCompass expert finder functionality.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from src.features.codecompass_expert_finder import (
    get_expert_finder,
    ExpertQuery,
    ExpertiseLevel,
    Expert,
    ExpertiseAnalysis
)
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Request/Response Models
class ExpertSearchRequest(BaseModel):
    """Expert search request"""
    query: str = Field(..., description="Natural language query for finding experts")
    project_id: Optional[int] = Field(None, description="GitLab project ID")
    technologies: Optional[List[str]] = Field(None, description="Specific technologies")
    file_paths: Optional[List[str]] = Field(None, description="Specific file paths")
    min_expertise: str = Field("intermediate", description="Minimum expertise level")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of experts to return")

class ExpertResponse(BaseModel):
    """Expert information response"""
    username: str
    name: str
    email: str
    avatar_url: Optional[str]
    expertise_score: float
    relevant_skills: List[Dict[str, Any]]
    recent_contributions: List[Dict[str, Any]]
    availability_status: str
    timezone: Optional[str]
    preferred_contact: Optional[str]

class ExpertiseAnalysisResponse(BaseModel):
    """Expertise analysis response"""
    primary_experts: List[ExpertResponse]
    secondary_experts: List[ExpertResponse]
    knowledge_gaps: List[str]
    recommendations: List[str]
    confidence_score: float

class KnowledgeGraphBuildRequest(BaseModel):
    """Knowledge graph build request"""
    project_id: int = Field(..., description="GitLab project ID")
    full_scan: bool = Field(False, description="Perform full project scan")

class DeveloperProfileResponse(BaseModel):
    """Developer profile response"""
    developer: Dict[str, Any]
    expertise: Dict[str, Any]

# Routes
@router.post("/experts/search", response_model=ExpertiseAnalysisResponse)
async def search_experts(request: ExpertSearchRequest):
    """
    Search for experts using natural language query
    
    Find developers with expertise in specific technologies, files, or skills.
    Uses AI-powered analysis and knowledge graph to identify the best experts.
    """
    
    try:
        expert_finder = await get_expert_finder()
        
        # Convert expertise level
        try:
            min_expertise = ExpertiseLevel(request.min_expertise.lower())
        except ValueError:
            min_expertise = ExpertiseLevel.INTERMEDIATE
        
        # Create query object
        query = ExpertQuery(
            query=request.query,
            project_id=request.project_id,
            technologies=request.technologies,
            file_paths=request.file_paths,
            min_expertise=min_expertise,
            limit=request.limit
        )
        
        # Find experts
        analysis = await expert_finder.find_experts(query)
        
        # Convert to response format
        return ExpertiseAnalysisResponse(
            primary_experts=[_expert_to_response(e) for e in analysis.primary_experts],
            secondary_experts=[_expert_to_response(e) for e in analysis.secondary_experts],
            knowledge_gaps=analysis.knowledge_gaps,
            recommendations=analysis.recommendations,
            confidence_score=analysis.confidence_score
        )
        
    except Exception as e:
        logger.error(
            "Expert search failed",
            query=request.query,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Expert search failed: {str(e)}"
        )

@router.get("/experts/technologies/{technology}", response_model=List[ExpertResponse])
async def get_technology_experts(
    technology: str,
    min_expertise: str = Query("intermediate", description="Minimum expertise level"),
    limit: int = Query(10, ge=1, le=50, description="Maximum experts to return")
):
    """
    Get experts for a specific technology
    
    Find developers with expertise in a particular technology or framework.
    """
    
    try:
        expert_finder = await get_expert_finder()
        
        # Convert expertise level
        try:
            min_expertise_level = ExpertiseLevel(min_expertise.lower())
        except ValueError:
            min_expertise_level = ExpertiseLevel.INTERMEDIATE
        
        # Create query
        query = ExpertQuery(
            query=f"experts in {technology}",
            technologies=[technology],
            min_expertise=min_expertise_level,
            limit=limit
        )
        
        # Find experts
        analysis = await expert_finder.find_experts(query)
        
        # Return all experts (primary + secondary)
        all_experts = analysis.primary_experts + analysis.secondary_experts
        return [_expert_to_response(e) for e in all_experts[:limit]]
        
    except Exception as e:
        logger.error(
            "Technology expert search failed",
            technology=technology,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Technology expert search failed: {str(e)}"
        )

@router.get("/experts/files", response_model=List[ExpertResponse])
async def get_file_experts(
    file_path: str = Query(..., description="File path to find experts for"),
    project_id: int = Query(..., description="GitLab project ID"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get experts for a specific file or module
    
    Find developers who have the most experience with a particular file or code module.
    """
    
    try:
        expert_finder = await get_expert_finder()
        
        # Create query
        query = ExpertQuery(
            query=f"experts for file {file_path}",
            project_id=project_id,
            file_paths=[file_path],
            limit=limit
        )
        
        # Find experts
        analysis = await expert_finder.find_experts(query)
        
        # Return all experts
        all_experts = analysis.primary_experts + analysis.secondary_experts
        return [_expert_to_response(e) for e in all_experts[:limit]]
        
    except Exception as e:
        logger.error(
            "File expert search failed",
            file_path=file_path,
            project_id=project_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"File expert search failed: {str(e)}"
        )

@router.get("/developers/{username}/profile", response_model=DeveloperProfileResponse)
async def get_developer_profile(username: str):
    """
    Get complete expertise profile for a developer
    
    Returns comprehensive information about a developer's skills, expertise areas,
    and contribution history.
    """
    
    try:
        expert_finder = await get_expert_finder()
        
        if not expert_finder.knowledge_graph_ready:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph not available"
            )
        
        # Get profile from Neo4j
        profile = await expert_finder._neo4j_client.get_developer_expertise_profile(username)
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Developer '{username}' not found"
            )
        
        return DeveloperProfileResponse(
            developer=profile["developer"],
            expertise=profile["expertise"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Developer profile retrieval failed",
            username=username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get developer profile: {str(e)}"
        )

@router.get("/developers/{username}/similar", response_model=List[Dict[str, Any]])
async def get_similar_developers(
    username: str,
    limit: int = Query(10, ge=1, le=20)
):
    """
    Find developers with similar expertise
    
    Identifies other developers who work with similar technologies and have
    overlapping skill sets.
    """
    
    try:
        expert_finder = await get_expert_finder()
        
        if not expert_finder.knowledge_graph_ready:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph not available"
            )
        
        # Find similar developers
        similar_devs = await expert_finder._neo4j_client.find_similar_experts(
            username=username,
            limit=limit
        )
        
        return similar_devs
        
    except Exception as e:
        logger.error(
            "Similar developers search failed",
            username=username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Similar developers search failed: {str(e)}"
        )

@router.post("/knowledge-graph/build")
async def build_knowledge_graph(
    request: KnowledgeGraphBuildRequest,
    background_tasks: BackgroundTasks
):
    """
    Build or update knowledge graph for a project
    
    Processes project commits, merge requests, and contributions to build
    a comprehensive expertise knowledge graph.
    """
    
    try:
        expert_finder = await get_expert_finder()
        
        if not expert_finder.knowledge_graph_ready:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph not available"
            )
        
        # Run knowledge graph building in background
        background_tasks.add_task(
            expert_finder.build_knowledge_graph,
            request.project_id,
            request.full_scan
        )
        
        return {
            "status": "accepted",
            "message": f"Knowledge graph build started for project {request.project_id}",
            "project_id": request.project_id,
            "full_scan": request.full_scan
        }
        
    except Exception as e:
        logger.error(
            "Knowledge graph build request failed",
            project_id=request.project_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge graph build failed: {str(e)}"
        )

@router.get("/knowledge-graph/stats")
async def get_knowledge_graph_stats():
    """
    Get knowledge graph statistics
    
    Returns information about the current state of the knowledge graph,
    including node counts and relationship statistics.
    """
    
    try:
        expert_finder = await get_expert_finder()
        stats = await expert_finder.get_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats
        }
        
    except Exception as e:
        logger.error("Knowledge graph stats retrieval failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get knowledge graph stats: {str(e)}"
        )

@router.get("/experts/demo")
async def demo_expert_search():
    """
    Demo expert search functionality
    
    Provides sample expert search results for demonstration purposes.
    """
    
    try:
        expert_finder = await get_expert_finder()
        
        # Demo search for Python experts
        demo_query = ExpertQuery(
            query="Who are the Python experts in this project?",
            technologies=["python"],
            min_expertise=ExpertiseLevel.INTERMEDIATE,
            limit=5
        )
        
        # Get analysis
        analysis = await expert_finder.find_experts(demo_query)
        
        return {
            "demo": True,
            "query": "Python experts search",
            "analysis": {
                "primary_experts_count": len(analysis.primary_experts),
                "secondary_experts_count": len(analysis.secondary_experts),
                "knowledge_gaps": analysis.knowledge_gaps,
                "recommendations": analysis.recommendations,
                "confidence_score": analysis.confidence_score
            },
            "sample_experts": [
                _expert_to_response(expert) 
                for expert in analysis.primary_experts[:3]
            ]
        }
        
    except Exception as e:
        logger.error("Demo expert search failed", error=str(e))
        
        # Return fallback demo response
        return {
            "demo": True,
            "query": "Python experts search",
            "status": "fallback",
            "message": "Knowledge graph not available - showing sample data",
            "sample_experts": [
                {
                    "username": "alice_dev",
                    "name": "Alice Johnson",
                    "email": "alice@example.com",
                    "avatar_url": None,
                    "expertise_score": 0.95,
                    "relevant_skills": [
                        {"name": "python", "level": "expert", "confidence": 0.9},
                        {"name": "django", "level": "advanced", "confidence": 0.8},
                        {"name": "fastapi", "level": "intermediate", "confidence": 0.7}
                    ],
                    "recent_contributions": [
                        {"type": "commit", "count": 150, "last_30_days": 25}
                    ],
                    "availability_status": "available",
                    "timezone": "UTC-8",
                    "preferred_contact": "alice@example.com"
                },
                {
                    "username": "bob_backend",
                    "name": "Bob Smith",
                    "email": "bob@example.com", 
                    "avatar_url": None,
                    "expertise_score": 0.87,
                    "relevant_skills": [
                        {"name": "python", "level": "advanced", "confidence": 0.85},
                        {"name": "postgresql", "level": "expert", "confidence": 0.9},
                        {"name": "redis", "level": "intermediate", "confidence": 0.6}
                    ],
                    "recent_contributions": [
                        {"type": "commit", "count": 120, "last_30_days": 18}
                    ],
                    "availability_status": "busy",
                    "timezone": "UTC-5",
                    "preferred_contact": "bob@example.com"
                }
            ],
            "knowledge_gaps": ["Limited ML/AI expertise in Python stack"],
            "recommendations": [
                "Consider training in advanced Python frameworks",
                "Pair programming sessions for knowledge transfer"
            ],
            "confidence_score": 0.8
        }

# Helper Functions
def _expert_to_response(expert: Expert) -> ExpertResponse:
    """Convert Expert object to response model"""
    
    return ExpertResponse(
        username=expert.username,
        name=expert.name,
        email=expert.email,
        avatar_url=expert.avatar_url,
        expertise_score=expert.expertise_score,
        relevant_skills=expert.relevant_skills,
        recent_contributions=expert.recent_contributions,
        availability_status=expert.availability_status,
        timezone=expert.timezone,
        preferred_contact=expert.preferred_contact
    )