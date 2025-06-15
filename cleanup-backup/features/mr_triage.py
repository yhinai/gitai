"""
AI-powered merge request triage system
"""
import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import structlog
import json

from src.integrations.gitlab_client import get_gitlab_client, GitLabAPIError
from src.integrations.gemini_client import get_gemini_client

logger = structlog.get_logger(__name__)

class RiskLevel(Enum):
    """Risk levels for merge requests"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MRType(Enum):
    """Merge request types"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "docs"
    DEPENDENCY = "dependency"
    HOTFIX = "hotfix"

class Complexity(Enum):
    """Code complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"

@dataclass
class MRAnalysis:
    """Merge request analysis result"""
    mr_id: int
    mr_iid: int
    project_id: int
    risk_level: RiskLevel
    risk_score: float  # 0-1.0
    mr_type: MRType
    complexity: Complexity
    estimated_review_hours: float
    risk_factors: List[str]
    suggested_reviewers: List[Dict[str, Any]]
    review_requirements: Dict[str, bool]
    labels: List[str]
    confidence_score: float
    analysis_timestamp: datetime

class MRTriageSystem:
    """AI-powered merge request triage system"""
    
    def __init__(self):
        self.gitlab_client = get_gitlab_client()
        self.gemini_client = get_gemini_client()
        
        # Risk patterns
        self.security_patterns = [
            r'password|secret|key|token|credential|auth',
            r'sql|query|database|db_',
            r'encrypt|decrypt|hash|crypto',
            r'permission|role|access|admin',
            r'security|vulnerability|cve|exploit'
        ]
        
        self.complexity_indicators = [
            r'refactor|redesign|architecture',
            r'migration|upgrade|major',
            r'algorithm|optimization|performance',
            r'threading|async|concurrent',
            r'api|interface|contract'
        ]
        
        # Cache for analysis results
        self.analysis_cache = {}
    
    async def analyze_merge_request(self, project_id: int, mr_iid: int) -> MRAnalysis:
        """Analyze a merge request for risk and complexity"""
        cache_key = f"{project_id}:{mr_iid}"
        
        # Check cache first
        if cache_key in self.analysis_cache:
            cached = self.analysis_cache[cache_key]
            # Return cached if less than 1 hour old
            if (datetime.utcnow() - cached.analysis_timestamp).total_seconds() < 3600:
                return cached
        
        logger.info(
            "Analyzing merge request",
            project_id=project_id,
            mr_iid=mr_iid
        )
        
        try:
            # Fetch MR data
            mr_data = await self.gitlab_client.get_merge_request(project_id, mr_iid)
            if not mr_data:
                raise ValueError(f"Merge request {mr_iid} not found")
            
            # Fetch changes
            changes = await self.gitlab_client.get_merge_request_changes(project_id, mr_iid)
            
            # Perform analysis
            analysis = await self._perform_analysis(mr_data, changes)
            
            # Cache result
            self.analysis_cache[cache_key] = analysis
            
            logger.info(
                "MR analysis completed",
                project_id=project_id,
                mr_iid=mr_iid,
                risk_level=analysis.risk_level.value,
                mr_type=analysis.mr_type.value,
                confidence=analysis.confidence_score
            )
            
            return analysis
            
        except Exception as e:
            logger.error(
                "MR analysis failed",
                project_id=project_id,
                mr_iid=mr_iid,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _perform_analysis(self, mr_data: Dict[str, Any], changes: Dict[str, Any]) -> MRAnalysis:
        """Perform comprehensive MR analysis"""
        
        # Extract basic info
        mr_id = mr_data["id"]
        mr_iid = mr_data["iid"]
        project_id = mr_data["project_id"]
        title = mr_data.get("title", "")
        description = mr_data.get("description", "")
        
        # Try AI analysis first, fall back to pattern-based analysis
        if await self.gemini_client.is_available():
            try:
                logger.info("Using AI-powered MR analysis", mr_iid=mr_iid)
                ai_analysis = await self.gemini_client.analyze_merge_request(
                    mr_data, 
                    changes.get("changes", [])
                )
                return self._convert_ai_analysis(ai_analysis, mr_id, mr_iid, project_id)
            except Exception as e:
                logger.warning("AI analysis failed, using fallback", error=str(e))
        
        # Fallback to pattern-based analysis
        logger.info("Using pattern-based MR analysis", mr_iid=mr_iid)
        risk_analysis = await self._analyze_risk(mr_data, changes)
        type_analysis = await self._analyze_type(mr_data, changes)
        complexity_analysis = await self._analyze_complexity(mr_data, changes)
        reviewer_analysis = await self._suggest_reviewers(mr_data, changes)
        
        # Combine results
        analysis = MRAnalysis(
            mr_id=mr_id,
            mr_iid=mr_iid,
            project_id=project_id,
            risk_level=risk_analysis["level"],
            risk_score=risk_analysis["score"],
            mr_type=type_analysis["type"],
            complexity=complexity_analysis["level"],
            estimated_review_hours=complexity_analysis["hours"],
            risk_factors=risk_analysis["factors"],
            suggested_reviewers=reviewer_analysis["reviewers"],
            review_requirements=self._determine_review_requirements(risk_analysis, type_analysis),
            labels=self._generate_labels(risk_analysis, type_analysis, complexity_analysis),
            confidence_score=min(
                risk_analysis["confidence"],
                type_analysis["confidence"],
                complexity_analysis["confidence"]
            ),
            analysis_timestamp=datetime.utcnow()
        )
        
        return analysis
    
    def _convert_ai_analysis(self, ai_analysis: Dict[str, Any], mr_id: int, mr_iid: int, project_id: int) -> MRAnalysis:
        """Convert AI analysis result to MRAnalysis object"""
        
        # Map AI analysis to our enums and structure
        risk_level_map = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL
        }
        
        mr_type_map = {
            "feature": MRType.FEATURE,
            "bugfix": MRType.BUGFIX,
            "docs": MRType.DOCUMENTATION,
            "security": MRType.SECURITY,
            "refactor": MRType.REFACTOR,
            "refactoring": MRType.REFACTOR,  # Alternative spelling
            "performance": MRType.PERFORMANCE,
            "dependency": MRType.DEPENDENCY,
            "hotfix": MRType.HOTFIX
        }
        
        complexity_map = {
            "simple": Complexity.SIMPLE,
            "moderate": Complexity.MODERATE,
            "complex": Complexity.COMPLEX,
            "very_complex": Complexity.VERY_COMPLEX
        }
        
        # Extract and map values with fallbacks
        risk_level = risk_level_map.get(ai_analysis.get("risk_level", "medium"), RiskLevel.MEDIUM)
        mr_type = mr_type_map.get(ai_analysis.get("mr_type", "feature"), MRType.FEATURE)
        complexity = complexity_map.get(ai_analysis.get("complexity", "moderate"), Complexity.MODERATE)
        
        # Create review requirements from AI analysis
        review_reqs = ai_analysis.get("review_requirements", {})
        review_requirements = {
            "security_review": review_reqs.get("security_review", False),
            "performance_review": review_reqs.get("performance_review", False),
            "architecture_review": review_reqs.get("architecture_review", False),
            "database_review": review_reqs.get("database_review", False)
        }
        
        return MRAnalysis(
            mr_id=mr_id,
            mr_iid=mr_iid,
            project_id=project_id,
            risk_level=risk_level,
            risk_score=ai_analysis.get("risk_score", 0.5),
            mr_type=mr_type,
            complexity=complexity,
            estimated_review_hours=ai_analysis.get("estimated_review_hours", 1.0),
            risk_factors=ai_analysis.get("risk_factors", []),
            suggested_reviewers=[],  # Would need additional logic for reviewer suggestions
            review_requirements=review_requirements,
            labels=ai_analysis.get("suggested_labels", []),
            confidence_score=ai_analysis.get("confidence_score", 0.8),
            analysis_timestamp=datetime.utcnow()
        )
    
    async def _analyze_risk(self, mr_data: Dict[str, Any], changes: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk level of the merge request"""
        risk_factors = []
        risk_score = 0.0
        
        title = mr_data.get("title", "").lower()
        description = mr_data.get("description", "").lower()
        changes_data = changes.get("changes", []) if changes else []
        
        # Check for security-related changes
        security_score = self._check_security_patterns(title, description, changes_data)
        if security_score > 0.3:
            risk_factors.append("Security-sensitive changes detected")
            risk_score += security_score
        
        # Check file types and count
        file_analysis = self._analyze_files(changes_data)
        if file_analysis["high_risk_files"] > 0:
            risk_factors.append(f"Changes to {file_analysis['high_risk_files']} high-risk files")
            risk_score += 0.3
        
        if file_analysis["total_files"] > 20:
            risk_factors.append(f"Large changeset: {file_analysis['total_files']} files")
            risk_score += 0.2
        
        # Check code volume
        additions = mr_data.get("changes_count") or 0
        # Convert to int if it's a string
        try:
            additions = int(additions) if isinstance(additions, str) else additions
        except (ValueError, TypeError):
            additions = 0
            
        if additions > 500:
            risk_factors.append(f"Large code change: {additions} lines")
            risk_score += 0.2
        
        # Check for deletions (potential breaking changes)
        for change in changes_data:
            if change.get("deleted_file", False):
                risk_factors.append("File deletions detected")
                risk_score += 0.1
                break
        
        # Database/migration changes
        if any("migration" in change.get("old_path", "").lower() for change in changes_data):
            risk_factors.append("Database migration changes")
            risk_score += 0.3
        
        # Configuration changes
        config_patterns = ["config", "env", "settings", "dockerfile", "requirements"]
        for change in changes_data:
            path = change.get("old_path", "").lower()
            if any(pattern in path for pattern in config_patterns):
                risk_factors.append("Configuration changes detected")
                risk_score += 0.2
                break
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.5:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return {
            "level": risk_level,
            "score": min(risk_score, 1.0),
            "factors": risk_factors,
            "confidence": 0.8  # Rule-based analysis has good confidence
        }
    
    async def _analyze_type(self, mr_data: Dict[str, Any], changes: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the type of merge request"""
        title = mr_data.get("title", "").lower()
        description = mr_data.get("description", "").lower()
        branch_name = mr_data.get("source_branch", "").lower()
        
        # Type indicators
        type_scores = {
            MRType.HOTFIX: 0,
            MRType.SECURITY: 0,
            MRType.BUGFIX: 0,
            MRType.FEATURE: 0,
            MRType.REFACTOR: 0,
            MRType.PERFORMANCE: 0,
            MRType.DOCUMENTATION: 0,
            MRType.DEPENDENCY: 0
        }
        
        # Analyze title and description
        text_content = f"{title} {description} {branch_name}"
        
        # Hotfix indicators
        if any(word in text_content for word in ["hotfix", "urgent", "critical", "emergency"]):
            type_scores[MRType.HOTFIX] += 0.8
        
        # Security indicators
        if any(word in text_content for word in ["security", "vulnerability", "cve", "exploit", "auth"]):
            type_scores[MRType.SECURITY] += 0.7
        
        # Bug fix indicators
        if any(word in text_content for word in ["fix", "bug", "issue", "error", "crash"]):
            type_scores[MRType.BUGFIX] += 0.6
        
        # Feature indicators
        if any(word in text_content for word in ["feature", "add", "new", "implement", "create"]):
            type_scores[MRType.FEATURE] += 0.5
        
        # Refactor indicators
        if any(word in text_content for word in ["refactor", "cleanup", "reorganize", "restructure"]):
            type_scores[MRType.REFACTOR] += 0.6
        
        # Performance indicators
        if any(word in text_content for word in ["performance", "optimize", "speed", "memory", "cache"]):
            type_scores[MRType.PERFORMANCE] += 0.6
        
        # Documentation indicators
        if any(word in text_content for word in ["docs", "documentation", "readme", "comment"]):
            type_scores[MRType.DOCUMENTATION] += 0.7
        
        # Dependency indicators
        if any(word in text_content for word in ["dependency", "update", "upgrade", "requirements"]):
            type_scores[MRType.DEPENDENCY] += 0.6
        
        # Analyze file changes
        changes_data = changes.get("changes", []) if changes else []
        for change in changes_data:
            path = change.get("old_path", "").lower()
            
            # Documentation files
            if any(ext in path for ext in [".md", ".txt", ".rst", "readme"]):
                type_scores[MRType.DOCUMENTATION] += 0.3
            
            # Dependency files
            if any(file in path for file in ["requirements.txt", "package.json", "pom.xml", "cargo.toml"]):
                type_scores[MRType.DEPENDENCY] += 0.4
        
        # Determine type
        best_type = max(type_scores.items(), key=lambda x: x[1])
        mr_type = best_type[0]
        confidence = min(best_type[1], 1.0)
        
        # Default to feature if no clear type
        if confidence < 0.3:
            mr_type = MRType.FEATURE
            confidence = 0.3
        
        return {
            "type": mr_type,
            "confidence": confidence
        }
    
    async def _analyze_complexity(self, mr_data: Dict[str, Any], changes: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code complexity"""
        complexity_score = 0.0
        
        changes_data = changes.get("changes", []) if changes else []
        total_files = len(changes_data)
        total_lines = mr_data.get("changes_count", 0)
        
        # File count factor
        if total_files > 50:
            complexity_score += 0.4
        elif total_files > 20:
            complexity_score += 0.3
        elif total_files > 10:
            complexity_score += 0.2
        
        # Line count factor  
        total_lines = total_lines or 0
        # Convert to int if it's a string
        try:
            total_lines = int(total_lines) if isinstance(total_lines, str) else total_lines
        except (ValueError, TypeError):
            total_lines = 0
            
        if total_lines > 1000:
            complexity_score += 0.4
        elif total_lines > 500:
            complexity_score += 0.3
        elif total_lines > 200:
            complexity_score += 0.2
        
        # Analyze file types and content
        for change in changes_data:
            path = change.get("old_path", "")
            diff = change.get("diff", "")
            
            # Core system files
            if any(pattern in path.lower() for pattern in ["core", "engine", "framework", "base"]):
                complexity_score += 0.1
            
            # Database/model changes
            if any(pattern in path.lower() for pattern in ["model", "schema", "migration"]):
                complexity_score += 0.1
            
            # API/interface changes
            if any(pattern in path.lower() for pattern in ["api", "interface", "controller"]):
                complexity_score += 0.1
            
            # Check diff complexity
            if diff:
                # Function/class additions
                if len(re.findall(r'^\+.*def |^\+.*class |^\+.*function', diff, re.MULTILINE)) > 5:
                    complexity_score += 0.1
                
                # Complex logic patterns
                if len(re.findall(r'^\+.*(if|for|while|switch|try)', diff, re.MULTILINE)) > 10:
                    complexity_score += 0.1
        
        # Determine complexity level
        if complexity_score >= 0.7:
            complexity_level = Complexity.VERY_COMPLEX
            hours = 8.0
        elif complexity_score >= 0.5:
            complexity_level = Complexity.COMPLEX
            hours = 4.0
        elif complexity_score >= 0.3:
            complexity_level = Complexity.MODERATE
            hours = 2.0
        else:
            complexity_level = Complexity.SIMPLE
            hours = 1.0
        
        return {
            "level": complexity_level,
            "score": min(complexity_score, 1.0),
            "hours": hours,
            "confidence": 0.7
        }
    
    async def _suggest_reviewers(self, mr_data: Dict[str, Any], changes: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest appropriate reviewers (simplified version)"""
        # This is a simplified implementation
        # In a real system, this would analyze:
        # - File history to find experts
        # - Team structure and expertise
        # - Workload balancing
        # - Previous review patterns
        
        suggested_reviewers = []
        
        # For now, return placeholder suggestions
        # TODO: Integrate with CodeCompass expert finder
        
        return {
            "reviewers": suggested_reviewers,
            "confidence": 0.5
        }
    
    def _check_security_patterns(self, title: str, description: str, changes: List[Dict]) -> float:
        """Check for security-related patterns"""
        score = 0.0
        text_content = f"{title} {description}".lower()
        
        # Check title and description
        for pattern in self.security_patterns:
            if re.search(pattern, text_content):
                score += 0.2
        
        # Check file changes
        for change in changes:
            path = change.get("old_path", "").lower()
            diff = change.get("diff", "").lower()
            
            # Security-sensitive files
            if any(keyword in path for keyword in ["auth", "security", "crypto", "admin"]):
                score += 0.3
            
            # Security patterns in diff
            for pattern in self.security_patterns:
                if re.search(pattern, diff):
                    score += 0.1
                    break
        
        return min(score, 1.0)
    
    def _analyze_files(self, changes: List[Dict]) -> Dict[str, int]:
        """Analyze file changes"""
        high_risk_files = 0
        total_files = len(changes)
        
        high_risk_patterns = [
            "dockerfile", "docker-compose", "k8s", "kubernetes",
            "config", "env", "settings",
            "migration", "schema", "database",
            "security", "auth", "permission",
            "makefile", "build", "deploy"
        ]
        
        for change in changes:
            path = change.get("old_path", "").lower()
            if any(pattern in path for pattern in high_risk_patterns):
                high_risk_files += 1
        
        return {
            "total_files": total_files,
            "high_risk_files": high_risk_files
        }
    
    def _determine_review_requirements(self, risk_analysis: Dict, type_analysis: Dict) -> Dict[str, bool]:
        """Determine what types of reviews are needed"""
        requirements = {
            "security_review": False,
            "performance_review": False,
            "architecture_review": False,
            "database_review": False
        }
        
        # Security review needed
        if (risk_analysis["level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL] or
            type_analysis["type"] == MRType.SECURITY or
            "Security-sensitive changes detected" in risk_analysis["factors"]):
            requirements["security_review"] = True
        
        # Performance review needed
        if (type_analysis["type"] == MRType.PERFORMANCE or
            "Large code change" in str(risk_analysis["factors"])):
            requirements["performance_review"] = True
        
        # Architecture review needed
        if (risk_analysis["level"] == RiskLevel.CRITICAL or
            type_analysis["type"] == MRType.REFACTOR):
            requirements["architecture_review"] = True
        
        # Database review needed
        if "Database migration changes" in risk_analysis["factors"]:
            requirements["database_review"] = True
        
        return requirements
    
    def _generate_labels(self, risk_analysis: Dict, type_analysis: Dict, complexity_analysis: Dict) -> List[str]:
        """Generate appropriate labels for the MR"""
        labels = []
        
        # Risk labels
        labels.append(f"risk::{risk_analysis['level'].value}")
        
        # Type labels
        labels.append(f"type::{type_analysis['type'].value}")
        
        # Complexity labels
        labels.append(f"complexity::{complexity_analysis['level'].value}")
        
        # Review labels
        if complexity_analysis["hours"] > 4:
            labels.append("review::extended")
        
        return labels

# Global instance
_mr_triage_system: Optional[MRTriageSystem] = None

def get_mr_triage_system() -> MRTriageSystem:
    """Get or create MR triage system instance"""
    global _mr_triage_system
    if _mr_triage_system is None:
        _mr_triage_system = MRTriageSystem()
    return _mr_triage_system