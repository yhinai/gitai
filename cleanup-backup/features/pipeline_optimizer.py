"""
AI-powered CI/CD pipeline optimizer
"""
import asyncio
import json
import re
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import structlog
from cachetools import TTLCache

from src.integrations.gitlab_client import get_gitlab_client

logger = structlog.get_logger(__name__)

class OptimizationLevel(Enum):
    """Optimization aggressiveness levels"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"

class JobOptimization(Enum):
    """Types of job optimizations"""
    PARALLELIZATION = "parallelization"
    CACHING = "caching"
    RESOURCE_REDUCTION = "resource_reduction"
    STAGE_REORDERING = "stage_reordering"
    CONDITIONAL_EXECUTION = "conditional_execution"
    IMAGE_OPTIMIZATION = "image_optimization"

@dataclass
class PipelineMetrics:
    """Pipeline performance metrics"""
    avg_duration: float
    p95_duration: float
    success_rate: float
    failure_rate: float
    avg_queue_time: float
    resource_efficiency: float
    bottleneck_stages: List[str]
    cost_per_run: float

@dataclass
class OptimizationRecommendation:
    """Single optimization recommendation"""
    type: JobOptimization
    description: str
    estimated_impact: Dict[str, float]  # duration_reduction, cost_savings, etc.
    implementation_difficulty: str  # easy, medium, hard
    risk_level: str  # low, medium, high
    code_changes: Optional[Dict[str, str]]  # file -> content changes
    confidence: float

@dataclass
class PipelineAnalysis:
    """Complete pipeline optimization analysis"""
    pipeline_id: Optional[int]
    project_id: int
    current_metrics: PipelineMetrics
    recommendations: List[OptimizationRecommendation]
    predicted_metrics: PipelineMetrics
    overall_score: float  # 0-100 optimization score
    analysis_timestamp: datetime

class PipelineOptimizer:
    """AI-powered pipeline optimization system"""
    
    def __init__(self):
        self.gitlab_client = get_gitlab_client()
        self.analysis_cache = TTLCache(maxsize=500, ttl=7200)  # 2 hour cache
        
        # Optimization patterns
        self.parallelization_patterns = [
            (r'yarn test', r'yarn test --parallel'),
            (r'npm test', r'npm run test:parallel'),
            (r'pytest', r'pytest -n auto'),
            (r'mvn test', r'mvn test -T 1C'),
            (r'go test', r'go test -parallel 8')
        ]
        
        self.caching_opportunities = [
            'node_modules', 'vendor', '.gradle', '.m2', 'target',
            '__pycache__', '.pip', 'node_cache', 'gems'
        ]
        
        # Docker image optimizations
        self.optimized_images = {
            'node:latest': 'node:18-alpine',
            'python:latest': 'python:3.11-slim',
            'ubuntu:latest': 'ubuntu:22.04',
            'postgres:latest': 'postgres:15-alpine',
            'redis:latest': 'redis:7-alpine'
        }
    
    async def analyze_pipeline_performance(
        self, 
        project_id: int, 
        pipeline_id: Optional[int] = None,
        optimization_level: OptimizationLevel = OptimizationLevel.BALANCED
    ) -> PipelineAnalysis:
        """Analyze pipeline performance and generate optimization recommendations"""
        
        cache_key = f"pipeline_analysis_{project_id}_{pipeline_id}_{optimization_level.value}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        logger.info(
            "Starting pipeline analysis",
            project_id=project_id,
            pipeline_id=pipeline_id,
            optimization_level=optimization_level.value
        )
        
        try:
            # Gather pipeline data
            if pipeline_id:
                pipeline_data = await self._analyze_single_pipeline(project_id, pipeline_id)
            else:
                pipeline_data = await self._analyze_project_pipelines(project_id)
            
            # Calculate current metrics
            current_metrics = await self._calculate_pipeline_metrics(pipeline_data)
            
            # Generate optimizations
            recommendations = await self._generate_optimizations(
                pipeline_data, 
                current_metrics,
                optimization_level
            )
            
            # Predict improved metrics
            predicted_metrics = self._predict_optimized_metrics(
                current_metrics, 
                recommendations
            )
            
            # Calculate overall optimization score
            score = self._calculate_optimization_score(current_metrics, predicted_metrics)
            
            analysis = PipelineAnalysis(
                pipeline_id=pipeline_id,
                project_id=project_id,
                current_metrics=current_metrics,
                recommendations=recommendations,
                predicted_metrics=predicted_metrics,
                overall_score=score,
                analysis_timestamp=datetime.utcnow()
            )
            
            # Cache the result
            self.analysis_cache[cache_key] = analysis
            
            logger.info(
                "Pipeline analysis completed",
                project_id=project_id,
                pipeline_id=pipeline_id,
                score=score,
                recommendations_count=len(recommendations)
            )
            
            return analysis
            
        except Exception as e:
            logger.error(
                "Pipeline analysis failed",
                project_id=project_id,
                pipeline_id=pipeline_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _analyze_single_pipeline(self, project_id: int, pipeline_id: int) -> Dict:
        """Analyze a single pipeline"""
        pipeline = await self.gitlab_client.get_pipeline(project_id, pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        jobs = await self.gitlab_client.get_pipeline_jobs(project_id, pipeline_id)
        
        return {
            'pipeline': pipeline,
            'jobs': jobs,
            'is_single': True
        }
    
    async def _analyze_project_pipelines(self, project_id: int) -> Dict:
        """Analyze recent pipelines for a project"""
        pipelines = await self.gitlab_client.list_project_pipelines(
            project_id=project_id,
            per_page=50
        )
        
        # Get detailed data for recent pipelines
        detailed_pipelines = []
        jobs_data = []
        
        for pipeline in pipelines[:10]:  # Analyze last 10 pipelines
            try:
                jobs = await self.gitlab_client.get_pipeline_jobs(
                    project_id, pipeline['id']
                )
                detailed_pipelines.append(pipeline)
                jobs_data.extend(jobs)
            except Exception as e:
                logger.warning(
                    "Failed to fetch pipeline jobs",
                    pipeline_id=pipeline['id'],
                    error=str(e)
                )
        
        return {
            'pipelines': detailed_pipelines,
            'jobs': jobs_data,
            'is_single': False
        }
    
    async def _calculate_pipeline_metrics(self, pipeline_data: Dict) -> PipelineMetrics:
        """Calculate pipeline performance metrics"""
        
        if pipeline_data['is_single']:
            # Single pipeline metrics
            pipeline = pipeline_data['pipeline']
            jobs = pipeline_data['jobs']
            
            duration = pipeline.get('duration', 0) or 0
            queue_time = 0  # Would need to calculate from job start times
            
            # Calculate job-level metrics
            job_durations = [job.get('duration', 0) or 0 for job in jobs if job.get('duration')]
            failed_jobs = [job for job in jobs if job.get('status') == 'failed']
            
            return PipelineMetrics(
                avg_duration=duration,
                p95_duration=duration,
                success_rate=1.0 if pipeline.get('status') == 'success' else 0.0,
                failure_rate=len(failed_jobs) / len(jobs) if jobs else 0.0,
                avg_queue_time=queue_time,
                resource_efficiency=self._calculate_resource_efficiency(jobs),
                bottleneck_stages=self._identify_bottleneck_stages(jobs),
                cost_per_run=self._estimate_cost(duration, jobs)
            )
        
        else:
            # Multi-pipeline metrics
            pipelines = pipeline_data['pipelines']
            all_jobs = pipeline_data['jobs']
            
            # Calculate aggregate metrics
            durations = [p.get('duration', 0) or 0 for p in pipelines if p.get('duration')]
            statuses = [p.get('status') for p in pipelines]
            
            success_count = sum(1 for s in statuses if s == 'success')
            total_pipelines = len(pipelines)
            
            return PipelineMetrics(
                avg_duration=statistics.mean(durations) if durations else 0,
                p95_duration=statistics.quantiles(durations, n=20)[18] if len(durations) > 5 else max(durations, default=0),
                success_rate=success_count / total_pipelines if total_pipelines else 0,
                failure_rate=(total_pipelines - success_count) / total_pipelines if total_pipelines else 0,
                avg_queue_time=0,  # Would need detailed timing data
                resource_efficiency=self._calculate_resource_efficiency(all_jobs),
                bottleneck_stages=self._identify_bottleneck_stages(all_jobs),
                cost_per_run=self._estimate_cost(
                    statistics.mean(durations) if durations else 0, 
                    all_jobs
                )
            )
    
    def _calculate_resource_efficiency(self, jobs: List[Dict]) -> float:
        """Calculate resource utilization efficiency"""
        if not jobs:
            return 0.5
        
        # Simplified efficiency calculation
        # In reality, would analyze CPU/memory usage from monitoring data
        total_duration = sum(job.get('duration', 0) or 0 for job in jobs)
        parallel_duration = max(job.get('duration', 0) or 0 for job in jobs)
        
        if parallel_duration == 0:
            return 0.5
        
        # Efficiency = actual parallelism / theoretical maximum
        theoretical_parallel = total_duration / len(jobs) if jobs else 0
        efficiency = min(theoretical_parallel / parallel_duration, 1.0) if parallel_duration > 0 else 0.5
        
        return efficiency
    
    def _identify_bottleneck_stages(self, jobs: List[Dict]) -> List[str]:
        """Identify slowest pipeline stages"""
        stage_durations = {}
        
        for job in jobs:
            stage = job.get('stage', 'unknown')
            duration = job.get('duration', 0) or 0
            
            if stage not in stage_durations:
                stage_durations[stage] = []
            stage_durations[stage].append(duration)
        
        # Calculate average duration per stage
        avg_durations = {
            stage: statistics.mean(durations) 
            for stage, durations in stage_durations.items()
        }
        
        # Return stages above 75th percentile
        if not avg_durations:
            return []
        
        sorted_stages = sorted(avg_durations.items(), key=lambda x: x[1], reverse=True)
        bottleneck_count = max(1, len(sorted_stages) // 4)
        
        return [stage for stage, _ in sorted_stages[:bottleneck_count]]
    
    def _estimate_cost(self, duration_minutes: float, jobs: List[Dict]) -> float:
        """Estimate pipeline cost based on duration and resource usage"""
        # Simplified cost calculation (would integrate with actual cloud billing)
        base_cost_per_minute = 0.02  # $0.02 per minute per job
        
        job_count = len(jobs) if jobs else 1
        estimated_cost = duration_minutes * job_count * base_cost_per_minute
        
        return estimated_cost
    
    async def _generate_optimizations(
        self, 
        pipeline_data: Dict, 
        metrics: PipelineMetrics,
        level: OptimizationLevel
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations"""
        
        recommendations = []
        
        # Get CI config for analysis
        ci_config = await self._get_ci_config(pipeline_data)
        
        # Generate different types of optimizations
        recommendations.extend(await self._suggest_parallelization(ci_config, metrics))
        recommendations.extend(await self._suggest_caching(ci_config, metrics))
        recommendations.extend(await self._suggest_image_optimization(ci_config, metrics))
        recommendations.extend(await self._suggest_conditional_execution(ci_config, metrics))
        recommendations.extend(await self._suggest_resource_optimization(ci_config, metrics))
        
        # Filter based on optimization level
        filtered_recommendations = self._filter_by_optimization_level(
            recommendations, level
        )
        
        # Sort by impact
        filtered_recommendations.sort(
            key=lambda r: r.estimated_impact.get('duration_reduction', 0), 
            reverse=True
        )
        
        return filtered_recommendations[:10]  # Return top 10
    
    async def _get_ci_config(self, pipeline_data: Dict) -> str:
        """Get CI configuration for analysis"""
        # This would fetch the actual .gitlab-ci.yml file
        # For now, return a placeholder
        return """
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - npm install
    - npm run build

test:
  stage: test
  script:
    - npm test

deploy:
  stage: deploy
  script:
    - echo "Deploying..."
"""
    
    async def _suggest_parallelization(self, ci_config: str, metrics: PipelineMetrics) -> List[OptimizationRecommendation]:
        """Suggest parallelization optimizations"""
        recommendations = []
        
        # Look for sequential test execution
        if 'npm test' in ci_config and 'parallel' not in ci_config:
            recommendations.append(OptimizationRecommendation(
                type=JobOptimization.PARALLELIZATION,
                description="Enable parallel test execution with Jest or similar",
                estimated_impact={
                    'duration_reduction': 0.4,  # 40% faster
                    'cost_savings': 0.3
                },
                implementation_difficulty="easy",
                risk_level="low",
                code_changes={
                    '.gitlab-ci.yml': """
test:
  stage: test
  script:
    - npm run test:parallel
  parallel: 4
"""
                },
                confidence=0.8
            ))
        
        # Suggest stage parallelization
        if 'stages:' in ci_config and len(metrics.bottleneck_stages) > 1:
            recommendations.append(OptimizationRecommendation(
                type=JobOptimization.PARALLELIZATION,
                description="Parallelize independent build stages",
                estimated_impact={
                    'duration_reduction': 0.25,
                    'cost_savings': 0.15
                },
                implementation_difficulty="medium",
                risk_level="low",
                code_changes={
                    '.gitlab-ci.yml': "# Split independent stages into parallel jobs"
                },
                confidence=0.7
            ))
        
        return recommendations
    
    async def _suggest_caching(self, ci_config: str, metrics: PipelineMetrics) -> List[OptimizationRecommendation]:
        """Suggest caching optimizations"""
        recommendations = []
        
        # Look for missing cache configurations
        missing_caches = []
        for cache_dir in self.caching_opportunities:
            if cache_dir in ci_config and 'cache:' not in ci_config:
                missing_caches.append(cache_dir)
        
        if missing_caches:
            recommendations.append(OptimizationRecommendation(
                type=JobOptimization.CACHING,
                description=f"Add caching for {', '.join(missing_caches[:3])}",
                estimated_impact={
                    'duration_reduction': 0.6,  # 60% faster for cache hits
                    'cost_savings': 0.4
                },
                implementation_difficulty="easy",
                risk_level="low",
                code_changes={
                    '.gitlab-ci.yml': f"""
cache:
  paths:
{chr(10).join(f'    - {cache}' for cache in missing_caches[:3])}
  key: ${{CI_COMMIT_REF_SLUG}}
"""
                },
                confidence=0.9
            ))
        
        return recommendations
    
    async def _suggest_image_optimization(self, ci_config: str, metrics: PipelineMetrics) -> List[OptimizationRecommendation]:
        """Suggest Docker image optimizations"""
        recommendations = []
        
        for original, optimized in self.optimized_images.items():
            if original in ci_config:
                recommendations.append(OptimizationRecommendation(
                    type=JobOptimization.IMAGE_OPTIMIZATION,
                    description=f"Replace {original} with {optimized} for faster startup",
                    estimated_impact={
                        'duration_reduction': 0.15,
                        'cost_savings': 0.1,
                        'startup_improvement': 0.5
                    },
                    implementation_difficulty="easy",
                    risk_level="low",
                    code_changes={
                        '.gitlab-ci.yml': ci_config.replace(original, optimized)
                    },
                    confidence=0.85
                ))
        
        return recommendations
    
    async def _suggest_conditional_execution(self, ci_config: str, metrics: PipelineMetrics) -> List[OptimizationRecommendation]:
        """Suggest conditional job execution"""
        recommendations = []
        
        if 'rules:' not in ci_config and 'only:' not in ci_config:
            recommendations.append(OptimizationRecommendation(
                type=JobOptimization.CONDITIONAL_EXECUTION,
                description="Add conditional execution rules to skip unnecessary jobs",
                estimated_impact={
                    'duration_reduction': 0.3,
                    'cost_savings': 0.4,
                    'efficiency_gain': 0.5
                },
                implementation_difficulty="medium",
                risk_level="medium",
                code_changes={
                    '.gitlab-ci.yml': """
# Add rules to jobs
test:
  stage: test
  script: [...]
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
"""
                },
                confidence=0.7
            ))
        
        return recommendations
    
    async def _suggest_resource_optimization(self, ci_config: str, metrics: PipelineMetrics) -> List[OptimizationRecommendation]:
        """Suggest resource optimization"""
        recommendations = []
        
        if metrics.resource_efficiency < 0.7:
            recommendations.append(OptimizationRecommendation(
                type=JobOptimization.RESOURCE_REDUCTION,
                description="Optimize resource allocation based on actual usage",
                estimated_impact={
                    'cost_savings': 0.2,
                    'efficiency_gain': 0.3
                },
                implementation_difficulty="medium",
                risk_level="low",
                code_changes={
                    '.gitlab-ci.yml': """
# Add resource limits
variables:
  KUBERNETES_CPU_REQUEST: "100m"
  KUBERNETES_MEMORY_REQUEST: "128Mi"
  KUBERNETES_CPU_LIMIT: "500m"
  KUBERNETES_MEMORY_LIMIT: "512Mi"
"""
                },
                confidence=0.6
            ))
        
        return recommendations
    
    def _filter_by_optimization_level(
        self, 
        recommendations: List[OptimizationRecommendation],
        level: OptimizationLevel
    ) -> List[OptimizationRecommendation]:
        """Filter recommendations based on optimization level"""
        
        if level == OptimizationLevel.CONSERVATIVE:
            return [r for r in recommendations if r.risk_level == "low"]
        elif level == OptimizationLevel.BALANCED:
            return [r for r in recommendations if r.risk_level in ["low", "medium"]]
        else:  # AGGRESSIVE
            return recommendations
    
    def _predict_optimized_metrics(
        self, 
        current: PipelineMetrics,
        recommendations: List[OptimizationRecommendation]
    ) -> PipelineMetrics:
        """Predict metrics after applying optimizations"""
        
        total_duration_reduction = 0
        total_cost_savings = 0
        
        for rec in recommendations:
            # Apply compound improvements
            total_duration_reduction = 1 - (1 - total_duration_reduction) * (1 - rec.estimated_impact.get('duration_reduction', 0))
            total_cost_savings = 1 - (1 - total_cost_savings) * (1 - rec.estimated_impact.get('cost_savings', 0))
        
        return PipelineMetrics(
            avg_duration=current.avg_duration * (1 - total_duration_reduction),
            p95_duration=current.p95_duration * (1 - total_duration_reduction),
            success_rate=min(current.success_rate + 0.05, 1.0),  # Slight improvement
            failure_rate=max(current.failure_rate - 0.05, 0.0),
            avg_queue_time=current.avg_queue_time * 0.9,  # Assume some improvement
            resource_efficiency=min(current.resource_efficiency + 0.1, 1.0),
            bottleneck_stages=current.bottleneck_stages[1:],  # Assume one bottleneck resolved
            cost_per_run=current.cost_per_run * (1 - total_cost_savings)
        )
    
    def _calculate_optimization_score(
        self, 
        current: PipelineMetrics, 
        predicted: PipelineMetrics
    ) -> float:
        """Calculate overall optimization score (0-100)"""
        
        duration_improvement = (current.avg_duration - predicted.avg_duration) / current.avg_duration if current.avg_duration > 0 else 0
        cost_improvement = (current.cost_per_run - predicted.cost_per_run) / current.cost_per_run if current.cost_per_run > 0 else 0
        efficiency_improvement = predicted.resource_efficiency - current.resource_efficiency
        
        # Weighted score
        score = (
            duration_improvement * 40 +  # 40% weight on duration
            cost_improvement * 30 +      # 30% weight on cost
            efficiency_improvement * 20 + # 20% weight on efficiency
            (predicted.success_rate - current.success_rate) * 10  # 10% weight on reliability
        ) * 100
        
        return max(0, min(100, score))

# Global instance
_pipeline_optimizer: Optional[PipelineOptimizer] = None

def get_pipeline_optimizer() -> PipelineOptimizer:
    """Get or create pipeline optimizer instance"""
    global _pipeline_optimizer
    if _pipeline_optimizer is None:
        _pipeline_optimizer = PipelineOptimizer()
    return _pipeline_optimizer