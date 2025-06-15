"""
Neo4j Integration Client

Provides async interface for Neo4j graph database operations
for the CodeCompass expert finder system.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import structlog
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import Neo4jError
import hashlib
import json
from dataclasses import dataclass, asdict
from enum import Enum

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

class ExpertiseLevel(Enum):
    """Developer expertise levels"""
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class DeveloperNode:
    """Developer node in knowledge graph"""
    id: str
    username: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    total_commits: int = 0
    total_mrs: int = 0
    total_reviews: int = 0
    active_since: Optional[datetime] = None
    last_active: Optional[datetime] = None

@dataclass
class TechnologyNode:
    """Technology/skill node in knowledge graph"""
    id: str
    name: str
    category: str  # language, framework, tool, etc.
    ecosystem: Optional[str] = None  # npm, pypi, maven, etc.

@dataclass
class FileNode:
    """File/module node in knowledge graph"""
    id: str
    path: str
    project_id: int
    language: Optional[str] = None
    module_type: Optional[str] = None  # controller, service, model, etc.
    complexity_score: float = 0.0
    last_modified: Optional[datetime] = None

@dataclass
class ExpertiseEdge:
    """Expertise relationship between developer and technology/file"""
    developer_id: str
    target_id: str  # technology_id or file_id
    expertise_level: ExpertiseLevel
    confidence_score: float
    contribution_count: int
    last_contribution: datetime
    contribution_types: List[str]  # commits, reviews, etc.

class Neo4jClient:
    """Async Neo4j client for knowledge graph operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self._driver: Optional[AsyncDriver] = None
        self._initialized = False
        
        # Connection settings
        self.uri = self.settings.NEO4J_URI or "bolt://localhost:7687"
        self.username = self.settings.NEO4J_USERNAME or "neo4j"
        self.password = self.settings.NEO4J_PASSWORD or "password"
        self.database = self.settings.NEO4J_DATABASE or "neo4j"
        
    async def initialize(self):
        """Initialize Neo4j connection and create indexes"""
        if self._initialized:
            return
            
        try:
            logger.info("Initializing Neo4j connection", uri=self.uri)
            
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            
            # Verify connection
            await self._driver.verify_connectivity()
            
            # Create indexes and constraints
            await self._create_indexes()
            
            self._initialized = True
            logger.info("Neo4j connection initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Neo4j", error=str(e))
            raise
    
    async def close(self):
        """Close Neo4j connection"""
        if self._driver:
            await self._driver.close()
            self._initialized = False
            logger.info("Neo4j connection closed")
    
    async def _create_indexes(self):
        """Create indexes and constraints for optimal performance"""
        indexes = [
            # Developer indexes
            "CREATE INDEX dev_username IF NOT EXISTS FOR (d:Developer) ON (d.username)",
            "CREATE INDEX dev_email IF NOT EXISTS FOR (d:Developer) ON (d.email)",
            "CREATE CONSTRAINT dev_id IF NOT EXISTS FOR (d:Developer) REQUIRE d.id IS UNIQUE",
            
            # Technology indexes
            "CREATE INDEX tech_name IF NOT EXISTS FOR (t:Technology) ON (t.name)",
            "CREATE INDEX tech_category IF NOT EXISTS FOR (t:Technology) ON (t.category)",
            "CREATE CONSTRAINT tech_id IF NOT EXISTS FOR (t:Technology) REQUIRE t.id IS UNIQUE",
            
            # File indexes
            "CREATE INDEX file_path IF NOT EXISTS FOR (f:File) ON (f.path)",
            "CREATE INDEX file_project IF NOT EXISTS FOR (f:File) ON (f.project_id)",
            "CREATE CONSTRAINT file_id IF NOT EXISTS FOR (f:File) REQUIRE f.id IS UNIQUE",
            
            # Relationship indexes
            "CREATE INDEX rel_expertise_level IF NOT EXISTS FOR ()-[e:HAS_EXPERTISE]->() ON (e.expertise_level)",
            "CREATE INDEX rel_confidence IF NOT EXISTS FOR ()-[e:HAS_EXPERTISE]->() ON (e.confidence_score)",
            "CREATE INDEX rel_owns_confidence IF NOT EXISTS FOR ()-[o:OWNS]->() ON (o.ownership_score)"
        ]
        
        async with self._driver.session(database=self.database) as session:
            for index_query in indexes:
                try:
                    await session.run(index_query)
                except Neo4jError as e:
                    # Ignore if index already exists
                    if "already exists" not in str(e):
                        logger.warning(f"Failed to create index: {index_query}", error=str(e))
    
    # Developer operations
    async def create_or_update_developer(self, developer: DeveloperNode) -> str:
        """Create or update developer node"""
        query = """
        MERGE (d:Developer {id: $id})
        SET d.username = $username,
            d.email = $email,
            d.name = $name,
            d.avatar_url = $avatar_url,
            d.total_commits = $total_commits,
            d.total_mrs = $total_mrs,
            d.total_reviews = $total_reviews,
            d.active_since = $active_since,
            d.last_active = $last_active,
            d.updated_at = datetime()
        RETURN d.id as id
        """
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(
                query,
                id=developer.id,
                username=developer.username,
                email=developer.email,
                name=developer.name,
                avatar_url=developer.avatar_url,
                total_commits=developer.total_commits,
                total_mrs=developer.total_mrs,
                total_reviews=developer.total_reviews,
                active_since=developer.active_since.isoformat() if developer.active_since else None,
                last_active=developer.last_active.isoformat() if developer.last_active else None
            )
            record = await result.single()
            return record["id"]
    
    async def get_developer_by_username(self, username: str) -> Optional[DeveloperNode]:
        """Get developer by username"""
        query = """
        MATCH (d:Developer {username: $username})
        RETURN d
        """
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, username=username)
            record = await result.single()
            
            if not record:
                return None
                
            data = dict(record["d"])
            return DeveloperNode(
                id=data["id"],
                username=data["username"],
                email=data["email"],
                name=data["name"],
                avatar_url=data.get("avatar_url"),
                total_commits=data.get("total_commits", 0),
                total_mrs=data.get("total_mrs", 0),
                total_reviews=data.get("total_reviews", 0),
                active_since=datetime.fromisoformat(data["active_since"]) if data.get("active_since") else None,
                last_active=datetime.fromisoformat(data["last_active"]) if data.get("last_active") else None
            )
    
    # Technology operations
    async def create_or_update_technology(self, technology: TechnologyNode) -> str:
        """Create or update technology node"""
        query = """
        MERGE (t:Technology {id: $id})
        SET t.name = $name,
            t.category = $category,
            t.ecosystem = $ecosystem,
            t.updated_at = datetime()
        RETURN t.id as id
        """
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(
                query,
                id=technology.id,
                name=technology.name,
                category=technology.category,
                ecosystem=technology.ecosystem
            )
            record = await result.single()
            return record["id"]
    
    # File operations
    async def create_or_update_file(self, file: FileNode) -> str:
        """Create or update file node"""
        query = """
        MERGE (f:File {id: $id})
        SET f.path = $path,
            f.project_id = $project_id,
            f.language = $language,
            f.module_type = $module_type,
            f.complexity_score = $complexity_score,
            f.last_modified = $last_modified,
            f.updated_at = datetime()
        RETURN f.id as id
        """
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(
                query,
                id=file.id,
                path=file.path,
                project_id=file.project_id,
                language=file.language,
                module_type=file.module_type,
                complexity_score=file.complexity_score,
                last_modified=file.last_modified.isoformat() if file.last_modified else None
            )
            record = await result.single()
            return record["id"]
    
    # Expertise relationships
    async def create_or_update_expertise(self, expertise: ExpertiseEdge):
        """Create or update expertise relationship"""
        query = """
        MATCH (d:Developer {id: $developer_id})
        MATCH (target) WHERE target.id = $target_id
        MERGE (d)-[e:HAS_EXPERTISE]->(target)
        SET e.expertise_level = $expertise_level,
            e.confidence_score = $confidence_score,
            e.contribution_count = $contribution_count,
            e.last_contribution = $last_contribution,
            e.contribution_types = $contribution_types,
            e.updated_at = datetime()
        RETURN e
        """
        
        async with self._driver.session(database=self.database) as session:
            await session.run(
                query,
                developer_id=expertise.developer_id,
                target_id=expertise.target_id,
                expertise_level=expertise.expertise_level.value,
                confidence_score=expertise.confidence_score,
                contribution_count=expertise.contribution_count,
                last_contribution=expertise.last_contribution.isoformat(),
                contribution_types=expertise.contribution_types
            )
    
    # Query operations
    async def find_experts_for_technology(
        self, 
        technology_name: str, 
        min_expertise: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find experts for a specific technology"""
        query = """
        MATCH (d:Developer)-[e:HAS_EXPERTISE]->(t:Technology)
        WHERE toLower(t.name) CONTAINS toLower($tech_name)
          AND e.expertise_level IN $allowed_levels
          AND e.confidence_score >= 0.5
        RETURN d, e, t
        ORDER BY e.confidence_score DESC, e.contribution_count DESC
        LIMIT $limit
        """
        
        # Get allowed expertise levels
        expertise_order = [ExpertiseLevel.NOVICE, ExpertiseLevel.INTERMEDIATE, 
                          ExpertiseLevel.ADVANCED, ExpertiseLevel.EXPERT]
        min_index = expertise_order.index(min_expertise)
        allowed_levels = [level.value for level in expertise_order[min_index:]]
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(
                query,
                tech_name=technology_name,
                allowed_levels=allowed_levels,
                limit=limit
            )
            
            experts = []
            async for record in result:
                dev_data = dict(record["d"])
                exp_data = dict(record["e"])
                tech_data = dict(record["t"])
                
                experts.append({
                    "developer": {
                        "id": dev_data["id"],
                        "username": dev_data["username"],
                        "name": dev_data["name"],
                        "email": dev_data["email"],
                        "avatar_url": dev_data.get("avatar_url")
                    },
                    "expertise": {
                        "level": exp_data["expertise_level"],
                        "confidence": exp_data["confidence_score"],
                        "contributions": exp_data["contribution_count"],
                        "last_contribution": exp_data["last_contribution"],
                        "contribution_types": exp_data["contribution_types"]
                    },
                    "technology": {
                        "id": tech_data["id"],
                        "name": tech_data["name"],
                        "category": tech_data["category"]
                    }
                })
            
            return experts
    
    async def find_experts_for_file(
        self, 
        file_path: str, 
        project_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find experts for a specific file"""
        query = """
        MATCH (d:Developer)-[o:OWNS]->(f:File)
        WHERE f.path = $file_path AND f.project_id = $project_id
        RETURN d, o, f
        ORDER BY o.ownership_score DESC, o.contribution_count DESC
        LIMIT $limit
        """
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(
                query,
                file_path=file_path,
                project_id=project_id,
                limit=limit
            )
            
            experts = []
            async for record in result:
                dev_data = dict(record["d"])
                own_data = dict(record["o"])
                file_data = dict(record["f"])
                
                experts.append({
                    "developer": {
                        "id": dev_data["id"],
                        "username": dev_data["username"],
                        "name": dev_data["name"],
                        "email": dev_data["email"],
                        "avatar_url": dev_data.get("avatar_url")
                    },
                    "ownership": {
                        "score": own_data["ownership_score"],
                        "contributions": own_data["contribution_count"],
                        "last_contribution": own_data["last_contribution"],
                        "first_contribution": own_data.get("first_contribution")
                    },
                    "file": {
                        "id": file_data["id"],
                        "path": file_data["path"],
                        "language": file_data.get("language"),
                        "module_type": file_data.get("module_type")
                    }
                })
            
            return experts
    
    async def get_developer_expertise_profile(self, username: str) -> Dict[str, Any]:
        """Get complete expertise profile for a developer"""
        query = """
        MATCH (d:Developer {username: $username})
        OPTIONAL MATCH (d)-[e:HAS_EXPERTISE]->(t:Technology)
        OPTIONAL MATCH (d)-[o:OWNS]->(f:File)
        WITH d, 
             COLLECT(DISTINCT {
                 technology: t.name, 
                 category: t.category,
                 level: e.expertise_level,
                 confidence: e.confidence_score,
                 contributions: e.contribution_count
             }) as technologies,
             COLLECT(DISTINCT {
                 file: f.path,
                 ownership: o.ownership_score,
                 contributions: o.contribution_count
             }) as files
        RETURN d, technologies, files
        """
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, username=username)
            record = await result.single()
            
            if not record:
                return None
                
            dev_data = dict(record["d"])
            
            # Filter out null entries
            technologies = [t for t in record["technologies"] if t["technology"]]
            files = [f for f in record["files"] if f["file"]]
            
            # Sort technologies by confidence
            technologies.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Sort files by ownership
            files.sort(key=lambda x: x["ownership"], reverse=True)
            
            return {
                "developer": {
                    "id": dev_data["id"],
                    "username": dev_data["username"],
                    "name": dev_data["name"],
                    "email": dev_data["email"],
                    "avatar_url": dev_data.get("avatar_url"),
                    "stats": {
                        "total_commits": dev_data.get("total_commits", 0),
                        "total_mrs": dev_data.get("total_mrs", 0),
                        "total_reviews": dev_data.get("total_reviews", 0)
                    }
                },
                "expertise": {
                    "technologies": technologies[:20],  # Top 20 technologies
                    "owned_files": files[:20],  # Top 20 owned files
                    "expertise_score": self._calculate_expertise_score(technologies),
                    "primary_languages": self._extract_primary_languages(technologies)
                }
            }
    
    async def find_similar_experts(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find developers with similar expertise"""
        query = """
        MATCH (d1:Developer {username: $username})-[:HAS_EXPERTISE]->(t:Technology)<-[:HAS_EXPERTISE]-(d2:Developer)
        WHERE d1 <> d2
        WITH d1, d2, COUNT(DISTINCT t) as shared_tech
        ORDER BY shared_tech DESC
        LIMIT $limit
        MATCH (d2)-[e:HAS_EXPERTISE]->(tech:Technology)
        WITH d2, shared_tech, COLLECT({
            name: tech.name, 
            level: e.expertise_level,
            confidence: e.confidence_score
        }) as expertise
        RETURN d2, shared_tech, expertise
        """
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, username=username, limit=limit)
            
            similar_experts = []
            async for record in result:
                dev_data = dict(record["d2"])
                
                similar_experts.append({
                    "developer": {
                        "id": dev_data["id"],
                        "username": dev_data["username"],
                        "name": dev_data["name"],
                        "email": dev_data["email"],
                        "avatar_url": dev_data.get("avatar_url")
                    },
                    "similarity": {
                        "shared_technologies": record["shared_tech"],
                        "expertise_overlap": record["expertise"][:10]  # Top 10 skills
                    }
                })
            
            return similar_experts
    
    # Helper methods
    def _calculate_expertise_score(self, technologies: List[Dict]) -> float:
        """Calculate overall expertise score"""
        if not technologies:
            return 0.0
            
        # Weight by expertise level
        level_weights = {
            "expert": 1.0,
            "advanced": 0.7,
            "intermediate": 0.4,
            "novice": 0.1
        }
        
        total_score = 0.0
        for tech in technologies:
            level = tech.get("level", "novice")
            confidence = tech.get("confidence", 0.5)
            contributions = tech.get("contributions", 1)
            
            weight = level_weights.get(level, 0.1)
            score = weight * confidence * min(contributions / 10, 1.0)
            total_score += score
        
        # Normalize to 0-100 scale
        return min(total_score * 10, 100.0)
    
    def _extract_primary_languages(self, technologies: List[Dict]) -> List[str]:
        """Extract primary programming languages"""
        languages = []
        for tech in technologies:
            if tech.get("category") == "language" and tech.get("confidence", 0) > 0.5:
                languages.append(tech["technology"])
        
        return languages[:5]  # Top 5 languages
    
    # Stats and analytics
    async def get_knowledge_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        query = """
        MATCH (d:Developer) WITH COUNT(d) as developer_count
        MATCH (t:Technology) WITH developer_count, COUNT(t) as technology_count
        MATCH (f:File) WITH developer_count, technology_count, COUNT(f) as file_count
        MATCH ()-[e:HAS_EXPERTISE]->() WITH developer_count, technology_count, file_count, COUNT(e) as expertise_edges
        MATCH ()-[o:OWNS]->() WITH developer_count, technology_count, file_count, expertise_edges, COUNT(o) as ownership_edges
        RETURN {
            nodes: {
                developers: developer_count,
                technologies: technology_count,
                files: file_count
            },
            relationships: {
                expertise: expertise_edges,
                ownership: ownership_edges
            }
        } as stats
        """
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query)
            record = await result.single()
            return record["stats"] if record else {
                "nodes": {"developers": 0, "technologies": 0, "files": 0},
                "relationships": {"expertise": 0, "ownership": 0}
            }

# Singleton instance
_neo4j_client: Optional[Neo4jClient] = None

async def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client instance"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
        await _neo4j_client.initialize()
    return _neo4j_client