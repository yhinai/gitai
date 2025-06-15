"""
AI insights API endpoints
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import structlog
import uuid

from src.features.mr_triage import get_mr_triage_system, MRAnalysis, RiskLevel, MRType, Complexity
from src.features.pipeline_optimizer import get_pipeline_optimizer, OptimizationLevel, JobOptimization
from src.features.vulnerability_scanner import get_vulnerability_scanner, VulnerabilitySeverity
from src.features.chatops_bot import get_chatops_bot, ChatMessage, DiagnosisConfidence

logger = structlog.get_logger(__name__)
router = APIRouter()

class MRTriageRequest(BaseModel):
    """Request for MR triage analysis"""
    project_id: int
    mr_iid: int

class PipelineOptimizationRequest(BaseModel):
    """Request for pipeline optimization analysis"""
    project_id: int
    pipeline_id: Optional[int] = None
    optimization_level: str = "balanced"

class VulnerabilityScanRequest(BaseModel):
    """Request for vulnerability scan"""
    project_id: int
    commit_sha: Optional[str] = None

class ChatRequest(BaseModel):
    """Request for ChatOps interaction"""
    user_id: str
    project_id: int
    message: str
    channel: str = "api"
    context: Dict[str, Any] = {}

class MRTriageResponse(BaseModel):
    """Response for MR triage analysis"""
    mr_id: int
    mr_iid: int
    project_id: int
    risk_level: str
    risk_score: float
    mr_type: str
    complexity: str
    estimated_review_hours: float
    risk_factors: List[str]
    suggested_reviewers: List[Dict[str, Any]]
    review_requirements: Dict[str, bool]
    labels: List[str]
    confidence_score: float
    analysis_timestamp: str

@router.post("/triage/merge-request", response_model=MRTriageResponse)
async def analyze_merge_request(request: MRTriageRequest):
    """Analyze a merge request for risk and complexity"""
    triage_system = get_mr_triage_system()
    
    try:
        logger.info(
            "Starting MR triage analysis",
            project_id=request.project_id,
            mr_iid=request.mr_iid
        )
        
        analysis = await triage_system.analyze_merge_request(
            project_id=request.project_id,
            mr_iid=request.mr_iid
        )
        
        response = MRTriageResponse(
            mr_id=analysis.mr_id,
            mr_iid=analysis.mr_iid,
            project_id=analysis.project_id,
            risk_level=analysis.risk_level.value,
            risk_score=analysis.risk_score,
            mr_type=analysis.mr_type.value,
            complexity=analysis.complexity.value,
            estimated_review_hours=analysis.estimated_review_hours,
            risk_factors=analysis.risk_factors,
            suggested_reviewers=analysis.suggested_reviewers,
            review_requirements=analysis.review_requirements,
            labels=analysis.labels,
            confidence_score=analysis.confidence_score,
            analysis_timestamp=analysis.analysis_timestamp.isoformat()
        )
        
        logger.info(
            "MR triage analysis completed",
            project_id=request.project_id,
            mr_iid=request.mr_iid,
            risk_level=analysis.risk_level.value,
            confidence=analysis.confidence_score
        )
        
        return response
        
    except ValueError as e:
        logger.error(
            "MR triage analysis failed - not found",
            project_id=request.project_id,
            mr_iid=request.mr_iid,
            error=str(e)
        )
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(
            "MR triage analysis failed",
            project_id=request.project_id,
            mr_iid=request.mr_iid,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Analysis failed")

@router.get("/triage/demo")
async def demo_mr_analysis():
    """Demo MR analysis with realistic examples"""
    return {
        "demo": True,
        "project_name": "ecommerce-platform",
        "project_id": 278964,
        "mr_iid": 1247,
        "mr_title": "Add Redis caching layer for product recommendations",
        "author": "sarah.chen",
        "branch": "feature/redis-product-cache",
        "target_branch": "main",
        "analysis": {
            "risk_level": "medium",
            "risk_score": 0.65,
            "mr_type": "feature",
            "complexity": "moderate",
            "estimated_review_hours": 2.5,
            "risk_factors": [
                "Database schema changes detected",
                "New Redis dependency introduced",
                "Configuration changes in production files",
                "Cache invalidation logic added"
            ],
            "suggested_reviewers": [
                {
                    "username": "mike.rodriguez",
                    "name": "Mike Rodriguez",
                    "expertise": ["backend", "caching", "redis"],
                    "confidence": 0.92
                },
                {
                    "username": "lisa.park",
                    "name": "Lisa Park", 
                    "expertise": ["database", "performance", "architecture"],
                    "confidence": 0.88
                }
            ],
            "review_requirements": {
                "security_review": False,
                "performance_review": True,
                "architecture_review": True,
                "two_approvals_required": True
            },
            "labels": ["feature", "caching", "performance", "needs-testing"],
            "confidence_score": 0.87,
            "files_changed": [
                "src/services/product_service.py",
                "src/cache/redis_client.py", 
                "config/redis.yml",
                "requirements.txt",
                "tests/test_product_cache.py"
            ],
            "lines_added": 234,
            "lines_removed": 12,
            "security_concerns": [],
            "performance_impact": "Positive - Expected 40% reduction in product query time"
        }
    }

@router.get("/triage/stats")
async def get_triage_stats():
    """Get triage system statistics"""
    triage_system = get_mr_triage_system()
    
    return {
        "cache_size": len(triage_system.analysis_cache),
        "security_patterns": len(triage_system.security_patterns),
        "complexity_indicators": len(triage_system.complexity_indicators),
        "supported_risk_levels": [level.value for level in RiskLevel],
        "supported_mr_types": [mr_type.value for mr_type in MRType],
        "supported_complexity_levels": [complexity.value for complexity in Complexity]
    }

@router.post("/triage/bulk")
async def bulk_analyze_merge_requests(
    project_id: int,
    mr_iids: List[int],
    background_tasks: BackgroundTasks
):
    """Analyze multiple merge requests in background"""
    if len(mr_iids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 MRs per bulk request")
    
    # Start background analysis
    background_tasks.add_task(_bulk_analyze_mrs, project_id, mr_iids)
    
    return {
        "status": "started",
        "project_id": project_id,
        "mr_count": len(mr_iids),
        "message": "Bulk analysis started in background"
    }

async def _bulk_analyze_mrs(project_id: int, mr_iids: List[int]):
    """Background task for bulk MR analysis"""
    triage_system = get_mr_triage_system()
    
    logger.info(
        "Starting bulk MR analysis",
        project_id=project_id,
        mr_count=len(mr_iids)
    )
    
    successful = 0
    failed = 0
    
    for mr_iid in mr_iids:
        try:
            await triage_system.analyze_merge_request(project_id, mr_iid)
            successful += 1
        except Exception as e:
            logger.error(
                "Bulk analysis failed for MR",
                project_id=project_id,
                mr_iid=mr_iid,
                error=str(e)
            )
            failed += 1
    
    logger.info(
        "Bulk MR analysis completed",
        project_id=project_id,
        successful=successful,
        failed=failed
    )

@router.post("/optimize/pipeline")
async def optimize_pipeline(request: PipelineOptimizationRequest):
    """Analyze and optimize CI/CD pipeline performance"""
    optimizer = get_pipeline_optimizer()
    
    try:
        # Validate optimization level
        try:
            opt_level = OptimizationLevel(request.optimization_level)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid optimization level. Must be one of: {[l.value for l in OptimizationLevel]}"
            )
        
        logger.info(
            "Starting pipeline optimization",
            project_id=request.project_id,
            pipeline_id=request.pipeline_id,
            optimization_level=opt_level.value
        )
        
        analysis = await optimizer.analyze_pipeline_performance(
            project_id=request.project_id,
            pipeline_id=request.pipeline_id,
            optimization_level=opt_level
        )
        
        return {
            "project_id": analysis.project_id,
            "pipeline_id": analysis.pipeline_id,
            "optimization_score": analysis.overall_score,
            "current_metrics": {
                "avg_duration_minutes": analysis.current_metrics.avg_duration,
                "success_rate": analysis.current_metrics.success_rate,
                "cost_per_run": analysis.current_metrics.cost_per_run,
                "resource_efficiency": analysis.current_metrics.resource_efficiency,
                "bottleneck_stages": analysis.current_metrics.bottleneck_stages
            },
            "predicted_metrics": {
                "avg_duration_minutes": analysis.predicted_metrics.avg_duration,
                "success_rate": analysis.predicted_metrics.success_rate,
                "cost_per_run": analysis.predicted_metrics.cost_per_run,
                "resource_efficiency": analysis.predicted_metrics.resource_efficiency
            },
            "recommendations": [
                {
                    "type": rec.type.value,
                    "description": rec.description,
                    "estimated_impact": rec.estimated_impact,
                    "difficulty": rec.implementation_difficulty,
                    "risk": rec.risk_level,
                    "confidence": rec.confidence,
                    "has_code_changes": bool(rec.code_changes)
                }
                for rec in analysis.recommendations
            ],
            "improvements": {
                "duration_reduction": f"{((analysis.current_metrics.avg_duration - analysis.predicted_metrics.avg_duration) / analysis.current_metrics.avg_duration * 100):.1f}%" if analysis.current_metrics.avg_duration > 0 else "0%",
                "cost_savings": f"{((analysis.current_metrics.cost_per_run - analysis.predicted_metrics.cost_per_run) / analysis.current_metrics.cost_per_run * 100):.1f}%" if analysis.current_metrics.cost_per_run > 0 else "0%",
                "efficiency_gain": f"{((analysis.predicted_metrics.resource_efficiency - analysis.current_metrics.resource_efficiency) * 100):.1f}%"
            },
            "analysis_timestamp": analysis.analysis_timestamp.isoformat()
        }
        
    except ValueError as e:
        logger.error(
            "Pipeline optimization failed - not found",
            project_id=request.project_id,
            pipeline_id=request.pipeline_id,
            error=str(e)
        )
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(
            "Pipeline optimization failed",
            project_id=request.project_id,
            pipeline_id=request.pipeline_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Optimization analysis failed")

@router.get("/optimize/demo")
async def demo_pipeline_optimization():
    """Demo pipeline optimization with realistic examples"""
    return {
        "demo": True,
        "project_name": "microservices-api",
        "project_id": 278964,
        "pipeline_id": 45231,
        "analysis": {
            "optimization_score": 73,
            "current_metrics": {
                "avg_duration_minutes": 18.5,
                "p95_duration_minutes": 24.2,
                "success_rate": 0.87,
                "cost_per_run": 2.45,
                "resource_efficiency": 0.62,
                "bottleneck_stages": ["integration-tests", "security-scan"]
            },
            "predicted_metrics": {
                "avg_duration_minutes": 12.3,
                "p95_duration_minutes": 16.8,
                "success_rate": 0.91,
                "cost_per_run": 1.78,
                "resource_efficiency": 0.84
            },
            "improvements": {
                "duration_reduction": "33.5%",
                "cost_savings": "27.3%", 
                "efficiency_gain": "35.5%"
            },
            "recommendations": [
                {
                    "type": "parallelization",
                    "description": "Run unit tests and lint checks in parallel instead of sequentially",
                    "estimated_impact": {
                        "duration_reduction": 4.2,
                        "cost_savings": 0.31
                    },
                    "difficulty": "easy",
                    "risk": "low",
                    "confidence": 0.94,
                    "code_changes": {
                        ".gitlab-ci.yml": "stages:\n  - build\n  - test\n  - lint\n\nunit-tests:\n  stage: test\n  script: npm test\n\nlint:\n  stage: lint\n  script: npm run lint"
                    }
                },
                {
                    "type": "caching",
                    "description": "Cache node_modules between pipeline runs to avoid repeated npm install",
                    "estimated_impact": {
                        "duration_reduction": 2.8,
                        "cost_savings": 0.24
                    },
                    "difficulty": "easy",
                    "risk": "low",
                    "confidence": 0.89,
                    "code_changes": {
                        ".gitlab-ci.yml": "variables:\n  npm_config_cache: '$CI_PROJECT_DIR/.npm'\n\ncache:\n  paths:\n    - .npm/\n    - node_modules/"
                    }
                },
                {
                    "type": "image_optimization",
                    "description": "Replace node:latest with node:18-alpine to reduce image pull time",
                    "estimated_impact": {
                        "duration_reduction": 1.5,
                        "cost_savings": 0.12
                    },
                    "difficulty": "easy",
                    "risk": "low",
                    "confidence": 0.96
                }
            ],
            "ci_config_analysis": {
                "stages": ["build", "test", "security", "deploy"],
                "total_jobs": 8,
                "parallel_jobs": 2,
                "unused_artifacts": ["coverage/", "logs/"],
                "cache_utilization": 0.23
            }
        }
    }

@router.get("/optimize/stats")
async def get_optimizer_stats():
    """Get pipeline optimizer statistics"""
    optimizer = get_pipeline_optimizer()
    
    return {
        "cache_size": len(optimizer.analysis_cache),
        "parallelization_patterns": len(optimizer.parallelization_patterns),
        "caching_opportunities": len(optimizer.caching_opportunities),
        "optimized_images": len(optimizer.optimized_images),
        "supported_optimization_levels": [level.value for level in OptimizationLevel],
        "supported_optimization_types": [opt_type.value for opt_type in JobOptimization]
    }

@router.post("/scan/vulnerabilities")
async def scan_vulnerabilities(request: VulnerabilityScanRequest):
    """Scan project dependencies for vulnerabilities"""
    scanner = get_vulnerability_scanner()
    
    try:
        logger.info(
            "Starting vulnerability scan",
            project_id=request.project_id,
            commit_sha=request.commit_sha
        )
        
        scan_result = await scanner.scan_project(
            project_id=request.project_id,
            commit_sha=request.commit_sha
        )
        
        return {
            "scan_id": scan_result.scan_id,
            "project_id": scan_result.project_id,
            "commit_sha": scan_result.commit_sha,
            "scan_timestamp": scan_result.scan_timestamp.isoformat(),
            "summary": {
                "dependencies": {
                    "total": scan_result.summary["total_dependencies"],
                    "direct": scan_result.summary["direct_dependencies"],
                    "transitive": scan_result.summary["transitive_dependencies"],
                    "by_ecosystem": scan_result.summary.get("ecosystems", {})
                },
                "vulnerabilities": {
                    "total": scan_result.summary["total_vulnerabilities"],
                    "critical": scan_result.summary["critical"],
                    "high": scan_result.summary["high"],
                    "medium": scan_result.summary["medium"],
                    "low": scan_result.summary["low"],
                    "info": scan_result.summary["info"]
                }
            },
            "vulnerabilities": [
                {
                    "id": vuln.id,
                    "cve_id": vuln.cve_id,
                    "title": vuln.title,
                    "severity": vuln.severity.value,
                    "cvss_score": vuln.cvss_score,
                    "affected_package": vuln.affected_package,
                    "fixed_versions": vuln.fixed_versions,
                    "published_date": vuln.published_date.isoformat(),
                    "exploitability": vuln.exploitability
                }
                for vuln in scan_result.vulnerabilities[:20]  # Limit to top 20
            ],
            "dependencies": [
                {
                    "name": dep.name,
                    "version": dep.version,
                    "ecosystem": dep.ecosystem.value,
                    "scope": dep.scope,
                    "file_path": dep.file_path
                }
                for dep in scan_result.dependencies[:50]  # Limit to top 50
            ],
            "sbom_available": bool(scan_result.sbom)
        }
        
    except Exception as e:
        logger.error(
            "Vulnerability scan failed",
            project_id=request.project_id,
            commit_sha=request.commit_sha,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Vulnerability scan failed")

@router.get("/scan/demo")
async def demo_vulnerability_scan():
    """Demo vulnerability scan with realistic examples"""
    return {
        "demo": True,
        "project_name": "react-dashboard",
        "project_id": 278964,
        "commit_sha": "a7b8c9d1e2f3",
        "scan_id": "scan_20241215_143022",
        "scan_timestamp": datetime.utcnow().isoformat(),
        "scan_summary": {
            "dependencies_found": 247,
            "direct_dependencies": 23,
            "transitive_dependencies": 224,
            "vulnerabilities_found": 8,
            "critical_vulns": 1,
            "high_vulns": 2,
            "medium_vulns": 3,
            "low_vulns": 2,
            "ecosystems_detected": ["npm", "pypi"],
            "scan_duration": "3.2 seconds",
            "sbom_generated": True
        },
        "vulnerabilities": [
            {
                "id": "GHSA-c427-hjc3-wrfw",
                "cve_id": "CVE-2023-45133",
                "title": "Babel vulnerable to arbitrary code execution when compiling specifically crafted malicious code",
                "severity": "critical",
                "cvss_score": 8.8,
                "affected_package": "@babel/traverse",
                "current_version": "7.22.0",
                "fixed_versions": ["7.23.2"],
                "published_date": "2023-10-12T00:00:00Z",
                "exploitability": "proof_of_concept"
            },
            {
                "id": "GHSA-67hx-6x53-jw92",
                "cve_id": "CVE-2023-44270",
                "title": "PostCSS line return parsing error",
                "severity": "high",
                "cvss_score": 7.5,
                "affected_package": "postcss",
                "current_version": "8.7.0",
                "fixed_versions": ["8.4.31"],
                "published_date": "2023-09-28T00:00:00Z",
                "exploitability": "no_known_exploit"
            },
            {
                "id": "GHSA-3xgq-45jj-v275",
                "cve_id": "CVE-2023-39325",
                "title": "RapidJSON insecure parsing of numeric values",
                "severity": "high",
                "cvss_score": 7.3,
                "affected_package": "rapidjson",
                "current_version": "1.1.0",
                "fixed_versions": ["1.2.0"],
                "published_date": "2023-10-10T00:00:00Z",
                "exploitability": "exploit_available"
            },
            {
                "id": "PYSEC-2023-218",
                "cve_id": "CVE-2023-5752",
                "title": "pip vulnerable to mercurial configuration injection",
                "severity": "medium",
                "cvss_score": 6.4,
                "affected_package": "pip",
                "current_version": "21.3.1",
                "fixed_versions": ["23.3"],
                "published_date": "2023-10-25T00:00:00Z",
                "exploitability": "no_known_exploit"
            }
        ],
        "dependencies": [
            {
                "name": "react",
                "version": "18.2.0",
                "ecosystem": "npm",
                "scope": "direct",
                "file_path": "package.json",
                "license": "MIT"
            },
            {
                "name": "@babel/core",
                "version": "7.22.5",
                "ecosystem": "npm",
                "scope": "direct",
                "file_path": "package.json",
                "license": "MIT"
            },
            {
                "name": "lodash",
                "version": "4.17.21",
                "ecosystem": "npm",
                "scope": "transitive",
                "file_path": "package-lock.json",
                "license": "MIT"
            },
            {
                "name": "fastapi",
                "version": "0.104.1",
                "ecosystem": "pypi",
                "scope": "direct",
                "file_path": "requirements.txt",
                "license": "MIT"
            },
            {
                "name": "pydantic",
                "version": "2.4.2",
                "ecosystem": "pypi",
                "scope": "direct",
                "file_path": "requirements.txt",
                "license": "MIT"
            }
        ],
        "ecosystem_breakdown": {
            "npm": {
                "total": 198,
                "direct": 18,
                "vulnerabilities": 6
            },
            "pypi": {
                "total": 49,
                "direct": 5,
                "vulnerabilities": 2
            }
        },
        "sbom_available": True,
        "remediation_advice": [
            "Update @babel/traverse to version 7.23.2 or later (CRITICAL)",
            "Update postcss to version 8.4.31 or later",
            "Consider updating pip to version 23.3 or later",
            "Review transitive dependencies for additional updates"
        ]
    }

@router.get("/scan/{scan_id}/sbom")
async def get_sbom(scan_id: str):
    """Get SBOM (Software Bill of Materials) for a scan"""
    scanner = get_vulnerability_scanner()
    
    # Look for scan in cache
    for cached_result in scanner.scan_cache.values():
        if cached_result.scan_id == scan_id:
            return {
                "scan_id": scan_id,
                "format": "CycloneDX",
                "sbom": cached_result.sbom
            }
    
    raise HTTPException(status_code=404, detail="Scan not found or expired")

@router.get("/scan/stats")
async def get_scanner_stats():
    """Get vulnerability scanner statistics"""
    scanner = get_vulnerability_scanner()
    
    return {
        "scan_cache_size": len(scanner.scan_cache),
        "supported_file_types": list(scanner.dependency_parser.parsers.keys()),
        "vulnerability_sources": ["OSV (Open Source Vulnerabilities)"],
        "sbom_formats": ["CycloneDX"],
        "severity_levels": [severity.value for severity in VulnerabilitySeverity]
    }

@router.post("/chat")
async def chat_with_bot(request: ChatRequest):
    """Chat with AI-powered DevOps bot"""
    chatops_bot = get_chatops_bot()
    
    try:
        # Create chat message
        chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            project_id=request.project_id,
            channel=request.channel,
            content=request.message,
            timestamp=datetime.utcnow(),
            context=request.context
        )
        
        # Process message
        response = await chatops_bot.process_message(chat_message)
        
        return {
            "response_text": response.response_text,
            "action_taken": response.action_taken.value if response.action_taken else None,
            "confidence": response.confidence.value,
            "suggested_actions": response.suggested_actions,
            "attachments": response.attachments,
            "escalation_needed": response.escalation_needed,
            "message_id": response.message_id
        }
        
    except Exception as e:
        logger.error(
            "ChatOps request failed",
            user_id=request.user_id,
            project_id=request.project_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Chat processing failed")

@router.get("/chat/demo")
async def demo_chatops():
    """Demo ChatOps functionality with realistic examples"""
    return {
        "demo": True,
        "project_name": "web-app-backend",
        "responses": [
            {
                "input": "Why did build #1247 fail?",
                "response": "Build #1247 failed in the 'integration-tests' stage. The main issue was a timeout in the database connection test. I found that the test database wasn't properly initialized. The specific error was: 'psycopg2.OperationalError: FATAL: database 'test_db' does not exist'. This suggests the database setup step in the CI pipeline may have been skipped or failed silently.",
                "action": "build_diagnosis",
                "confidence": "high",
                "suggested_actions": [
                    "Check database initialization script",
                    "Verify test database configuration",
                    "Review CI pipeline database setup stage"
                ],
                "time_to_fix": "~15 minutes"
            },
            {
                "input": "analyze MR !456",
                "response": "MR !456 'Add user authentication middleware' shows MEDIUM risk with 2.5 hour estimated review time. Key findings: introduces new JWT dependency, modifies core authentication flow, adds 234 lines of code. Security review recommended due to authentication changes. Suggested reviewers: @mike.security and @sarah.backend based on their middleware expertise.",
                "action": "mr_analysis",
                "confidence": "high",
                "risk_level": "medium",
                "complexity": "moderate",
                "files_changed": 5
            },
            {
                "input": "how to make pipeline faster?",
                "response": "I analyzed your current pipeline and found 3 major optimization opportunities: 1) Parallelize unit tests and linting (saves ~4 minutes), 2) Add node_modules caching (saves ~2.8 minutes), 3) Use node:18-alpine instead of node:latest (saves ~1.5 minutes). Total potential savings: 33% faster builds. I can generate the optimized .gitlab-ci.yml if you'd like.",
                "action": "pipeline_optimization",
                "confidence": "high",
                "potential_savings": "33%",
                "implementation_difficulty": "easy"
            },
            {
                "input": "explain the error in job test:unit",
                "response": "The test:unit job failed with exit code 1. The error log shows 'TypeError: Cannot read property 'length' of undefined' in user_service.test.js:45. This happened because the mock user data wasn't properly set up in the test. The test is trying to access user.roles.length but the mock user object doesn't have a roles property. Fix: Add roles: [] to the mock user object.",
                "action": "error_diagnosis",
                "confidence": "high",
                "error_type": "TypeError",
                "file_location": "user_service.test.js:45",
                "fix_suggestion": "Add roles: [] to mock user object"
            },
            {
                "input": "scan for vulnerabilities",
                "response": "I found 8 vulnerabilities in your dependencies: 1 CRITICAL (CVE-2023-45133 in @babel/traverse), 2 HIGH, 3 MEDIUM, 2 LOW. The critical vulnerability allows arbitrary code execution. Immediate action needed: Update @babel/traverse from 7.22.0 to 7.23.2. I can create a security patch MR if you approve.",
                "action": "security_scan",
                "confidence": "high",
                "vulnerabilities": {
                    "critical": 1,
                    "high": 2,
                    "medium": 3,
                    "low": 2
                },
                "priority_fix": "@babel/traverse update"
            },
            {
                "input": "help",
                "response": "I'm your GitAIOps assistant! I can help with: 🔍 Diagnose build failures, 📊 Analyze merge requests, ⚡ Optimize pipelines, 🛡️ Scan for vulnerabilities, 🔧 Explain errors, 📈 Provide performance insights. Try asking: 'why did build #123 fail?' or 'analyze MR !456' or 'how to make pipeline faster?'",
                "action": "help",
                "confidence": "high",
                "capabilities": [
                    "Build diagnosis",
                    "MR analysis", 
                    "Pipeline optimization",
                    "Vulnerability scanning",
                    "Error explanation"
                ]
            }
        ],
        "supported_commands": [
            "diagnose build #<number>",
            "analyze MR !<number>",
            "scan for vulnerabilities",
            "fix pipeline",
            "explain error in job <job_name>",
            "optimize build time",
            "security check",
            "help"
        ],
        "context_awareness": {
            "project_language": "JavaScript/Python",
            "ci_platform": "GitLab CI/CD",
            "recent_failures": 3,
            "average_build_time": "18.5 minutes",
            "success_rate": "87%"
        }
    }

@router.get("/chat/stats")
async def get_chatops_stats():
    """Get ChatOps bot statistics"""
    chatops_bot = get_chatops_bot()
    return chatops_bot.get_stats()

# Additional realistic demo endpoints

@router.get("/demo/projects")
async def demo_project_showcase():
    """Showcase analysis across different project types"""
    return {
        "demo": True,
        "projects": [
            {
                "name": "react-ecommerce",
                "type": "Frontend",
                "language": "JavaScript/TypeScript",
                "recent_mr": {
                    "title": "Implement shopping cart persistence with Redux",
                    "risk_level": "medium",
                    "complexity": "moderate",
                    "files_changed": ["src/store/cartSlice.js", "src/components/Cart.tsx", "src/hooks/useCart.ts"],
                    "estimated_review_time": "2.5 hours"
                },
                "pipeline_status": {
                    "avg_duration": "12.3 minutes",
                    "success_rate": "91%",
                    "last_optimization": "Added node_modules caching - 35% faster"
                },
                "security": {
                    "vulnerabilities": 3,
                    "critical": 0,
                    "high": 1,
                    "most_critical": "postcss XSS vulnerability"
                }
            },
            {
                "name": "fastapi-microservice",
                "type": "Backend API",
                "language": "Python",
                "recent_mr": {
                    "title": "Add JWT authentication and rate limiting",
                    "risk_level": "high",
                    "complexity": "complex",
                    "files_changed": ["src/auth/jwt_handler.py", "src/middleware/rate_limit.py", "src/main.py"],
                    "estimated_review_time": "4.5 hours"
                },
                "pipeline_status": {
                    "avg_duration": "8.7 minutes", 
                    "success_rate": "87%",
                    "last_optimization": "Parallelized pytest runs - 28% faster"
                },
                "security": {
                    "vulnerabilities": 5,
                    "critical": 1,
                    "high": 2,
                    "most_critical": "pydantic RCE vulnerability"
                }
            },
            {
                "name": "golang-cli-tool",
                "type": "CLI Application",
                "language": "Go",
                "recent_mr": {
                    "title": "Refactor command parsing with cobra library",
                    "risk_level": "low",
                    "complexity": "simple",
                    "files_changed": ["cmd/root.go", "cmd/version.go", "main.go"],
                    "estimated_review_time": "1.5 hours"
                },
                "pipeline_status": {
                    "avg_duration": "3.2 minutes",
                    "success_rate": "95%",
                    "last_optimization": "Multi-arch builds in parallel - 45% faster"
                },
                "security": {
                    "vulnerabilities": 0,
                    "critical": 0,
                    "high": 0,
                    "most_critical": "No vulnerabilities found"
                }
            }
        ]
    }

@router.get("/demo/realtime-analysis")
async def demo_realtime_analysis():
    """Demo real-time analysis of a simulated MR"""
    return {
        "demo": True,
        "analysis_in_progress": True,
        "mr_details": {
            "project": "mobile-banking-app",
            "mr_iid": 892,
            "title": "Implement biometric authentication for iOS",
            "author": "jennifer.kim",
            "branch": "feature/ios-biometric-auth",
            "target_branch": "develop",
            "created_at": "2024-12-15T10:30:00Z",
            "commits": 8,
            "files_changed": 12
        },
        "analysis_stages": [
            {
                "stage": "Code Analysis",
                "status": "completed",
                "duration": "1.2s",
                "findings": [
                    "TouchID/FaceID integration detected",
                    "Keychain security implementation found",
                    "Privacy permissions properly configured"
                ]
            },
            {
                "stage": "Security Review",
                "status": "completed", 
                "duration": "2.1s",
                "findings": [
                    "Biometric data handling follows Apple guidelines",
                    "No hardcoded credentials detected",
                    "Proper error handling for auth failures"
                ]
            },
            {
                "stage": "Complexity Assessment",
                "status": "completed",
                "duration": "0.8s",
                "findings": [
                    "Moderate complexity due to biometric APIs",
                    "Well-structured code with clear separation",
                    "Comprehensive unit tests included"
                ]
            },
            {
                "stage": "Risk Evaluation",
                "status": "completed",
                "duration": "1.5s",
                "findings": [
                    "Medium risk due to authentication changes",
                    "Requires iOS security expert review",
                    "Device testing recommended"
                ]
            }
        ],
        "final_assessment": {
            "risk_level": "medium",
            "risk_score": 0.58,
            "complexity": "moderate",
            "estimated_review_hours": 3.5,
            "confidence": 0.89,
            "recommended_reviewers": [
                {
                    "username": "alex.ios",
                    "expertise": ["iOS", "biometrics", "security"],
                    "confidence": 0.94
                },
                {
                    "username": "sarah.security",
                    "expertise": ["mobile-security", "authentication"],
                    "confidence": 0.87
                }
            ],
            "required_checks": [
                "iOS security review",
                "Device testing on multiple iOS versions",
                "Privacy compliance verification"
            ]
        }
    }

@router.get("/demo/pipeline-history")
async def demo_pipeline_history():
    """Demo pipeline optimization history and trends"""
    return {
        "demo": True,
        "project": "web-application-monorepo",
        "optimization_history": [
            {
                "date": "2024-12-10",
                "optimization": "Added Docker layer caching",
                "duration_before": "25.3 minutes",
                "duration_after": "18.7 minutes",
                "improvement": "26% faster",
                "cost_savings": "$0.43 per build"
            },
            {
                "date": "2024-12-08", 
                "optimization": "Parallelized test suites",
                "duration_before": "18.7 minutes",
                "duration_after": "14.2 minutes",
                "improvement": "24% faster",
                "cost_savings": "$0.31 per build"
            },
            {
                "date": "2024-12-05",
                "optimization": "Optimized bundle size analysis",
                "duration_before": "14.2 minutes", 
                "duration_after": "12.8 minutes",
                "improvement": "10% faster",
                "cost_savings": "$0.12 per build"
            }
        ],
        "current_metrics": {
            "avg_duration": "12.8 minutes",
            "success_rate": "92%",
            "cost_per_build": "$1.23",
            "runs_per_day": 45,
            "total_monthly_savings": "$147.30"
        },
        "upcoming_recommendations": [
            {
                "type": "conditional_execution",
                "description": "Skip test suite when only docs are changed",
                "estimated_savings": "15% on doc-only commits",
                "confidence": "high"
            },
            {
                "type": "resource_optimization",
                "description": "Use smaller runners for lint/format jobs",
                "estimated_savings": "$0.08 per build",
                "confidence": "medium"
            }
        ]
    }

@router.get("/demo/code-analysis")
async def demo_code_analysis():
    """Demo detailed code analysis with actual code snippets"""
    return {
        "demo": True,
        "project": "react-typescript-webapp",
        "mr_title": "Refactor user authentication with TypeScript and JWT",
        "analysis": {
            "files_analyzed": [
                {
                    "path": "src/auth/AuthService.ts",
                    "change_type": "modified",
                    "lines_added": 89,
                    "lines_removed": 34,
                    "complexity_score": 7.2,
                    "code_sample": '''export class AuthService {
  private tokenKey = 'auth_token';
  
  async login(credentials: LoginCredentials): Promise<AuthResult> {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });
      
      if (!response.ok) {
        throw new AuthError(`Login failed: ${response.statusText}`);
      }
      
      const { token, user } = await response.json();
      this.setToken(token);
      return { success: true, user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
}''',
                    "issues_detected": [
                        {
                            "type": "security",
                            "severity": "medium",
                            "message": "Token stored in localStorage without encryption",
                            "line": 15,
                            "suggestion": "Consider using secure storage or httpOnly cookies"
                        }
                    ]
                },
                {
                    "path": "src/components/LoginForm.tsx",
                    "change_type": "new",
                    "lines_added": 156,
                    "lines_removed": 0,
                    "complexity_score": 4.8,
                    "code_sample": '''interface LoginFormProps {
  onSuccess: (user: User) => void;
  onError: (error: string) => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, onError }) => {
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    const result = await authService.login(credentials);
    if (result.success) {
      onSuccess(result.user);
    } else {
      onError(result.error);
    }
    setIsLoading(false);
  };''',
                    "issues_detected": [
                        {
                            "type": "accessibility",
                            "severity": "low", 
                            "message": "Missing ARIA labels for form inputs",
                            "line": 18,
                            "suggestion": "Add aria-label attributes for screen readers"
                        }
                    ]
                },
                {
                    "path": ".gitlab-ci.yml",
                    "change_type": "modified",
                    "lines_added": 12,
                    "lines_removed": 8,
                    "complexity_score": 3.1,
                    "code_sample": '''stages:
  - build
  - test
  - security
  - deploy

variables:
  NODE_VERSION: "18"
  npm_config_cache: "$CI_PROJECT_DIR/.npm"

cache:
  paths:
    - .npm/
    - node_modules/

build:
  stage: build
  image: node:18-alpine
  script:
    - npm ci --cache .npm --prefer-offline
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 hour

test:
  stage: test
  image: node:18-alpine
  script:
    - npm ci --cache .npm --prefer-offline
    - npm run test:coverage
  coverage: '/All files[^|]*|[^|]*\\s+([\\d\\.]+)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml''',
                    "issues_detected": [
                        {
                            "type": "optimization",
                            "severity": "low",
                            "message": "Tests and build could run in parallel",
                            "line": 25,
                            "suggestion": "Split into parallel jobs for faster execution"
                        }
                    ]
                }
            ],
            "security_analysis": {
                "score": 7.5,
                "issues_found": 2,
                "critical": 0,
                "high": 0,
                "medium": 1,
                "low": 1,
                "recommendations": [
                    "Implement secure token storage mechanism",
                    "Add input validation for login credentials",
                    "Enable content security policy headers"
                ]
            },
            "performance_analysis": {
                "score": 8.2,
                "bundle_size_impact": "+12KB (acceptable)",
                "recommendations": [
                    "Consider lazy loading authentication components",
                    "Optimize JWT parsing with lightweight library"
                ]
            },
            "maintainability": {
                "score": 9.1,
                "test_coverage": "89%",
                "type_safety": "95%",
                "documentation": "Good - interfaces well documented"
            }
        }
    }

@router.get("/demo/vulnerability-details")
async def demo_vulnerability_details():
    """Demo detailed vulnerability information"""
    return {
        "demo": True,
        "project": "node-express-api",
        "scan_results": {
            "critical_vulnerability": {
                "id": "GHSA-c427-hjc3-wrfw",
                "cve_id": "CVE-2023-45133",
                "package": "@babel/traverse",
                "current_version": "7.22.0",
                "fixed_version": "7.23.2",
                "severity": "critical",
                "cvss_score": 8.8,
                "description": "Babel's traverse function can execute arbitrary code when compiling specifically crafted malicious code",
                "impact": "Remote Code Execution (RCE)",
                "exploitability": "proof_of_concept",
                "affected_code": '''// Vulnerable pattern in babel transformation
traverse(ast, {
  StringLiteral(path) {
    // Malicious code can be injected here
    eval(path.node.value); // DANGEROUS!
  }
});''',
                "fix_diff": '''- "@babel/traverse": "^7.22.0"
+ "@babel/traverse": "^7.23.2"''',
                "remediation_steps": [
                    "Update @babel/traverse to version 7.23.2 or later",
                    "Review any custom babel plugins for similar patterns",
                    "Run security tests after update",
                    "Consider using SRI for CDN-delivered babel packages"
                ],
                "references": [
                    "https://github.com/advisories/GHSA-c427-hjc3-wrfw",
                    "https://nvd.nist.gov/vuln/detail/CVE-2023-45133"
                ]
            },
            "dependency_tree": {
                "direct_dependencies": [
                    {
                        "name": "express",
                        "version": "4.18.2",
                        "vulnerabilities": 0,
                        "transitive_count": 31
                    },
                    {
                        "name": "@babel/core",
                        "version": "7.23.0",
                        "vulnerabilities": 1,
                        "transitive_count": 15,
                        "vulnerable_transitive": ["@babel/traverse"]
                    },
                    {
                        "name": "jsonwebtoken",
                        "version": "9.0.2",
                        "vulnerabilities": 0,
                        "transitive_count": 8
                    }
                ],
                "vulnerability_path": [
                    "@babel/core@7.23.0",
                    "→ @babel/traverse@7.22.0 (VULNERABLE)"
                ]
            },
            "automated_fixes": {
                "available": True,
                "patch_command": "npm update @babel/traverse",
                "breaking_changes": False,
                "confidence": "high"
            }
        }
    }