"""
CodeCompass Expert Finder

AI-powered system for finding code experts and mapping developer expertise
using knowledge graph and natural language queries.
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import structlog
import hashlib
from collections import defaultdict
from pathlib import Path

from src.integrations.gitlab_client import get_gitlab_client
from src.integrations.openrouter_client import get_openrouter_client
from src.integrations.neo4j_client import (
    get_neo4j_client, 
    DeveloperNode, 
    TechnologyNode, 
    FileNode,
    ExpertiseEdge,
    ExpertiseLevel
)
# Cache client - simplified for now
async def get_cache_client():
    return None

logger = structlog.get_logger(__name__)

@dataclass
class ExpertQuery:
    """Natural language query for finding experts"""
    query: str
    project_id: Optional[int] = None
    file_paths: List[str] = None
    technologies: List[str] = None
    min_expertise: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    limit: int = 10

@dataclass
class Expert:
    """Expert developer information"""
    username: str
    name: str
    email: str
    avatar_url: Optional[str]
    expertise_score: float
    relevant_skills: List[Dict[str, Any]]
    recent_contributions: List[Dict[str, Any]]
    availability_status: str  # available, busy, on_leave
    timezone: Optional[str] = None
    preferred_contact: Optional[str] = None

@dataclass
class ExpertiseAnalysis:
    """Analysis of developer expertise"""
    primary_experts: List[Expert]
    secondary_experts: List[Expert]
    knowledge_gaps: List[str]
    recommendations: List[str]
    confidence_score: float

class CodeCompassExpertFinder:
    """Expert finder system using knowledge graph and AI"""
    
    def __init__(self):
        self.gitlab_client = get_gitlab_client()
        self.openrouter_client = get_openrouter_client()
        self.knowledge_graph_ready = False
        self._neo4j_client = None
        self._cache_client = None
        
        # Technology detection patterns
        self.tech_patterns = {
            # Languages
            'python': [r'\.py$', r'requirements\.txt', r'setup\.py', r'pyproject\.toml'],
            'javascript': [r'\.js$', r'\.jsx$', r'package\.json'],
            'typescript': [r'\.ts$', r'\.tsx$', r'tsconfig\.json'],
            'java': [r'\.java$', r'pom\.xml', r'build\.gradle'],
            'go': [r'\.go$', r'go\.mod', r'go\.sum'],
            'rust': [r'\.rs$', r'Cargo\.toml'],
            'ruby': [r'\.rb$', r'Gemfile', r'\.gemspec'],
            'cpp': [r'\.cpp$', r'\.cc$', r'\.cxx$', r'\.hpp$'],
            
            # Frameworks
            'react': [r'react', r'\.jsx$', r'\.tsx$'],
            'vue': [r'vue', r'\.vue$'],
            'angular': [r'angular', r'\.component\.ts$'],
            'django': [r'django', r'manage\.py', r'settings\.py'],
            'flask': [r'flask', r'app\.py'],
            'spring': [r'spring', r'@SpringBoot', r'application\.properties'],
            'fastapi': [r'fastapi', r'uvicorn'],
            
            # Tools & Infrastructure
            'docker': [r'Dockerfile', r'docker-compose', r'\.dockerignore'],
            'kubernetes': [r'\.yaml$', r'kubectl', r'k8s', r'deployment\.yaml'],
            'terraform': [r'\.tf$', r'\.tfvars$'],
            'ansible': [r'playbook\.yml', r'ansible\.cfg'],
            'jenkins': [r'Jenkinsfile', r'\.jenkins'],
            'gitlab-ci': [r'\.gitlab-ci\.yml'],
            
            # Databases
            'postgresql': [r'postgres', r'\.sql$', r'pg_'],
            'mongodb': [r'mongo', r'\.bson', r'mongoose'],
            'redis': [r'redis', r'cache', r'session'],
            'elasticsearch': [r'elastic', r'\.es', r'logstash']
        }
        
        # File type to module mapping
        self.module_patterns = {
            'controller': [r'controller', r'handler', r'route', r'endpoint'],
            'service': [r'service', r'business', r'logic', r'manager'],
            'model': [r'model', r'entity', r'schema', r'domain'],
            'repository': [r'repository', r'dao', r'store', r'persistence'],
            'api': [r'api', r'rest', r'graphql', r'grpc'],
            'test': [r'test', r'spec', r'_test\.', r'\.test\.'],
            'config': [r'config', r'settings', r'env', r'properties'],
            'util': [r'util', r'helper', r'common', r'shared']
        }
    
    async def initialize(self):
        """Initialize expert finder with Neo4j connection"""
        try:
            self._neo4j_client = await get_neo4j_client()
            self._cache_client = await get_cache_client()
            self.knowledge_graph_ready = True
            logger.info("CodeCompass Expert Finder initialized")
        except Exception as e:
            logger.error("Failed to initialize expert finder", error=str(e))
            self.knowledge_graph_ready = False
    
    async def find_experts(self, query: ExpertQuery) -> ExpertiseAnalysis:
        """Find experts based on natural language query"""
        
        logger.info(
            "Finding experts",
            query=query.query,
            project_id=query.project_id,
            technologies=query.technologies,
            file_paths=query.file_paths
        )
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(query)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # Parse query using AI if available
            parsed_query = await self._parse_natural_language_query(query)
            
            # Find experts based on parsed criteria
            experts = await self._find_experts_by_criteria(parsed_query)
            
            # Analyze and rank experts
            analysis = await self._analyze_and_rank_experts(experts, parsed_query)
            
            # Cache result
            await self._cache_result(cache_key, analysis)
            
            logger.info(
                "Expert search completed",
                primary_experts=len(analysis.primary_experts),
                secondary_experts=len(analysis.secondary_experts),
                confidence=analysis.confidence_score
            )
            
            return analysis
            
        except Exception as e:
            logger.error(
                "Expert search failed",
                query=query.query,
                error=str(e),
                exc_info=True
            )
            
            # Return fallback result
            return ExpertiseAnalysis(
                primary_experts=[],
                secondary_experts=[],
                knowledge_gaps=["Unable to analyze expertise at this time"],
                recommendations=["Please try again or refine your query"],
                confidence_score=0.0
            )
    
    async def _parse_natural_language_query(self, query: ExpertQuery) -> Dict[str, Any]:
        """Parse natural language query to extract criteria"""
        
        # Try AI parsing first
        if await self.openrouter_client.is_available():
            try:
                ai_result = await self.openrouter_client.parse_expert_query(query.query)
                if ai_result:
                    return {
                        "technologies": ai_result.get("technologies", []) + (query.technologies or []),
                        "file_paths": ai_result.get("file_paths", []) + (query.file_paths or []),
                        "skills": ai_result.get("skills", []),
                        "experience_level": ai_result.get("experience_level", "intermediate"),
                        "context": ai_result.get("context", ""),
                        "project_id": query.project_id
                    }
            except Exception as e:
                logger.warning("AI query parsing failed", error=str(e))
        
        # Fallback to pattern-based parsing
        parsed = {
            "technologies": query.technologies or [],
            "file_paths": query.file_paths or [],
            "skills": [],
            "experience_level": query.min_expertise.value,
            "context": query.query,
            "project_id": query.project_id
        }
        
        # Extract technologies from query
        query_lower = query.query.lower()
        for tech, patterns in self.tech_patterns.items():
            for pattern in patterns:
                if tech in query_lower or re.search(pattern, query_lower):
                    if tech not in parsed["technologies"]:
                        parsed["technologies"].append(tech)
        
        # Extract file paths
        file_pattern = r'[a-zA-Z0-9_/\-]+\.[a-zA-Z]+'
        potential_files = re.findall(file_pattern, query.query)
        parsed["file_paths"].extend(potential_files)
        
        return parsed
    
    async def _find_experts_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find experts based on parsed criteria"""
        
        experts = []
        
        if not self.knowledge_graph_ready:
            # Fallback to GitLab-based search
            return await self._fallback_gitlab_search(criteria)
        
        # Search by technologies
        if criteria.get("technologies"):
            for tech in criteria["technologies"]:
                tech_experts = await self._neo4j_client.find_experts_for_technology(
                    technology_name=tech,
                    min_expertise=ExpertiseLevel.INTERMEDIATE,
                    limit=20
                )
                experts.extend(tech_experts)
        
        # Search by file paths
        if criteria.get("file_paths") and criteria.get("project_id"):
            for file_path in criteria["file_paths"]:
                file_experts = await self._neo4j_client.find_experts_for_file(
                    file_path=file_path,
                    project_id=criteria["project_id"],
                    limit=20
                )
                experts.extend(file_experts)
        
        # Deduplicate experts
        unique_experts = {}
        for expert in experts:
            dev_id = expert["developer"]["id"]
            if dev_id not in unique_experts:
                unique_experts[dev_id] = expert
            else:
                # Merge expertise information
                self._merge_expert_data(unique_experts[dev_id], expert)
        
        return list(unique_experts.values())
    
    async def _analyze_and_rank_experts(
        self, 
        experts: List[Dict[str, Any]], 
        criteria: Dict[str, Any]
    ) -> ExpertiseAnalysis:
        """Analyze and rank experts based on criteria"""
        
        if not experts:
            return ExpertiseAnalysis(
                primary_experts=[],
                secondary_experts=[],
                knowledge_gaps=self._identify_knowledge_gaps(criteria),
                recommendations=["No experts found. Consider expanding search criteria."],
                confidence_score=0.0
            )
        
        # Score and rank experts
        scored_experts = []
        for expert_data in experts:
            score = await self._calculate_expert_score(expert_data, criteria)
            expert = await self._create_expert_object(expert_data, score)
            scored_experts.append((score, expert))
        
        # Sort by score
        scored_experts.sort(key=lambda x: x[0], reverse=True)
        
        # Separate primary and secondary experts
        primary_threshold = 0.7
        primary_experts = []
        secondary_experts = []
        
        for score, expert in scored_experts:
            if score >= primary_threshold and len(primary_experts) < 5:
                primary_experts.append(expert)
            elif len(secondary_experts) < 5:
                secondary_experts.append(expert)
        
        # Calculate confidence
        confidence = self._calculate_confidence(scored_experts, criteria)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            primary_experts, 
            secondary_experts, 
            criteria
        )
        
        return ExpertiseAnalysis(
            primary_experts=primary_experts,
            secondary_experts=secondary_experts,
            knowledge_gaps=self._identify_knowledge_gaps(criteria),
            recommendations=recommendations,
            confidence_score=confidence
        )
    
    async def _calculate_expert_score(
        self, 
        expert_data: Dict[str, Any], 
        criteria: Dict[str, Any]
    ) -> float:
        """Calculate expert relevance score"""
        
        score = 0.0
        
        # Base score from expertise/ownership
        if "expertise" in expert_data:
            expertise = expert_data["expertise"]
            score += expertise["confidence"] * 0.4
            score += min(expertise["contributions"] / 100, 1.0) * 0.3
            
            # Recency bonus
            last_contrib = datetime.fromisoformat(expertise["last_contribution"])
            days_ago = (datetime.utcnow() - last_contrib).days
            if days_ago < 30:
                score += 0.2
            elif days_ago < 90:
                score += 0.1
        
        elif "ownership" in expert_data:
            ownership = expert_data["ownership"]
            score += ownership["score"] * 0.5
            score += min(ownership["contributions"] / 50, 1.0) * 0.3
        
        # Technology match bonus
        if "technology" in expert_data:
            tech_name = expert_data["technology"]["name"].lower()
            for criteria_tech in criteria.get("technologies", []):
                if criteria_tech.lower() in tech_name:
                    score += 0.1
        
        return min(score, 1.0)
    
    async def _create_expert_object(
        self, 
        expert_data: Dict[str, Any], 
        score: float
    ) -> Expert:
        """Create Expert object from data"""
        
        developer = expert_data["developer"]
        
        # Get full profile from knowledge graph
        profile = None
        if self.knowledge_graph_ready:
            profile = await self._neo4j_client.get_developer_expertise_profile(
                developer["username"]
            )
        
        # Extract relevant skills
        relevant_skills = []
        if profile and "expertise" in profile:
            for tech in profile["expertise"]["technologies"][:5]:
                relevant_skills.append({
                    "name": tech["technology"],
                    "level": tech["level"],
                    "confidence": tech["confidence"]
                })
        
        # Get recent contributions
        recent_contributions = []
        if profile:
            # Would fetch from GitLab API in production
            recent_contributions = [
                {
                    "type": "commit",
                    "count": profile["developer"]["stats"]["total_commits"],
                    "last_30_days": 0  # Would calculate from GitLab
                }
            ]
        
        # Determine availability (simplified)
        availability = "available"  # Would check calendar/status in production
        
        return Expert(
            username=developer["username"],
            name=developer["name"],
            email=developer["email"],
            avatar_url=developer.get("avatar_url"),
            expertise_score=score,
            relevant_skills=relevant_skills,
            recent_contributions=recent_contributions,
            availability_status=availability,
            timezone=None,  # Would fetch from user profile
            preferred_contact=developer["email"]
        )
    
    async def _fallback_gitlab_search(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback search using GitLab API when Neo4j is unavailable"""
        
        experts = []
        
        if not criteria.get("project_id"):
            return experts
        
        try:
            # Get project contributors
            contributors = await self.gitlab_client.get_project_contributors(
                criteria["project_id"],
                limit=50
            )
            
            # Convert to expert format
            for contrib in contributors:
                experts.append({
                    "developer": {
                        "id": str(contrib["id"]),
                        "username": contrib["username"],
                        "name": contrib["name"],
                        "email": contrib.get("email", f"{contrib['username']}@gitlab.com"),
                        "avatar_url": contrib.get("avatar_url")
                    },
                    "expertise": {
                        "confidence": min(contrib.get("commits", 0) / 100, 1.0),
                        "contributions": contrib.get("commits", 0),
                        "last_contribution": datetime.utcnow().isoformat(),
                        "contribution_types": ["commits"]
                    }
                })
        
        except Exception as e:
            logger.error("Fallback GitLab search failed", error=str(e))
        
        return experts
    
    def _merge_expert_data(self, existing: Dict[str, Any], new: Dict[str, Any]):
        """Merge expertise data for the same developer"""
        
        if "expertise" in new and "expertise" not in existing:
            existing["expertise"] = new["expertise"]
        elif "expertise" in new and "expertise" in existing:
            # Combine contribution counts
            existing["expertise"]["contributions"] += new["expertise"]["contributions"]
            # Use highest confidence
            existing["expertise"]["confidence"] = max(
                existing["expertise"]["confidence"],
                new["expertise"]["confidence"]
            )
    
    def _identify_knowledge_gaps(self, criteria: Dict[str, Any]) -> List[str]:
        """Identify knowledge gaps based on search criteria"""
        
        gaps = []
        
        # Check for emerging technologies
        emerging_tech = ["rust", "flutter", "svelte", "deno", "webassembly"]
        for tech in criteria.get("technologies", []):
            if tech.lower() in emerging_tech:
                gaps.append(f"Limited expertise in emerging technology: {tech}")
        
        # Check for specialized areas
        if "security" in criteria.get("context", "").lower():
            gaps.append("Security expertise may require specialized training")
        
        if "performance" in criteria.get("context", "").lower():
            gaps.append("Performance optimization expertise is limited")
        
        return gaps
    
    def _generate_recommendations(
        self,
        primary_experts: List[Expert],
        secondary_experts: List[Expert],
        criteria: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on expert analysis"""
        
        recommendations = []
        
        if not primary_experts:
            recommendations.append("Consider training existing team members in required technologies")
            recommendations.append("Look for external consultants or contractors")
        
        elif len(primary_experts) < 3:
            recommendations.append("Limited expert pool - consider knowledge sharing sessions")
            recommendations.append("Implement pair programming with available experts")
        
        if any(expert.availability_status != "available" for expert in primary_experts):
            recommendations.append("Some experts are busy - plan work allocation accordingly")
        
        # Technology-specific recommendations
        for tech in criteria.get("technologies", []):
            if tech in ["kubernetes", "terraform", "ansible"]:
                recommendations.append(f"Consider DevOps training for {tech}")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _calculate_confidence(
        self, 
        scored_experts: List[Tuple[float, Expert]], 
        criteria: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the analysis"""
        
        if not scored_experts:
            return 0.0
        
        # Base confidence on number and quality of experts
        top_scores = [score for score, _ in scored_experts[:5]]
        
        if not top_scores:
            return 0.0
        
        avg_top_score = sum(top_scores) / len(top_scores)
        
        # Adjust based on criteria complexity
        complexity_factor = 1.0
        if len(criteria.get("technologies", [])) > 3:
            complexity_factor = 0.8
        
        return min(avg_top_score * complexity_factor, 1.0)
    
    # Knowledge graph building methods
    async def build_knowledge_graph(self, project_id: int, full_scan: bool = False):
        """Build or update knowledge graph for a project"""
        
        logger.info(
            "Building knowledge graph",
            project_id=project_id,
            full_scan=full_scan
        )
        
        try:
            # Get project info
            project = await self.gitlab_client.get_project(project_id)
            
            # Process commits
            await self._process_project_commits(project_id, full_scan)
            
            # Process merge requests
            await self._process_project_mrs(project_id, full_scan)
            
            # Process code ownership
            await self._process_code_ownership(project_id)
            
            logger.info(
                "Knowledge graph build completed",
                project_id=project_id
            )
            
        except Exception as e:
            logger.error(
                "Knowledge graph build failed",
                project_id=project_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _process_project_commits(self, project_id: int, full_scan: bool):
        """Process commits to build expertise"""
        
        # Get recent commits (or all if full scan)
        since = None if full_scan else (datetime.utcnow() - timedelta(days=90)).isoformat()
        
        commits = await self.gitlab_client.list_project_commits(
            project_id=project_id,
            since=since,
            per_page=100
        )
        
        for commit in commits:
            # Get commit details
            commit_detail = await self.gitlab_client.get_commit(
                project_id=project_id,
                commit_sha=commit["id"]
            )
            
            # Process developer
            author = commit_detail.get("author")
            if author:
                dev_node = DeveloperNode(
                    id=str(author["id"]),
                    username=author["username"],
                    email=author["email"],
                    name=author["name"],
                    avatar_url=author.get("avatar_url")
                )
                await self._neo4j_client.create_or_update_developer(dev_node)
            
            # Process files and detect technologies
            for file_path in commit_detail.get("file_paths", []):
                await self._process_file_expertise(
                    developer_id=str(author["id"]),
                    file_path=file_path,
                    project_id=project_id,
                    contribution_type="commit"
                )
    
    async def _process_file_expertise(
        self,
        developer_id: str,
        file_path: str,
        project_id: int,
        contribution_type: str
    ):
        """Process file contribution to build expertise"""
        
        # Create file node
        file_id = hashlib.sha256(f"{project_id}:{file_path}".encode()).hexdigest()
        
        # Detect language and module type
        language = self._detect_language(file_path)
        module_type = self._detect_module_type(file_path)
        
        file_node = FileNode(
            id=file_id,
            path=file_path,
            project_id=project_id,
            language=language,
            module_type=module_type
        )
        await self._neo4j_client.create_or_update_file(file_node)
        
        # Detect technologies from file
        technologies = self._detect_technologies(file_path)
        
        # Create technology nodes and expertise edges
        for tech_name in technologies:
            tech_id = hashlib.sha256(tech_name.encode()).hexdigest()
            tech_node = TechnologyNode(
                id=tech_id,
                name=tech_name,
                category=self._categorize_technology(tech_name)
            )
            await self._neo4j_client.create_or_update_technology(tech_node)
            
            # Create expertise edge
            expertise = ExpertiseEdge(
                developer_id=developer_id,
                target_id=tech_id,
                expertise_level=ExpertiseLevel.INTERMEDIATE,  # Would calculate based on contributions
                confidence_score=0.7,  # Would calculate based on frequency
                contribution_count=1,  # Would aggregate
                last_contribution=datetime.utcnow(),
                contribution_types=[contribution_type]
            )
            await self._neo4j_client.create_or_update_expertise(expertise)
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file path"""
        
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.sql': 'sql',
            '.sh': 'bash',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.vue': 'vue',
            '.jsx': 'javascript',
            '.tsx': 'typescript'
        }
        
        path = Path(file_path)
        return ext_map.get(path.suffix.lower())
    
    def _detect_module_type(self, file_path: str) -> Optional[str]:
        """Detect module type from file path"""
        
        path_lower = file_path.lower()
        
        for module_type, patterns in self.module_patterns.items():
            for pattern in patterns:
                if re.search(pattern, path_lower):
                    return module_type
        
        return None
    
    def _detect_technologies(self, file_path: str) -> List[str]:
        """Detect technologies from file path"""
        
        detected = []
        path_lower = file_path.lower()
        
        for tech, patterns in self.tech_patterns.items():
            for pattern in patterns:
                if re.search(pattern, path_lower):
                    detected.append(tech)
                    break
        
        # Also add language as technology
        language = self._detect_language(file_path)
        if language and language not in detected:
            detected.append(language)
        
        return detected
    
    def _categorize_technology(self, tech_name: str) -> str:
        """Categorize technology"""
        
        categories = {
            'language': ['python', 'javascript', 'typescript', 'java', 'go', 'rust', 'ruby', 'cpp'],
            'framework': ['react', 'vue', 'angular', 'django', 'flask', 'spring', 'fastapi'],
            'database': ['postgresql', 'mongodb', 'redis', 'elasticsearch'],
            'infrastructure': ['docker', 'kubernetes', 'terraform', 'ansible'],
            'tool': ['jenkins', 'gitlab-ci', 'github-actions']
        }
        
        for category, techs in categories.items():
            if tech_name.lower() in techs:
                return category
        
        return 'other'
    
    async def _process_project_mrs(self, project_id: int, full_scan: bool):
        """Process merge requests for expertise"""
        
        # Implementation similar to commits
        # Would process MR reviews, approvals, etc.
        pass
    
    async def _process_code_ownership(self, project_id: int):
        """Process code ownership based on contributions"""
        
        # Implementation would calculate ownership scores
        # based on contribution frequency and recency
        pass
    
    # Helper methods
    def _generate_cache_key(self, query: ExpertQuery) -> str:
        """Generate cache key for query"""
        
        key_parts = [
            query.query,
            str(query.project_id),
            ",".join(query.technologies or []),
            ",".join(query.file_paths or []),
            query.min_expertise.value
        ]
        
        key_str = "|".join(key_parts)
        return f"expert_query:{hashlib.sha256(key_str.encode()).hexdigest()}"
    
    async def _get_cached_result(self, cache_key: str) -> Optional[ExpertiseAnalysis]:
        """Get cached result if available"""
        
        if not self._cache_client:
            return None
        
        try:
            cached = await self._cache_client.get(cache_key)
            if cached:
                # Reconstruct ExpertiseAnalysis from cached data
                return ExpertiseAnalysis(**cached)
        except Exception as e:
            logger.warning("Cache retrieval failed", error=str(e))
        
        return None
    
    async def _cache_result(self, cache_key: str, analysis: ExpertiseAnalysis):
        """Cache analysis result"""
        
        if not self._cache_client:
            return
        
        try:
            # Convert to cacheable format
            cache_data = {
                "primary_experts": [self._expert_to_dict(e) for e in analysis.primary_experts],
                "secondary_experts": [self._expert_to_dict(e) for e in analysis.secondary_experts],
                "knowledge_gaps": analysis.knowledge_gaps,
                "recommendations": analysis.recommendations,
                "confidence_score": analysis.confidence_score
            }
            
            await self._cache_client.set(cache_key, cache_data, ttl=3600)  # 1 hour TTL
        except Exception as e:
            logger.warning("Cache storage failed", error=str(e))
    
    def _expert_to_dict(self, expert: Expert) -> Dict[str, Any]:
        """Convert Expert to dictionary"""
        
        return {
            "username": expert.username,
            "name": expert.name,
            "email": expert.email,
            "avatar_url": expert.avatar_url,
            "expertise_score": expert.expertise_score,
            "relevant_skills": expert.relevant_skills,
            "recent_contributions": expert.recent_contributions,
            "availability_status": expert.availability_status,
            "timezone": expert.timezone,
            "preferred_contact": expert.preferred_contact
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get expert finder statistics"""
        
        stats = {
            "knowledge_graph_ready": self.knowledge_graph_ready,
            "supported_technologies": len(self.tech_patterns),
            "module_types": list(self.module_patterns.keys())
        }
        
        if self.knowledge_graph_ready:
            graph_stats = await self._neo4j_client.get_knowledge_graph_stats()
            stats["knowledge_graph"] = graph_stats
        
        return stats

# Global instance
_expert_finder: Optional[CodeCompassExpertFinder] = None

async def get_expert_finder() -> CodeCompassExpertFinder:
    """Get or create expert finder instance"""
    global _expert_finder
    if _expert_finder is None:
        _expert_finder = CodeCompassExpertFinder()
        await _expert_finder.initialize()
    return _expert_finder