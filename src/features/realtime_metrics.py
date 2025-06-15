"""
Real-time Metrics and Anomaly Detection

Advanced monitoring system for pipeline performance, build trends,
and predictive analytics with anomaly detection.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import structlog
import statistics
from collections import defaultdict, deque
import json
from pathlib import Path

from src.integrations.gitlab_client import get_gitlab_client
from src.integrations.openrouter_client import get_openrouter_client

logger = structlog.get_logger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MetricType(Enum):
    """Types of metrics being tracked"""
    PIPELINE_DURATION = "pipeline_duration"
    PIPELINE_SUCCESS_RATE = "pipeline_success_rate"
    BUILD_FREQUENCY = "build_frequency"
    DEPLOYMENT_FREQUENCY = "deployment_frequency"
    MR_CYCLE_TIME = "mr_cycle_time"
    CODE_QUALITY_SCORE = "code_quality_score"
    VULNERABILITY_COUNT = "vulnerability_count"
    TEST_COVERAGE = "test_coverage"

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any]
    project_id: Optional[int] = None
    pipeline_id: Optional[int] = None
    mr_iid: Optional[int] = None

@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    metric_type: MetricType
    timestamp: datetime
    actual_value: float
    expected_value: float
    deviation_score: float  # How far from normal (0-1)
    severity: AlertSeverity
    description: str
    recommendations: List[str]

@dataclass
class TrendAnalysis:
    """Trend analysis for metrics"""
    metric_type: MetricType
    trend_direction: str  # "improving", "declining", "stable"
    change_rate: float  # % change over time period
    confidence: float
    time_period_days: int
    key_insights: List[str]

@dataclass
class PerformanceAlert:
    """Performance alert"""
    id: str
    severity: AlertSeverity
    title: str
    description: str
    metric_type: MetricType
    threshold_breached: float
    current_value: float
    project_id: Optional[int]
    timestamp: datetime
    suggested_actions: List[str]
    auto_resolved: bool = False

class RealTimeMetricsSystem:
    """Real-time metrics collection and anomaly detection system"""
    
    def __init__(self):
        self.gitlab_client = get_gitlab_client()
        self.openrouter_client = get_openrouter_client()
        
        # Metric storage (in production, would use time-series DB)
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.anomalies = deque(maxlen=500)
        self.alerts = deque(maxlen=200)
        self.trends = {}
        
        # Configuration
        self.collection_interval = 300  # 5 minutes
        self.anomaly_detection_window = 100  # Last 100 data points
        self.alert_cooldown = 3600  # 1 hour between similar alerts
        
        # Thresholds for anomaly detection
        self.anomaly_thresholds = {
            MetricType.PIPELINE_DURATION: {
                "z_score_threshold": 2.5,
                "min_data_points": 20,
                "expected_range": (1, 60)  # 1-60 minutes
            },
            MetricType.PIPELINE_SUCCESS_RATE: {
                "z_score_threshold": 2.0,
                "min_data_points": 10,
                "expected_range": (0.7, 1.0)  # 70-100%
            },
            MetricType.MR_CYCLE_TIME: {
                "z_score_threshold": 2.0,
                "min_data_points": 15,
                "expected_range": (0.5, 7)  # 0.5-7 days
            },
            MetricType.VULNERABILITY_COUNT: {
                "z_score_threshold": 1.5,
                "min_data_points": 5,
                "expected_range": (0, 10)  # 0-10 vulnerabilities
            }
        }
        
        # Alert suppression
        self.last_alerts = defaultdict(datetime)
        
        # Background tasks
        self._collection_task = None
        self._analysis_task = None
        self._running = False
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        if self._running:
            return
        
        self._running = True
        
        # Start background tasks
        self._collection_task = asyncio.create_task(self._metrics_collection_loop())
        self._analysis_task = asyncio.create_task(self._anomaly_detection_loop())
        
        logger.info("Real-time metrics monitoring started")
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        self._running = False
        
        if self._collection_task:
            self._collection_task.cancel()
        if self._analysis_task:
            self._analysis_task.cancel()
        
        logger.info("Real-time metrics monitoring stopped")
    
    async def _metrics_collection_loop(self):
        """Background task for metrics collection"""
        
        while self._running:
            try:
                await self._collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Metrics collection error", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _anomaly_detection_loop(self):
        """Background task for anomaly detection"""
        
        while self._running:
            try:
                await self._run_anomaly_detection()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Anomaly detection error", error=str(e))
                await asyncio.sleep(60)
    
    async def _collect_all_metrics(self):
        """Collect all configured metrics"""
        
        logger.debug("Starting metrics collection cycle")
        
        # Get active projects (for demo, use a hardcoded list)
        projects = await self._get_monitored_projects()
        
        for project_id in projects:
            try:
                await self._collect_project_metrics(project_id)
            except Exception as e:
                logger.warning(
                    "Failed to collect metrics for project",
                    project_id=project_id,
                    error=str(e)
                )
        
        logger.debug("Metrics collection cycle completed")
    
    async def _get_monitored_projects(self) -> List[int]:
        """Get list of projects to monitor"""
        # For demo purposes, return the GitLab CE project
        return [278964]
    
    async def _collect_project_metrics(self, project_id: int):
        """Collect metrics for a specific project"""
        
        # Collect pipeline metrics
        await self._collect_pipeline_metrics(project_id)
        
        # Collect MR metrics
        await self._collect_mr_metrics(project_id)
        
        # Collect quality metrics
        await self._collect_quality_metrics(project_id)
    
    async def _collect_pipeline_metrics(self, project_id: int):
        """Collect pipeline-related metrics"""
        
        try:
            # Get recent pipelines
            pipelines = await self.gitlab_client.list_project_pipelines(
                project_id=project_id,
                per_page=50
            )
            
            if not pipelines:
                return
            
            # Calculate pipeline duration
            durations = []
            success_count = 0
            total_count = len(pipelines)
            
            for pipeline in pipelines:
                if pipeline.get("duration"):
                    duration_minutes = pipeline["duration"] / 60.0
                    durations.append(duration_minutes)
                    
                    # Record individual pipeline duration
                    self._add_metric(
                        MetricType.PIPELINE_DURATION,
                        duration_minutes,
                        project_id=project_id,
                        pipeline_id=pipeline["id"],
                        metadata={
                            "status": pipeline.get("status"),
                            "ref": pipeline.get("ref"),
                            "created_at": pipeline.get("created_at")
                        }
                    )
                
                if pipeline.get("status") == "success":
                    success_count += 1
            
            # Calculate success rate
            if total_count > 0:
                success_rate = success_count / total_count
                self._add_metric(
                    MetricType.PIPELINE_SUCCESS_RATE,
                    success_rate,
                    project_id=project_id,
                    metadata={
                        "success_count": success_count,
                        "total_count": total_count,
                        "time_window": "last_50_pipelines"
                    }
                )
            
            # Calculate build frequency (pipelines per day)
            if pipelines:
                # Get time range of pipelines
                oldest = min(
                    datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")) 
                    for p in pipelines if p.get("created_at")
                )
                newest = max(
                    datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")) 
                    for p in pipelines if p.get("created_at")
                )
                
                time_span_days = (newest - oldest).total_seconds() / 86400
                if time_span_days > 0:
                    build_frequency = total_count / time_span_days
                    self._add_metric(
                        MetricType.BUILD_FREQUENCY,
                        build_frequency,
                        project_id=project_id,
                        metadata={
                            "time_span_days": time_span_days,
                            "total_pipelines": total_count
                        }
                    )
        
        except Exception as e:
            logger.error(
                "Pipeline metrics collection failed",
                project_id=project_id,
                error=str(e)
            )
    
    async def _collect_mr_metrics(self, project_id: int):
        """Collect merge request metrics"""
        
        try:
            # Get recent MRs
            mrs = await self.gitlab_client.list_project_merge_requests(
                project_id=project_id,
                state="merged",
                per_page=50
            )
            
            if not mrs:
                return
            
            cycle_times = []
            
            for mr in mrs:
                created_at = mr.get("created_at")
                merged_at = mr.get("merged_at")
                
                if created_at and merged_at:
                    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    merged = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
                    
                    cycle_time_days = (merged - created).total_seconds() / 86400
                    cycle_times.append(cycle_time_days)
                    
                    # Record individual MR cycle time
                    self._add_metric(
                        MetricType.MR_CYCLE_TIME,
                        cycle_time_days,
                        project_id=project_id,
                        mr_iid=mr["iid"],
                        metadata={
                            "title": mr.get("title", ""),
                            "author": mr.get("author", {}).get("username", ""),
                            "created_at": created_at,
                            "merged_at": merged_at
                        }
                    )
            
        except Exception as e:
            logger.error(
                "MR metrics collection failed",
                project_id=project_id,
                error=str(e)
            )
    
    async def _collect_quality_metrics(self, project_id: int):
        """Collect code quality metrics"""
        
        try:
            # This would integrate with actual quality tools
            # For demo, generate some sample metrics
            
            # Simulate vulnerability count
            vulnerability_count = len(await self._simulate_vulnerability_scan(project_id))
            self._add_metric(
                MetricType.VULNERABILITY_COUNT,
                vulnerability_count,
                project_id=project_id,
                metadata={
                    "scan_type": "simulated",
                    "tools": ["safety", "bandit", "npm audit"]
                }
            )
            
            # Simulate test coverage
            test_coverage = 0.85 + (hash(str(datetime.now().hour)) % 20) / 100.0
            self._add_metric(
                MetricType.TEST_COVERAGE,
                test_coverage,
                project_id=project_id,
                metadata={
                    "test_framework": "pytest",
                    "coverage_tool": "coverage.py"
                }
            )
            
        except Exception as e:
            logger.error(
                "Quality metrics collection failed",
                project_id=project_id,
                error=str(e)
            )
    
    async def _simulate_vulnerability_scan(self, project_id: int) -> List[Dict]:
        """Simulate vulnerability scan (placeholder)"""
        
        # Return some sample vulnerabilities
        return [
            {"severity": "medium", "package": "requests", "cve": "CVE-2023-32681"},
            {"severity": "low", "package": "urllib3", "cve": "CVE-2023-45803"}
        ]
    
    def _add_metric(
        self,
        metric_type: MetricType,
        value: float,
        project_id: Optional[int] = None,
        pipeline_id: Optional[int] = None,
        mr_iid: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a metric data point"""
        
        metric_point = MetricPoint(
            timestamp=datetime.utcnow(),
            value=value,
            metadata=metadata or {},
            project_id=project_id,
            pipeline_id=pipeline_id,
            mr_iid=mr_iid
        )
        
        # Store in buffer
        self.metrics_buffer[metric_type].append(metric_point)
        
        logger.debug(
            "Metric recorded",
            metric_type=metric_type.value,
            value=value,
            project_id=project_id
        )
    
    async def _run_anomaly_detection(self):
        """Run anomaly detection on collected metrics"""
        
        for metric_type in MetricType:
            if metric_type in self.metrics_buffer:
                await self._detect_anomalies_for_metric(metric_type)
    
    async def _detect_anomalies_for_metric(self, metric_type: MetricType):
        """Detect anomalies for a specific metric type"""
        
        try:
            metric_data = list(self.metrics_buffer[metric_type])
            
            if len(metric_data) < self.anomaly_thresholds[metric_type]["min_data_points"]:
                return
            
            # Get recent data points
            recent_data = metric_data[-self.anomaly_detection_window:]
            values = [point.value for point in recent_data]
            
            if len(values) < 10:  # Need minimum data for statistical analysis
                return
            
            # Calculate statistical measures
            mean_value = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            
            if std_dev == 0:  # No variation, no anomalies
                return
            
            # Check latest value for anomaly
            latest_point = recent_data[-1]
            latest_value = latest_point.value
            
            # Calculate z-score
            z_score = abs(latest_value - mean_value) / std_dev
            z_threshold = self.anomaly_thresholds[metric_type]["z_score_threshold"]
            
            if z_score > z_threshold:
                # Anomaly detected
                deviation_score = min(z_score / (z_threshold * 2), 1.0)
                
                severity = self._calculate_anomaly_severity(
                    metric_type, 
                    deviation_score, 
                    latest_value
                )
                
                anomaly = await self._create_anomaly(
                    metric_type=metric_type,
                    timestamp=latest_point.timestamp,
                    actual_value=latest_value,
                    expected_value=mean_value,
                    deviation_score=deviation_score,
                    severity=severity
                )
                
                self.anomalies.append(anomaly)
                
                # Generate alert if severe enough
                if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                    await self._generate_alert(anomaly, latest_point)
                
                logger.warning(
                    "Anomaly detected",
                    metric_type=metric_type.value,
                    actual_value=latest_value,
                    expected_value=mean_value,
                    deviation_score=deviation_score,
                    severity=severity.value
                )
        
        except Exception as e:
            logger.error(
                "Anomaly detection failed",
                metric_type=metric_type.value,
                error=str(e)
            )
    
    def _calculate_anomaly_severity(
        self,
        metric_type: MetricType,
        deviation_score: float,
        actual_value: float
    ) -> AlertSeverity:
        """Calculate severity of anomaly"""
        
        # Check if value is completely out of expected range
        expected_range = self.anomaly_thresholds[metric_type]["expected_range"]
        min_val, max_val = expected_range
        
        if actual_value < min_val * 0.5 or actual_value > max_val * 2:
            return AlertSeverity.CRITICAL
        
        # Base severity on deviation score
        if deviation_score > 0.8:
            return AlertSeverity.HIGH
        elif deviation_score > 0.6:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    async def _create_anomaly(
        self,
        metric_type: MetricType,
        timestamp: datetime,
        actual_value: float,
        expected_value: float,
        deviation_score: float,
        severity: AlertSeverity
    ) -> AnomalyDetection:
        """Create anomaly detection object"""
        
        # Generate description and recommendations using AI if available
        description, recommendations = await self._generate_anomaly_analysis(
            metric_type, actual_value, expected_value, deviation_score
        )
        
        return AnomalyDetection(
            metric_type=metric_type,
            timestamp=timestamp,
            actual_value=actual_value,
            expected_value=expected_value,
            deviation_score=deviation_score,
            severity=severity,
            description=description,
            recommendations=recommendations
        )
    
    async def _generate_anomaly_analysis(
        self,
        metric_type: MetricType,
        actual_value: float,
        expected_value: float,
        deviation_score: float
    ) -> Tuple[str, List[str]]:
        """Generate anomaly description and recommendations"""
        
        # Try AI analysis first
        if await self.openrouter_client.is_available():
            try:
                ai_result = await self.openrouter_client.analyze_metric_anomaly(
                    metric_type.value,
                    actual_value,
                    expected_value,
                    deviation_score
                )
                
                if ai_result:
                    return (
                        ai_result.get("description", ""),
                        ai_result.get("recommendations", [])
                    )
            except Exception as e:
                logger.warning("AI anomaly analysis failed", error=str(e))
        
        # Fallback to rule-based analysis
        return self._fallback_anomaly_analysis(metric_type, actual_value, expected_value)
    
    def _fallback_anomaly_analysis(
        self,
        metric_type: MetricType,
        actual_value: float,
        expected_value: float
    ) -> Tuple[str, List[str]]:
        """Fallback anomaly analysis"""
        
        change_pct = ((actual_value - expected_value) / expected_value) * 100
        direction = "increased" if actual_value > expected_value else "decreased"
        
        descriptions = {
            MetricType.PIPELINE_DURATION: f"Pipeline duration {direction} by {abs(change_pct):.1f}%",
            MetricType.PIPELINE_SUCCESS_RATE: f"Pipeline success rate {direction} by {abs(change_pct):.1f}%",
            MetricType.MR_CYCLE_TIME: f"MR cycle time {direction} by {abs(change_pct):.1f}%",
            MetricType.VULNERABILITY_COUNT: f"Vulnerability count {direction} by {abs(change_pct):.1f}%"
        }
        
        recommendations_map = {
            MetricType.PIPELINE_DURATION: [
                "Review recent pipeline changes",
                "Check for resource contention",
                "Optimize slow pipeline stages"
            ],
            MetricType.PIPELINE_SUCCESS_RATE: [
                "Investigate recent failures", 
                "Review test stability",
                "Check dependency issues"
            ],
            MetricType.MR_CYCLE_TIME: [
                "Review code review process",
                "Check for bottlenecks in approval workflow",
                "Consider automating more checks"
            ],
            MetricType.VULNERABILITY_COUNT: [
                "Update dependencies",
                "Run security scan",
                "Review recent code changes"
            ]
        }
        
        description = descriptions.get(
            metric_type, 
            f"{metric_type.value} anomaly detected"
        )
        
        recommendations = recommendations_map.get(metric_type, [
            "Investigate the anomaly",
            "Check recent changes",
            "Monitor the trend"
        ])
        
        return description, recommendations
    
    async def _generate_alert(self, anomaly: AnomalyDetection, metric_point: MetricPoint):
        """Generate performance alert from anomaly"""
        
        # Check alert cooldown
        alert_key = f"{anomaly.metric_type.value}:{metric_point.project_id}"
        last_alert_time = self.last_alerts.get(alert_key)
        
        if (last_alert_time and 
            (datetime.utcnow() - last_alert_time).total_seconds() < self.alert_cooldown):
            return  # Skip due to cooldown
        
        # Create alert
        alert = PerformanceAlert(
            id=f"{anomaly.metric_type.value}_{int(anomaly.timestamp.timestamp())}",
            severity=anomaly.severity,
            title=f"{anomaly.metric_type.value.replace('_', ' ').title()} Anomaly",
            description=anomaly.description,
            metric_type=anomaly.metric_type,
            threshold_breached=anomaly.expected_value,
            current_value=anomaly.actual_value,
            project_id=metric_point.project_id,
            timestamp=anomaly.timestamp,
            suggested_actions=anomaly.recommendations
        )
        
        self.alerts.append(alert)
        self.last_alerts[alert_key] = datetime.utcnow()
        
        logger.warning(
            "Performance alert generated",
            alert_id=alert.id,
            severity=alert.severity.value,
            metric_type=alert.metric_type.value,
            project_id=alert.project_id
        )
    
    # Public API methods
    async def get_metrics_summary(
        self, 
        project_id: Optional[int] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get metrics summary for dashboard"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        summary = {
            "timeframe_hours": hours,
            "metrics": {},
            "alerts_count": 0,
            "anomalies_count": 0
        }
        
        for metric_type in MetricType:
            if metric_type in self.metrics_buffer:
                # Filter metrics by time and project
                metrics = [
                    point for point in self.metrics_buffer[metric_type]
                    if (point.timestamp >= cutoff_time and 
                        (project_id is None or point.project_id == project_id))
                ]
                
                if metrics:
                    values = [point.value for point in metrics]
                    summary["metrics"][metric_type.value] = {
                        "count": len(metrics),
                        "latest_value": values[-1],
                        "avg_value": statistics.mean(values),
                        "min_value": min(values),
                        "max_value": max(values),
                        "trend": self._calculate_simple_trend(values)
                    }
        
        # Count recent alerts and anomalies
        recent_alerts = [
            alert for alert in self.alerts
            if (alert.timestamp >= cutoff_time and
                (project_id is None or alert.project_id == project_id))
        ]
        
        recent_anomalies = [
            anomaly for anomaly in self.anomalies
            if anomaly.timestamp >= cutoff_time
        ]
        
        summary["alerts_count"] = len(recent_alerts)
        summary["anomalies_count"] = len(recent_anomalies)
        
        return summary
    
    def _calculate_simple_trend(self, values: List[float]) -> str:
        """Calculate simple trend direction"""
        
        if len(values) < 2:
            return "stable"
        
        # Compare first half vs second half
        mid = len(values) // 2
        first_half_avg = statistics.mean(values[:mid])
        second_half_avg = statistics.mean(values[mid:])
        
        change_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        
        if change_pct > 5:
            return "increasing"
        elif change_pct < -5:
            return "decreasing"
        else:
            return "stable"
    
    async def get_recent_alerts(
        self, 
        limit: int = 20,
        severity: Optional[AlertSeverity] = None
    ) -> List[Dict[str, Any]]:
        """Get recent performance alerts"""
        
        alerts = list(self.alerts)
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        # Sort by timestamp (newest first) and limit
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        alerts = alerts[:limit]
        
        # Convert to dict format
        return [
            {
                "id": alert.id,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "metric_type": alert.metric_type.value,
                "threshold_breached": alert.threshold_breached,
                "current_value": alert.current_value,
                "project_id": alert.project_id,
                "timestamp": alert.timestamp.isoformat(),
                "suggested_actions": alert.suggested_actions,
                "auto_resolved": alert.auto_resolved
            }
            for alert in alerts
        ]
    
    async def get_trend_analysis(
        self,
        metric_type: MetricType,
        days: int = 7,
        project_id: Optional[int] = None
    ) -> TrendAnalysis:
        """Get trend analysis for a metric"""
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Get metrics for the time period
        metrics = [
            point for point in self.metrics_buffer[metric_type]
            if (point.timestamp >= cutoff_time and
                (project_id is None or point.project_id == project_id))
        ]
        
        if len(metrics) < 5:
            return TrendAnalysis(
                metric_type=metric_type,
                trend_direction="insufficient_data",
                change_rate=0.0,
                confidence=0.0,
                time_period_days=days,
                key_insights=["Not enough data for trend analysis"]
            )
        
        # Calculate trend
        values = [point.value for point in metrics]
        timestamps = [point.timestamp for point in metrics]
        
        # Simple linear regression for trend
        x_values = [(ts - timestamps[0]).total_seconds() for ts in timestamps]
        n = len(values)
        
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        # Calculate slope (trend direction)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
        
        # Convert slope to percentage change per day
        seconds_per_day = 86400
        change_rate = slope * seconds_per_day * 100 / statistics.mean(values) if statistics.mean(values) != 0 else 0
        
        # Determine trend direction
        if abs(change_rate) < 1:
            trend_direction = "stable"
        elif change_rate > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"
        
        # Calculate confidence based on data consistency
        confidence = min(len(metrics) / 50, 1.0)  # Higher confidence with more data
        
        # Generate insights
        insights = []
        if abs(change_rate) > 10:
            insights.append(f"Significant {trend_direction} trend detected")
        
        if trend_direction == "increasing" and metric_type in [MetricType.PIPELINE_DURATION, MetricType.VULNERABILITY_COUNT]:
            insights.append("Concerning upward trend - investigation recommended")
        elif trend_direction == "decreasing" and metric_type in [MetricType.PIPELINE_SUCCESS_RATE, MetricType.TEST_COVERAGE]:
            insights.append("Declining performance trend detected")
        
        return TrendAnalysis(
            metric_type=metric_type,
            trend_direction=trend_direction,
            change_rate=change_rate,
            confidence=confidence,
            time_period_days=days,
            key_insights=insights or ["Trend within normal range"]
        )
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get real-time metrics system statistics"""
        
        total_metrics = sum(len(buffer) for buffer in self.metrics_buffer.values())
        
        return {
            "monitoring_active": self._running,
            "total_metrics_collected": total_metrics,
            "metric_types_count": len(self.metrics_buffer),
            "total_anomalies": len(self.anomalies),
            "total_alerts": len(self.alerts),
            "collection_interval_seconds": self.collection_interval,
            "latest_collection": max(
                (max(point.timestamp for point in buffer) for buffer in self.metrics_buffer.values() if buffer),
                default=None
            ),
            "buffer_sizes": {
                metric_type.value: len(buffer) 
                for metric_type, buffer in self.metrics_buffer.items()
            }
        }

# Global instance
_metrics_system: Optional[RealTimeMetricsSystem] = None

async def get_metrics_system() -> RealTimeMetricsSystem:
    """Get or create metrics system instance"""
    global _metrics_system
    if _metrics_system is None:
        _metrics_system = RealTimeMetricsSystem()
        await _metrics_system.start_monitoring()
    return _metrics_system