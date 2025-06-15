"""
Intelligent ChatOps bot for build diagnostics and automation
"""
import asyncio
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import structlog
from cachetools import TTLCache
import uuid

from src.integrations.gitlab_client import get_gitlab_client
from src.integrations.gemini_client import get_gemini_client
from src.features.pipeline_optimizer import get_pipeline_optimizer
from src.features.mr_triage import get_mr_triage_system

logger = structlog.get_logger(__name__)

class ChatAction(Enum):
    """Types of chat actions the bot can perform"""
    DIAGNOSE_BUILD = "diagnose_build"
    FIX_PIPELINE = "fix_pipeline"
    ANALYZE_MR = "analyze_mr"
    EXPLAIN_FAILURE = "explain_failure"
    SUGGEST_OPTIMIZATION = "suggest_optimization"
    PROVIDE_DOCS = "provide_docs"
    ESCALATE_ISSUE = "escalate_issue"

class DiagnosisConfidence(Enum):
    """Confidence levels for diagnostics"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ChatMessage:
    """Chat message structure"""
    id: str
    user_id: str
    project_id: int
    channel: str  # slack, teams, gitlab_comments, etc.
    content: str
    timestamp: datetime
    context: Dict[str, Any]  # Pipeline ID, MR ID, etc.

@dataclass
class BotResponse:
    """Bot response structure"""
    message_id: str
    response_text: str
    action_taken: Optional[ChatAction]
    confidence: DiagnosisConfidence
    suggested_actions: List[str]
    attachments: List[Dict[str, Any]]  # Code snippets, logs, etc.
    escalation_needed: bool

@dataclass
class BuildDiagnosis:
    """Build failure diagnosis"""
    pipeline_id: int
    failure_type: str
    root_cause: str
    failed_jobs: List[str]
    error_patterns: List[str]
    fix_suggestions: List[str]
    confidence: DiagnosisConfidence
    estimated_fix_time: str

class ChatOpsBot:
    """Intelligent ChatOps bot for build diagnostics"""
    
    def __init__(self):
        self.gitlab_client = get_gitlab_client()
        self.gemini_client = get_gemini_client()
        self.pipeline_optimizer = get_pipeline_optimizer()
        self.mr_triage = get_mr_triage_system()
        
        # Conversation cache
        self.conversation_cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour
        
        # Command patterns
        self.command_patterns = {
            'diagnose_build': [
                r'(?:diagnose|debug|analyze|check) (?:build|pipeline|job) (?:#|id )?(\d+)',
                r'(?:what|why).{0,20}(?:failed|failing|broken|error)',
                r'build (?:#|id )?(\d+) (?:failed|failing|broken)',
                r'pipeline (?:#|id )?(\d+) (?:failed|failing|broken)'
            ],
            'fix_pipeline': [
                r'(?:fix|repair|solve) (?:build|pipeline|job)',
                r'how (?:to |can I )?fix (?:this|the) (?:build|pipeline|error)',
                r'help (?:me )?fix (?:build|pipeline) (?:#|id )?(\d+)'
            ],
            'analyze_mr': [
                r'(?:analyze|review|check) (?:mr|merge request) (?:#|!)?(\d+)',
                r'(?:what|how) (?:about|is) (?:mr|merge request) (?:#|!)?(\d+)',
                r'review (?:mr|merge request) (?:#|!)?(\d+)'
            ],
            'explain_failure': [
                r'(?:explain|tell me|what is) (?:this |the )?(?:error|failure|problem)',
                r'(?:why|how) (?:did |is )(?:this|it) (?:fail|break|error)',
                r'what (?:went |is )wrong'
            ],
            'suggest_optimization': [
                r'(?:optimize|improve|speed up) (?:build|pipeline|ci)',
                r'(?:make|how to make) (?:build|pipeline) faster',
                r'optimization (?:suggestions|recommendations|tips)'
            ]
        }
        
        # Error pattern recognition
        self.error_patterns = {
            'dependency_issues': [
                r'npm ERR!.*ERESOLVE',
                r'Could not find or load main class',
                r'ModuleNotFoundError: No module named',
                r'package .* does not exist',
                r'Gemfile\.lock.*bundler'
            ],
            'test_failures': [
                r'\d+ failing',
                r'Test suite failed',
                r'AssertionError',
                r'Test.*failed',
                r'Expected.*but was'
            ],
            'build_failures': [
                r'Build failed',
                r'compilation terminated',
                r'Error: Command failed',
                r'make: \*\*\* \[.*\] Error',
                r'fatal error:'
            ],
            'deployment_issues': [
                r'deployment failed',
                r'kubectl.*error',
                r'docker.*permission denied',
                r'connection refused.*:443',
                r'timeout.*deployment'
            ],
            'resource_issues': [
                r'out of memory',
                r'disk space',
                r'resource.*quota.*exceeded',
                r'CPU.*limit.*exceeded',
                r'killed.*OOMKilled'
            ]
        }
        
        # Fix templates
        self.fix_templates = {
            'dependency_issues': {
                'npm': [
                    "Try clearing npm cache: `npm cache clean --force`",
                    "Delete node_modules and reinstall: `rm -rf node_modules && npm install`",
                    "Check for conflicting peer dependencies in package.json"
                ],
                'python': [
                    "Update pip: `pip install --upgrade pip`",
                    "Try installing with --no-cache-dir flag",
                    "Check if the package name/version exists on PyPI"
                ],
                'java': [
                    "Clean and rebuild: `mvn clean compile`",
                    "Check if all dependencies are available in repositories",
                    "Verify Java version compatibility"
                ]
            },
            'test_failures': [
                "Review failing test output for specific assertion errors",
                "Check if test data/fixtures are properly set up",
                "Verify test environment configuration",
                "Run tests locally to reproduce the issue"
            ],
            'build_failures': [
                "Check compilation errors in the build log",
                "Verify all required dependencies are installed",
                "Ensure build tools versions are compatible",
                "Check for syntax errors in configuration files"
            ],
            'deployment_issues': [
                "Verify deployment target connectivity",
                "Check authentication credentials and permissions",
                "Review resource limits and quotas",
                "Validate deployment configuration syntax"
            ],
            'resource_issues': [
                "Increase memory/CPU limits in CI configuration",
                "Optimize resource usage in the application",
                "Consider using smaller Docker images",
                "Review parallel job settings"
            ]
        }
    
    async def process_message(self, message: ChatMessage) -> BotResponse:
        """Process incoming chat message and generate response"""
        
        logger.info(
            "Processing chat message",
            message_id=message.id,
            user_id=message.user_id,
            project_id=message.project_id,
            content_length=len(message.content)
        )
        
        try:
            # Try AI-powered response first if available
            if await self.gemini_client.is_available():
                try:
                    logger.info("Using AI-powered ChatOps response", message_id=message.id)
                    ai_response = await self.gemini_client.process_chatops_message(
                        message.content, 
                        message.context
                    )
                    response = self._convert_ai_chatops_response(ai_response, message)
                except Exception as e:
                    logger.warning("AI ChatOps failed, using fallback", error=str(e))
                    response = await self._fallback_processing(message)
            else:
                # Fallback to pattern-based processing
                logger.info("Using pattern-based ChatOps response", message_id=message.id)
                response = await self._fallback_processing(message)
            
            # Cache conversation
            self.conversation_cache[message.id] = {
                'message': message,
                'response': response,
                'timestamp': datetime.utcnow()
            }
            
            logger.info(
                "Chat message processed",
                message_id=message.id,
                action=response.action_taken.value if response.action_taken else "unknown",
                confidence=response.confidence.value,
                escalation=response.escalation_needed
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Failed to process chat message",
                message_id=message.id,
                error=str(e),
                exc_info=True
            )
            
            return BotResponse(
                message_id=str(uuid.uuid4()),
                response_text="Sorry, I encountered an error processing your request. Please try again or contact support.",
                action_taken=None,
                confidence=DiagnosisConfidence.LOW,
                suggested_actions=["Contact support", "Try rephrasing your question"],
                attachments=[],
                escalation_needed=True
            )
    
    def _parse_command(self, content: str) -> Tuple[Optional[ChatAction], Dict[str, Any]]:
        """Parse chat message to determine action and extract relevant data"""
        
        content = content.lower().strip()
        extracted_data = {}
        
        for action_name, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    # Extract IDs from the match
                    if match.groups():
                        if 'build' in pattern or 'pipeline' in pattern:
                            extracted_data['pipeline_id'] = int(match.group(1))
                        elif 'mr' in pattern or 'merge request' in pattern:
                            extracted_data['mr_iid'] = int(match.group(1))
                    
                    return ChatAction(action_name), extracted_data
        
        return None, extracted_data
    
    async def _diagnose_build(self, message: ChatMessage, context: Dict[str, Any]) -> BotResponse:
        """Diagnose build failure"""
        
        pipeline_id = context.get('pipeline_id')
        if not pipeline_id:
            # Look for recent failed pipelines
            pipelines = await self.gitlab_client.list_project_pipelines(
                project_id=message.project_id,
                status='failed',
                per_page=5
            )
            
            if not pipelines:
                return BotResponse(
                    message_id=str(uuid.uuid4()),
                    response_text="I couldn't find any recent failed pipelines. Could you specify a pipeline ID?",
                    action_taken=ChatAction.DIAGNOSE_BUILD,
                    confidence=DiagnosisConfidence.LOW,
                    suggested_actions=["Specify pipeline ID", "Check pipeline status"],
                    attachments=[],
                    escalation_needed=False
                )
            
            pipeline_id = pipelines[0]['id']
        
        # Get pipeline details
        pipeline = await self.gitlab_client.get_pipeline(message.project_id, pipeline_id)
        if not pipeline:
            return BotResponse(
                message_id=str(uuid.uuid4()),
                response_text=f"Pipeline #{pipeline_id} not found.",
                action_taken=ChatAction.DIAGNOSE_BUILD,
                confidence=DiagnosisConfidence.LOW,
                suggested_actions=["Check pipeline ID", "Verify project access"],
                attachments=[],
                escalation_needed=False
            )
        
        # Get failed jobs
        jobs = await self.gitlab_client.get_pipeline_jobs(message.project_id, pipeline_id)
        failed_jobs = [job for job in jobs if job.get('status') == 'failed']
        
        # Analyze failures
        diagnosis = await self._analyze_build_failure(pipeline, failed_jobs)
        
        # Generate response
        response_text = f"🔍 **Build Diagnosis for Pipeline #{pipeline_id}**\n\n"
        response_text += f"**Status**: {pipeline.get('status', 'unknown').title()}\n"
        response_text += f"**Failure Type**: {diagnosis.failure_type}\n"
        response_text += f"**Root Cause**: {diagnosis.root_cause}\n\n"
        
        if diagnosis.failed_jobs:
            response_text += f"**Failed Jobs**: {', '.join(diagnosis.failed_jobs)}\n\n"
        
        if diagnosis.fix_suggestions:
            response_text += "**Suggested Fixes**:\n"
            for i, fix in enumerate(diagnosis.fix_suggestions[:3], 1):
                response_text += f"{i}. {fix}\n"
            response_text += "\n"
        
        response_text += f"**Estimated Fix Time**: {diagnosis.estimated_fix_time}\n"
        response_text += f"**Confidence**: {diagnosis.confidence.value.title()}"
        
        # Create attachments with logs
        attachments = []
        for job in failed_jobs[:2]:  # Limit to first 2 failed jobs
            job_log = await self._get_job_log_excerpt(message.project_id, job.get('id'))
            if job_log:
                attachments.append({
                    'title': f"Log excerpt from {job.get('name', 'unknown job')}",
                    'content': job_log,
                    'type': 'code'
                })
        
        return BotResponse(
            message_id=str(uuid.uuid4()),
            response_text=response_text,
            action_taken=ChatAction.DIAGNOSE_BUILD,
            confidence=diagnosis.confidence,
            suggested_actions=diagnosis.fix_suggestions[:3],
            attachments=attachments,
            escalation_needed=diagnosis.confidence == DiagnosisConfidence.LOW
        )
    
    async def _analyze_build_failure(self, pipeline: Dict, failed_jobs: List[Dict]) -> BuildDiagnosis:
        """Analyze build failure and determine root cause"""
        
        if not failed_jobs:
            return BuildDiagnosis(
                pipeline_id=pipeline.get('id', 0),
                failure_type="Unknown",
                root_cause="No failed jobs found",
                failed_jobs=[],
                error_patterns=[],
                fix_suggestions=["Check pipeline configuration"],
                confidence=DiagnosisConfidence.LOW,
                estimated_fix_time="Unknown"
            )
        
        failed_job_names = [job.get('name', 'unknown') for job in failed_jobs]
        error_patterns = []
        failure_type = "Build Failure"
        
        # Analyze job logs for error patterns
        for job in failed_jobs[:3]:  # Analyze first 3 failed jobs
            job_log = await self._get_job_log_excerpt(pipeline.get('id'), job.get('id'))
            if job_log:
                for error_type, patterns in self.error_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, job_log, re.IGNORECASE):
                            error_patterns.append(error_type)
                            failure_type = error_type.replace('_', ' ').title()
                            break
        
        # Determine root cause
        if 'dependency_issues' in error_patterns:
            root_cause = "Dependency resolution or installation failed"
        elif 'test_failures' in error_patterns:
            root_cause = "Unit/integration tests are failing"
        elif 'build_failures' in error_patterns:
            root_cause = "Compilation or build process failed"
        elif 'deployment_issues' in error_patterns:
            root_cause = "Deployment configuration or target issues"
        elif 'resource_issues' in error_patterns:
            root_cause = "Insufficient resources (memory/CPU/disk)"
        else:
            root_cause = "Unable to determine specific cause from logs"
        
        # Generate fix suggestions
        fix_suggestions = []
        for error_type in set(error_patterns):
            if error_type in self.fix_templates:
                if isinstance(self.fix_templates[error_type], dict):
                    # Language-specific fixes
                    fix_suggestions.extend(self.fix_templates[error_type].get('general', []))
                else:
                    fix_suggestions.extend(self.fix_templates[error_type])
        
        if not fix_suggestions:
            fix_suggestions = [
                "Review the full job log for specific error messages",
                "Check recent changes that might have caused the failure",
                "Verify CI/CD configuration syntax"
            ]
        
        # Estimate fix time
        if error_patterns:
            if any(t in error_patterns for t in ['dependency_issues', 'resource_issues']):
                estimated_fix_time = "15-30 minutes"
            elif 'test_failures' in error_patterns:
                estimated_fix_time = "30-60 minutes"
            else:
                estimated_fix_time = "1-2 hours"
        else:
            estimated_fix_time = "Unknown - requires investigation"
        
        # Determine confidence
        confidence = DiagnosisConfidence.HIGH if error_patterns else DiagnosisConfidence.LOW
        if len(error_patterns) > 2:
            confidence = DiagnosisConfidence.MEDIUM  # Multiple issues = less certain
        
        return BuildDiagnosis(
            pipeline_id=pipeline.get('id', 0),
            failure_type=failure_type,
            root_cause=root_cause,
            failed_jobs=failed_job_names,
            error_patterns=error_patterns,
            fix_suggestions=fix_suggestions,
            confidence=confidence,
            estimated_fix_time=estimated_fix_time
        )
    
    async def _get_job_log_excerpt(self, project_id: int, job_id: int) -> Optional[str]:
        """Get relevant excerpt from job log"""
        try:
            # This would get job logs from GitLab API
            # For now, return a placeholder
            return "Sample error log - would fetch actual logs from GitLab API"
        except Exception as e:
            logger.warning("Failed to fetch job log", job_id=job_id, error=str(e))
            return None
    
    async def _suggest_pipeline_fix(self, message: ChatMessage, context: Dict[str, Any]) -> BotResponse:
        """Suggest pipeline fixes based on optimization analysis"""
        
        try:
            analysis = await self.pipeline_optimizer.analyze_pipeline_performance(
                project_id=message.project_id,
                pipeline_id=context.get('pipeline_id')
            )
            
            response_text = "🔧 **Pipeline Optimization Suggestions**\n\n"
            
            if analysis.recommendations:
                response_text += "**Top Recommendations**:\n"
                for i, rec in enumerate(analysis.recommendations[:3], 1):
                    impact = rec.estimated_impact.get('duration_reduction', 0) * 100
                    response_text += f"{i}. {rec.description}\n"
                    response_text += f"   - Estimated improvement: {impact:.0f}%\n"
                    response_text += f"   - Difficulty: {rec.implementation_difficulty}\n\n"
            
            response_text += f"**Current avg duration**: {analysis.current_metrics.avg_duration:.1f} minutes\n"
            response_text += f"**Predicted improvement**: {analysis.predicted_metrics.avg_duration:.1f} minutes\n"
            response_text += f"**Optimization score**: {analysis.overall_score:.0f}/100"
            
            suggested_actions = [rec.description for rec in analysis.recommendations[:3]]
            
            return BotResponse(
                message_id=str(uuid.uuid4()),
                response_text=response_text,
                action_taken=ChatAction.FIX_PIPELINE,
                confidence=DiagnosisConfidence.HIGH,
                suggested_actions=suggested_actions,
                attachments=[],
                escalation_needed=False
            )
            
        except Exception as e:
            logger.error("Pipeline fix suggestion failed", error=str(e))
            return BotResponse(
                message_id=str(uuid.uuid4()),
                response_text="I couldn't analyze the pipeline right now. Please try again later.",
                action_taken=ChatAction.FIX_PIPELINE,
                confidence=DiagnosisConfidence.LOW,
                suggested_actions=["Retry later", "Check pipeline manually"],
                attachments=[],
                escalation_needed=True
            )
    
    async def _analyze_merge_request(self, message: ChatMessage, context: Dict[str, Any]) -> BotResponse:
        """Analyze merge request using AI triage"""
        
        mr_iid = context.get('mr_iid')
        if not mr_iid:
            return BotResponse(
                message_id=str(uuid.uuid4()),
                response_text="Please specify a merge request ID (e.g., 'analyze MR !123')",
                action_taken=ChatAction.ANALYZE_MR,
                confidence=DiagnosisConfidence.LOW,
                suggested_actions=["Specify MR ID"],
                attachments=[],
                escalation_needed=False
            )
        
        try:
            analysis = await self.mr_triage.analyze_merge_request(
                project_id=message.project_id,
                mr_iid=mr_iid
            )
            
            response_text = f"📋 **MR Analysis for !{mr_iid}**\n\n"
            response_text += f"**Risk Level**: {analysis.risk_level.value.title()}\n"
            response_text += f"**Type**: {analysis.mr_type.value.title()}\n"
            response_text += f"**Complexity**: {analysis.complexity.value.title()}\n"
            response_text += f"**Est. Review Time**: {analysis.estimated_review_hours:.1f} hours\n\n"
            
            if analysis.risk_factors:
                response_text += "**Risk Factors**:\n"
                for factor in analysis.risk_factors[:3]:
                    response_text += f"- {factor}\n"
                response_text += "\n"
            
            if analysis.labels:
                response_text += f"**Suggested Labels**: {', '.join(analysis.labels)}\n\n"
            
            response_text += f"**Confidence**: {analysis.confidence_score:.0%}"
            
            return BotResponse(
                message_id=str(uuid.uuid4()),
                response_text=response_text,
                action_taken=ChatAction.ANALYZE_MR,
                confidence=DiagnosisConfidence.HIGH if analysis.confidence_score > 0.7 else DiagnosisConfidence.MEDIUM,
                suggested_actions=analysis.labels[:3],
                attachments=[],
                escalation_needed=analysis.risk_level.name == "CRITICAL"
            )
            
        except Exception as e:
            logger.error("MR analysis failed", mr_iid=mr_iid, error=str(e))
            return BotResponse(
                message_id=str(uuid.uuid4()),
                response_text=f"I couldn't analyze MR !{mr_iid}. It might not exist or I don't have access.",
                action_taken=ChatAction.ANALYZE_MR,
                confidence=DiagnosisConfidence.LOW,
                suggested_actions=["Check MR ID", "Verify access permissions"],
                attachments=[],
                escalation_needed=False
            )
    
    async def _explain_failure(self, message: ChatMessage, context: Dict[str, Any]) -> BotResponse:
        """Explain general failure patterns"""
        
        response_text = "🤔 **Common Build Failure Explanations**\n\n"
        response_text += "**Dependency Issues** (40% of failures):\n"
        response_text += "- Package not found or version conflicts\n"
        response_text += "- Network issues during download\n"
        response_text += "- Cache corruption\n\n"
        
        response_text += "**Test Failures** (30% of failures):\n"
        response_text += "- Code changes broke existing functionality\n"
        response_text += "- Test environment issues\n"
        response_text += "- Flaky/unreliable tests\n\n"
        
        response_text += "**Configuration Issues** (20% of failures):\n"
        response_text += "- Syntax errors in CI config\n"
        response_text += "- Missing environment variables\n"
        response_text += "- Incorrect paths or commands\n\n"
        
        response_text += "**Resource Issues** (10% of failures):\n"
        response_text += "- Out of memory or disk space\n"
        response_text += "- Network timeouts\n"
        response_text += "- Service unavailability"
        
        return BotResponse(
            message_id=str(uuid.uuid4()),
            response_text=response_text,
            action_taken=ChatAction.EXPLAIN_FAILURE,
            confidence=DiagnosisConfidence.MEDIUM,
            suggested_actions=[
                "Check specific pipeline logs",
                "Review recent changes",
                "Verify configuration"
            ],
            attachments=[],
            escalation_needed=False
        )
    
    async def _suggest_optimizations(self, message: ChatMessage, context: Dict[str, Any]) -> BotResponse:
        """Suggest general pipeline optimizations"""
        
        response_text = "⚡ **Pipeline Optimization Tips**\n\n"
        response_text += "**Quick Wins**:\n"
        response_text += "- Add caching for dependencies (node_modules, .m2, etc.)\n"
        response_text += "- Use smaller, optimized Docker images\n"
        response_text += "- Parallelize independent jobs\n\n"
        
        response_text += "**Medium Impact**:\n"
        response_text += "- Implement conditional job execution\n"
        response_text += "- Optimize test execution (parallel, selective)\n"
        response_text += "- Review resource allocation\n\n"
        
        response_text += "**Advanced**:\n"
        response_text += "- Pipeline stage reordering\n"
        response_text += "- Build artifact optimization\n"
        response_text += "- Advanced caching strategies\n\n"
        
        response_text += "💡 For specific recommendations, ask me to analyze a particular pipeline!"
        
        return BotResponse(
            message_id=str(uuid.uuid4()),
            response_text=response_text,
            action_taken=ChatAction.SUGGEST_OPTIMIZATION,
            confidence=DiagnosisConfidence.HIGH,
            suggested_actions=[
                "Analyze specific pipeline",
                "Implement caching",
                "Add parallelization"
            ],
            attachments=[],
            escalation_needed=False
        )
    
    async def _provide_help(self, message: ChatMessage) -> BotResponse:
        """Provide help information"""
        
        response_text = "🤖 **GitAIOps ChatOps Bot Help**\n\n"
        response_text += "**What I can do**:\n"
        response_text += "- `diagnose build #123` - Analyze failed pipelines\n"
        response_text += "- `analyze MR !456` - Review merge requests\n"
        response_text += "- `fix pipeline` - Suggest optimizations\n"
        response_text += "- `explain failure` - Common failure patterns\n"
        response_text += "- `optimize build` - Performance improvement tips\n\n"
        
        response_text += "**Examples**:\n"
        response_text += "- \"Why did build #123 fail?\"\n"
        response_text += "- \"Analyze MR !456\"\n"  
        response_text += "- \"How to make the pipeline faster?\"\n"
        response_text += "- \"Fix the broken build\"\n\n"
        
        response_text += "Just describe what you need help with in natural language!"
        
        return BotResponse(
            message_id=str(uuid.uuid4()),
            response_text=response_text,
            action_taken=ChatAction.PROVIDE_DOCS,
            confidence=DiagnosisConfidence.HIGH,
            suggested_actions=[
                "Try a specific command",
                "Ask about a failed build",
                "Request MR analysis"
            ],
            attachments=[],
            escalation_needed=False
        )
    
    def _convert_ai_chatops_response(self, ai_response: Dict[str, Any], message: ChatMessage) -> BotResponse:
        """Convert AI ChatOps response to BotResponse object"""
        
        # Map AI intent to our ChatAction enum
        intent_map = {
            "diagnose_build": ChatAction.DIAGNOSE_BUILD,
            "analyze_mr": ChatAction.ANALYZE_MR,
            "explain_error": ChatAction.EXPLAIN_FAILURE,
            "optimize_pipeline": ChatAction.SUGGEST_OPTIMIZATION,
            "provide_help": ChatAction.PROVIDE_DOCS,
            "unknown": None
        }
        
        confidence_map = {
            "high": DiagnosisConfidence.HIGH,
            "medium": DiagnosisConfidence.MEDIUM,
            "low": DiagnosisConfidence.LOW
        }
        
        action = intent_map.get(ai_response.get("intent", "unknown"))
        confidence_str = str(ai_response.get("confidence", 0.5))
        
        # Convert confidence number to string
        if isinstance(ai_response.get("confidence"), (int, float)):
            conf_val = float(ai_response.get("confidence", 0.5))
            if conf_val >= 0.7:
                confidence_str = "high"
            elif conf_val >= 0.4:
                confidence_str = "medium"
            else:
                confidence_str = "low"
        
        confidence = confidence_map.get(confidence_str, DiagnosisConfidence.MEDIUM)
        
        return BotResponse(
            message_id=str(uuid.uuid4()),
            response_text=ai_response.get("response_text", "I'm processing your request..."),
            action_taken=action,
            confidence=confidence,
            suggested_actions=ai_response.get("suggested_actions", []),
            attachments=[],
            escalation_needed=ai_response.get("requires_escalation", False)
        )
    
    async def _fallback_processing(self, message: ChatMessage) -> BotResponse:
        """Fallback to pattern-based processing when AI is unavailable"""
        
        # Parse command and context
        action, extracted_data = self._parse_command(message.content)
        
        # Add message context
        context = {**message.context, **extracted_data}
        
        # Generate response based on action
        if action == ChatAction.DIAGNOSE_BUILD:
            return await self._diagnose_build(message, context)
        elif action == ChatAction.FIX_PIPELINE:
            return await self._suggest_pipeline_fix(message, context)
        elif action == ChatAction.ANALYZE_MR:
            return await self._analyze_merge_request(message, context)
        elif action == ChatAction.EXPLAIN_FAILURE:
            return await self._explain_failure(message, context)
        elif action == ChatAction.SUGGEST_OPTIMIZATION:
            return await self._suggest_optimizations(message, context)
        else:
            return await self._provide_help(message)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ChatOps bot statistics"""
        return {
            "conversation_cache_size": len(self.conversation_cache),
            "supported_actions": [action.value for action in ChatAction],
            "error_patterns_count": sum(len(patterns) for patterns in self.error_patterns.values()),
            "fix_templates_count": len(self.fix_templates),
            "command_patterns_count": sum(len(patterns) for patterns in self.command_patterns.values())
        }

# Global instance
_chatops_bot: Optional[ChatOpsBot] = None

def get_chatops_bot() -> ChatOpsBot:
    """Get or create ChatOps bot instance"""
    global _chatops_bot
    if _chatops_bot is None:
        _chatops_bot = ChatOpsBot()
    return _chatops_bot