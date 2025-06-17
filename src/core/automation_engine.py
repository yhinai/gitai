#!/usr/bin/env python3
"""
Automation Engine for GitAIOps Platform
Orchestrates intelligent workflows, automated triggers, and smart scheduling
"""
import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging
from pathlib import Path

try:
    from .unified_event_system import EventType, Priority, emit_event, on_event
except ImportError:
    # Define minimal classes if unified_event_system is not available
    from enum import Enum
    
    class EventType(Enum):
        GITLAB_MR_CREATED = "gitlab.mr.created"
        GITLAB_PIPELINE_STARTED = "gitlab.pipeline.started"
        ALERT_TRIGGERED = "alert.triggered"
        SECURITY_VULNERABILITY_FOUND = "security.vulnerability.found"
        AI_ANALYSIS_STARTED = "ai.analysis.started"
        AI_ANALYSIS_PROGRESS = "ai.analysis.progress"
        AI_ANALYSIS_COMPLETED = "ai.analysis.completed"
        AI_ANALYSIS_FAILED = "ai.analysis.failed"
    
    class Priority(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    async def emit_event(event_type, data, **kwargs):
        logger.info(f"Event emitted: {event_type.value} - {data}")
    
    def on_event(event_type):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TriggerType(Enum):
    EVENT_BASED = "event_based"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    CONDITIONAL = "conditional"

@dataclass
class WorkflowStep:
    id: str
    name: str
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    timeout: int = 300  # 5 minutes default
    retry_count: int = 3
    condition: Optional[str] = None  # Python expression for conditional execution
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class Workflow:
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    trigger_type: TriggerType
    trigger_config: Dict[str, Any]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()

class AutomationEngine:
    """Intelligent workflow orchestration and automation engine"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.running_workflows: Dict[str, asyncio.Task] = {}
        self.scheduled_workflows: Dict[str, asyncio.Task] = {}
        self.workflow_templates: Dict[str, Workflow] = {}
        self.running = False
        
        # Performance metrics
        self.metrics = {
            "workflows_executed": 0,
            "workflows_successful": 0,
            "workflows_failed": 0,
            "automation_efficiency": 0.0,
            "average_execution_time": 0.0
        }
        
        # Setup built-in workflows
        self._setup_builtin_workflows()
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _setup_builtin_workflows(self):
        """Setup built-in intelligent workflows"""
        
        # Smart MR Analysis Workflow
        mr_analysis_workflow = Workflow(
            id="smart_mr_analysis",
            name="Smart Merge Request Analysis",
            description="Automatically analyze MRs with AI, security scanning, and testing",
            trigger_type=TriggerType.EVENT_BASED,
            trigger_config={"event_type": "gitlab.mr.created"},
            steps=[
                WorkflowStep(
                    id="fetch_mr_details",
                    name="Fetch MR Details",
                    action="fetch_gitlab_mr",
                    parameters={"include_diff": True, "include_files": True}
                ),
                WorkflowStep(
                    id="ai_analysis",
                    name="AI Code Analysis",
                    action="run_ai_analysis",
                    parameters={"analysis_type": "merge_request"},
                    dependencies=["fetch_mr_details"]
                ),
                WorkflowStep(
                    id="security_scan",
                    name="Security Vulnerability Scan",
                    action="run_security_scan",
                    parameters={"scan_type": "incremental"},
                    dependencies=["fetch_mr_details"]
                ),
                WorkflowStep(
                    id="performance_check",
                    name="Performance Impact Analysis",
                    action="run_performance_analysis",
                    parameters={"analysis_type": "differential"},
                    dependencies=["fetch_mr_details"]
                ),
                WorkflowStep(
                    id="generate_report",
                    name="Generate Analysis Report",
                    action="generate_mr_report",
                    parameters={"include_recommendations": True},
                    dependencies=["ai_analysis", "security_scan", "performance_check"]
                ),
                WorkflowStep(
                    id="auto_approve_or_flag",
                    name="Auto Approval or Flagging",
                    action="auto_decision",
                    parameters={"decision_threshold": 0.85},
                    dependencies=["generate_report"],
                    condition="risk_level == 'low' and confidence > 0.9"
                )
            ]
        )
        
        # Continuous Quality Monitoring
        quality_monitoring_workflow = Workflow(
            id="continuous_quality_monitoring",
            name="Continuous Quality Monitoring",
            description="Regular automated quality checks and monitoring",
            trigger_type=TriggerType.SCHEDULED,
            trigger_config={"schedule": "0 */2 * * *"},  # Every 2 hours
            steps=[
                WorkflowStep(
                    id="security_sweep",
                    name="Security Sweep",
                    action="run_security_scan",
                    parameters={"scan_type": "full", "deep_scan": True}
                ),
                WorkflowStep(
                    id="performance_baseline",
                    name="Performance Baseline Check",
                    action="run_performance_analysis",
                    parameters={"analysis_type": "baseline", "compare_historical": True}
                ),
                WorkflowStep(
                    id="code_quality_metrics",
                    name="Code Quality Metrics",
                    action="calculate_quality_metrics",
                    parameters={"include_trends": True}
                ),
                WorkflowStep(
                    id="dependency_audit",
                    name="Dependency Security Audit",
                    action="audit_dependencies",
                    parameters={"check_vulnerabilities": True, "check_licenses": True}
                ),
                WorkflowStep(
                    id="generate_quality_report",
                    name="Generate Quality Report",
                    action="generate_quality_dashboard",
                    parameters={"send_notifications": True},
                    dependencies=["security_sweep", "performance_baseline", "code_quality_metrics", "dependency_audit"]
                )
            ]
        )
        
        # Smart Testing Workflow
        smart_testing_workflow = Workflow(
            id="smart_testing_workflow",
            name="Smart Testing Workflow",
            description="Intelligent test execution based on code changes",
            trigger_type=TriggerType.EVENT_BASED,
            trigger_config={"event_type": "gitlab.pipeline.started"},
            steps=[
                WorkflowStep(
                    id="analyze_changes",
                    name="Analyze Code Changes",
                    action="analyze_code_changes",
                    parameters={"include_impact_analysis": True}
                ),
                WorkflowStep(
                    id="select_tests",
                    name="Smart Test Selection",
                    action="select_relevant_tests",
                    parameters={"use_ai_prediction": True, "include_regression": True},
                    dependencies=["analyze_changes"]
                ),
                WorkflowStep(
                    id="parallel_testing",
                    name="Parallel Test Execution",
                    action="run_test_suite",
                    parameters={"parallel": True, "optimize_order": True},
                    dependencies=["select_tests"]
                ),
                WorkflowStep(
                    id="ai_test_analysis",
                    name="AI Test Result Analysis",
                    action="analyze_test_results",
                    parameters={"identify_patterns": True, "suggest_improvements": True},
                    dependencies=["parallel_testing"]
                ),
                WorkflowStep(
                    id="auto_fix_suggestions",
                    name="Auto-Fix Suggestions",
                    action="generate_fix_suggestions",
                    parameters={"auto_apply_safe_fixes": True},
                    dependencies=["ai_test_analysis"],
                    condition="test_failures < 3 and confidence > 0.8"
                )
            ]
        )
        
        # Emergency Response Workflow
        emergency_response_workflow = Workflow(
            id="emergency_response",
            name="Emergency Response Workflow",
            description="Automated response to critical issues and alerts",
            trigger_type=TriggerType.EVENT_BASED,
            trigger_config={"event_type": "alert.triggered", "priority": "critical"},
            steps=[
                WorkflowStep(
                    id="assess_severity",
                    name="Assess Issue Severity",
                    action="assess_issue_severity",
                    parameters={"use_ai_classification": True}
                ),
                WorkflowStep(
                    id="auto_diagnostics",
                    name="Auto Diagnostics",
                    action="run_diagnostics",
                    parameters={"deep_scan": True, "collect_logs": True},
                    dependencies=["assess_severity"]
                ),
                WorkflowStep(
                    id="notify_team",
                    name="Notify Response Team",
                    action="send_emergency_notifications",
                    parameters={"escalation_chain": True, "include_context": True},
                    dependencies=["assess_severity"]
                ),
                WorkflowStep(
                    id="auto_remediation",
                    name="Auto Remediation",
                    action="attempt_auto_fix",
                    parameters={"safe_fixes_only": True, "create_backup": True},
                    dependencies=["auto_diagnostics"],
                    condition="severity == 'high' and auto_fix_confidence > 0.9"
                ),
                WorkflowStep(
                    id="create_incident",
                    name="Create Incident Record",
                    action="create_incident_record",
                    parameters={"include_timeline": True, "attach_diagnostics": True},
                    dependencies=["notify_team", "auto_diagnostics"]
                )
            ]
        )
        
        # Store templates
        self.workflow_templates = {
            "smart_mr_analysis": mr_analysis_workflow,
            "continuous_quality_monitoring": quality_monitoring_workflow,
            "smart_testing_workflow": smart_testing_workflow,
            "emergency_response": emergency_response_workflow
        }
    
    def _setup_event_handlers(self):
        """Setup event handlers for automated workflow triggers"""
        
        @on_event(EventType.GITLAB_MR_CREATED)
        async def handle_mr_created(event):
            # Auto-trigger MR analysis workflow
            workflow_id = await self.trigger_workflow(
                "smart_mr_analysis",
                context={"mr_id": event.data.get("mr_id"), "event_id": event.id}
            )
            logger.info(f"Auto-triggered MR analysis workflow: {workflow_id}")
        
        @on_event(EventType.GITLAB_PIPELINE_STARTED)
        async def handle_pipeline_started(event):
            # Auto-trigger smart testing workflow
            workflow_id = await self.trigger_workflow(
                "smart_testing_workflow",
                context={"pipeline_id": event.data.get("pipeline_id"), "event_id": event.id}
            )
            logger.info(f"Auto-triggered testing workflow: {workflow_id}")
        
        @on_event(EventType.ALERT_TRIGGERED)
        async def handle_alert(event):
            if event.priority == Priority.CRITICAL:
                # Auto-trigger emergency response
                workflow_id = await self.trigger_workflow(
                    "emergency_response",
                    context={"alert_id": event.data.get("alert_id"), "event_id": event.id}
                )
                logger.info(f"Auto-triggered emergency response: {workflow_id}")
        
        @on_event(EventType.SECURITY_VULNERABILITY_FOUND)
        async def handle_vulnerability(event):
            severity = event.data.get("severity", "medium")
            if severity in ["high", "critical"]:
                # Auto-trigger security response
                await emit_event(EventType.ALERT_TRIGGERED, {
                    "alert_type": "security_vulnerability",
                    "severity": severity,
                    "vulnerability_id": event.data.get("vulnerability_id")
                }, priority=Priority.HIGH, source="automation_engine")
    
    async def trigger_workflow(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """Trigger a workflow from a template"""
        
        if template_name not in self.workflow_templates:
            raise ValueError(f"Workflow template '{template_name}' not found")
        
        # Create workflow instance from template
        template = self.workflow_templates[template_name]
        workflow_id = f"{template_name}_{uuid.uuid4().hex[:8]}"
        
        workflow = Workflow(
            id=workflow_id,
            name=template.name,
            description=template.description,
            steps=template.steps.copy(),
            trigger_type=template.trigger_type,
            trigger_config=template.trigger_config.copy()
        )
        
        # Add context to workflow
        if context:
            workflow.trigger_config["context"] = context
        
        # Store and execute workflow
        self.workflows[workflow_id] = workflow
        
        # Start workflow execution
        task = asyncio.create_task(self._execute_workflow(workflow))
        self.running_workflows[workflow_id] = task
        
        # Emit workflow started event
        await emit_event(EventType.AI_ANALYSIS_STARTED, {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "trigger_type": workflow.trigger_type.value,
            "context": context
        }, source="automation_engine")
        
        return workflow_id
    
    async def _execute_workflow(self, workflow: Workflow):
        """Execute a workflow with all its steps"""
        
        try:
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"Starting workflow: {workflow.name} ({workflow.id})")
            
            # Build dependency graph
            step_results = {}
            completed_steps = set()
            
            # Execute steps in dependency order
            while len(completed_steps) < len(workflow.steps):
                progress = len(completed_steps) / len(workflow.steps)
                
                # Emit progress update
                await emit_event(EventType.AI_ANALYSIS_PROGRESS, {
                    "workflow_id": workflow.id,
                    "progress": progress,
                    "completed_steps": len(completed_steps),
                    "total_steps": len(workflow.steps),
                    "current_step": "processing"
                }, source="automation_engine")
                
                # Find ready steps (dependencies satisfied)
                ready_steps = []
                for step in workflow.steps:
                    if step.id not in completed_steps:
                        dependencies_met = all(dep in completed_steps for dep in step.dependencies)
                        if dependencies_met:
                            # Check condition if present
                            if step.condition:
                                if self._evaluate_condition(step.condition, step_results):
                                    ready_steps.append(step)
                            else:
                                ready_steps.append(step)
                
                if not ready_steps:
                    # Deadlock or all steps completed
                    break
                
                # Execute ready steps in parallel
                step_tasks = []
                for step in ready_steps:
                    task = asyncio.create_task(self._execute_step(step, step_results, workflow))
                    step_tasks.append((step, task))
                
                # Wait for step completion
                for step, task in step_tasks:
                    try:
                        result = await task
                        step_results[step.id] = result
                        completed_steps.add(step.id)
                        
                        logger.info(f"Completed step: {step.name} in workflow {workflow.id}")
                        
                    except Exception as e:
                        logger.error(f"Step {step.name} failed in workflow {workflow.id}: {e}")
                        step_results[step.id] = {"error": str(e), "status": "failed"}
                        
                        # For now, continue with other steps
                        completed_steps.add(step.id)
            
            # Workflow completed
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now(timezone.utc).isoformat()
            workflow.result = step_results
            
            # Update metrics
            self.metrics["workflows_executed"] += 1
            self.metrics["workflows_successful"] += 1
            
            # Emit completion event
            await emit_event(EventType.AI_ANALYSIS_COMPLETED, {
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "execution_time": self._calculate_execution_time(workflow),
                "steps_completed": len(completed_steps),
                "result_summary": self._generate_result_summary(step_results)
            }, source="automation_engine")
            
            logger.info(f"Workflow completed successfully: {workflow.name} ({workflow.id})")
            
        except Exception as e:
            # Workflow failed
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now(timezone.utc).isoformat()
            workflow.error = str(e)
            
            # Update metrics
            self.metrics["workflows_executed"] += 1
            self.metrics["workflows_failed"] += 1
            
            # Emit failure event
            await emit_event(EventType.AI_ANALYSIS_FAILED, {
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "error": str(e),
                "execution_time": self._calculate_execution_time(workflow)
            }, source="automation_engine", priority=Priority.HIGH)
            
            logger.error(f"Workflow failed: {workflow.name} ({workflow.id}) - {e}")
            
        finally:
            # Cleanup
            if workflow.id in self.running_workflows:
                del self.running_workflows[workflow.id]
    
    async def _execute_step(self, step: WorkflowStep, context: Dict[str, Any], workflow: Workflow) -> Dict[str, Any]:
        """Execute a single workflow step"""
        
        start_time = time.time()
        
        try:
            logger.info(f"Executing step: {step.name} in workflow {workflow.id}")
            
            # Map action to actual implementation
            result = await self._perform_action(step.action, step.parameters, context)
            
            execution_time = time.time() - start_time
            
            return {
                "status": "completed",
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(f"Step {step.name} failed: {e}")
            
            return {
                "status": "failed",
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _perform_action(self, action: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Perform the actual action for a workflow step"""
        
        # Mock implementations for demonstration
        actions = {
            "fetch_gitlab_mr": self._mock_fetch_mr,
            "run_ai_analysis": self._mock_ai_analysis,
            "run_security_scan": self._mock_security_scan,
            "run_performance_analysis": self._mock_performance_analysis,
            "generate_mr_report": self._mock_generate_report,
            "auto_decision": self._mock_auto_decision,
            "analyze_code_changes": self._mock_analyze_changes,
            "select_relevant_tests": self._mock_select_tests,
            "run_test_suite": self._mock_run_tests,
            "analyze_test_results": self._mock_analyze_test_results,
            "generate_fix_suggestions": self._mock_generate_fixes,
            "assess_issue_severity": self._mock_assess_severity,
            "run_diagnostics": self._mock_run_diagnostics,
            "send_emergency_notifications": self._mock_send_notifications,
            "attempt_auto_fix": self._mock_auto_fix,
            "create_incident_record": self._mock_create_incident,
            "calculate_quality_metrics": self._mock_quality_metrics,
            "audit_dependencies": self._mock_audit_dependencies,
            "generate_quality_dashboard": self._mock_quality_dashboard
        }
        
        if action in actions:
            return await actions[action](parameters, context)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition string with context"""
        try:
            # Simple condition evaluation (in production, use a proper expression evaluator)
            # For demo, just return True
            return True
        except:
            return False
    
    def _calculate_execution_time(self, workflow: Workflow) -> float:
        """Calculate workflow execution time"""
        if workflow.started_at and workflow.completed_at:
            start = datetime.fromisoformat(workflow.started_at.replace('Z', '+00:00'))
            end = datetime.fromisoformat(workflow.completed_at.replace('Z', '+00:00'))
            return (end - start).total_seconds()
        return 0.0
    
    def _generate_result_summary(self, step_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of workflow results"""
        successful_steps = sum(1 for result in step_results.values() if result.get("status") == "completed")
        failed_steps = sum(1 for result in step_results.values() if result.get("status") == "failed")
        
        return {
            "total_steps": len(step_results),
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "success_rate": successful_steps / len(step_results) if step_results else 0
        }
    
    # Mock action implementations for demonstration
    async def _mock_fetch_mr(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(1)  # Simulate API call
        return {"mr_id": "123", "files_changed": 5, "lines_added": 150, "lines_removed": 30}
    
    async def _mock_ai_analysis(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(2)  # Simulate AI processing
        return {"risk_level": "medium", "confidence": 0.85, "issues_found": 2}
    
    async def _mock_security_scan(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(3)  # Simulate security scan
        return {"vulnerabilities": 1, "severity": "medium", "scan_duration": 3.2}
    
    async def _mock_performance_analysis(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(2)  # Simulate performance analysis
        return {"performance_score": 0.82, "bottlenecks": 2, "suggestions": 4}
    
    async def _mock_generate_report(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(1)  # Simulate report generation
        return {"report_id": f"report_{uuid.uuid4().hex[:8]}", "recommendations": 5}
    
    async def _mock_auto_decision(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.5)  # Simulate decision making
        return {"decision": "approve", "confidence": 0.9, "reason": "Low risk, high confidence"}
    
    async def _mock_analyze_changes(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(1)
        return {"files_analyzed": 8, "impact_score": 0.6, "test_suggestions": 12}
    
    async def _mock_select_tests(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(1)
        return {"tests_selected": 45, "estimated_time": 180, "coverage_impact": 0.95}
    
    async def _mock_run_tests(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(5)  # Simulate test execution
        return {"tests_run": 45, "passed": 42, "failed": 3, "execution_time": 175}
    
    async def _mock_analyze_test_results(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(1)
        return {"patterns_found": 2, "flaky_tests": 1, "suggestions": 3}
    
    async def _mock_generate_fixes(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(2)
        return {"fixes_generated": 3, "auto_applied": 1, "manual_review": 2}
    
    async def _mock_assess_severity(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        return {"severity": "high", "impact_score": 0.8, "urgency": "immediate"}
    
    async def _mock_run_diagnostics(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(3)
        return {"logs_collected": 1024, "anomalies_detected": 3, "root_cause": "identified"}
    
    async def _mock_send_notifications(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        return {"notifications_sent": 5, "escalated": True, "ack_received": 2}
    
    async def _mock_auto_fix(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(2)
        return {"fix_attempted": True, "success": True, "backup_created": True}
    
    async def _mock_create_incident(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(1)
        return {"incident_id": f"INC-{uuid.uuid4().hex[:8]}", "priority": "high", "assigned": True}
    
    async def _mock_quality_metrics(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(2)
        return {"code_quality": 0.85, "test_coverage": 0.78, "maintainability": 0.82}
    
    async def _mock_audit_dependencies(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(3)
        return {"dependencies_checked": 156, "vulnerabilities": 2, "license_issues": 0}
    
    async def _mock_quality_dashboard(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(1)
        return {"dashboard_updated": True, "notifications_sent": 3, "trend": "improving"}
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific workflow"""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            return {
                "id": workflow.id,
                "name": workflow.name,
                "status": workflow.status.value,
                "progress": self._calculate_progress(workflow),
                "started_at": workflow.started_at,
                "completed_at": workflow.completed_at,
                "result": workflow.result,
                "error": workflow.error
            }
        return None
    
    def _calculate_progress(self, workflow: Workflow) -> float:
        """Calculate workflow progress"""
        if workflow.status == WorkflowStatus.COMPLETED:
            return 1.0
        elif workflow.status == WorkflowStatus.FAILED:
            return 0.0
        elif workflow.status == WorkflowStatus.RUNNING and workflow.result:
            # Calculate based on completed steps
            completed = sum(1 for result in workflow.result.values() if result.get("status") == "completed")
            return completed / len(workflow.steps)
        else:
            return 0.0
    
    def list_workflows(self, status: Optional[WorkflowStatus] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List workflows, optionally filtered by status"""
        workflows = list(self.workflows.values())
        
        if status:
            workflows = [w for w in workflows if w.status == status]
        
        # Sort by creation time, most recent first
        workflows.sort(key=lambda w: w.created_at, reverse=True)
        
        return [asdict(w) for w in workflows[:limit]]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get automation engine metrics"""
        total_workflows = self.metrics["workflows_executed"]
        efficiency = (self.metrics["workflows_successful"] / total_workflows * 100) if total_workflows > 0 else 0
        
        return {
            **self.metrics,
            "automation_efficiency": efficiency,
            "active_workflows": len(self.running_workflows),
            "total_templates": len(self.workflow_templates),
            "scheduled_workflows": len(self.scheduled_workflows)
        }

# Global instance
automation_engine = AutomationEngine()

# Convenience functions
async def trigger_workflow(template_name: str, context: Dict[str, Any] = None) -> str:
    """Convenience function to trigger a workflow"""
    return await automation_engine.trigger_workflow(template_name, context)

def get_workflow_status(workflow_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get workflow status"""
    return automation_engine.get_workflow_status(workflow_id)