"""
OpenRouter AI client for GitAIOps platform
"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import structlog
from openai import AsyncOpenAI
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings

logger = structlog.get_logger(__name__)

class OpenRouterClient:
    """Enhanced OpenRouter AI client with multiple API keys and Claude Sonnet 4"""
    
    def __init__(self):
        self.settings = get_settings()
        self.clients = []
        self.current_client_index = 0
        self.model = self.settings.openrouter_model
        self.cache = TTLCache(maxsize=1000, ttl=1800)  # 30 min cache
        self.failed_keys = set()  # Track failed API keys
        self._init_clients()
    
    def _init_clients(self):
        """Initialize multiple OpenAI clients for load balancing"""
        api_keys = getattr(self.settings, 'openrouter_api_keys', [])
        
        # Fallback to single key if list not available
        if not api_keys and self.settings.openrouter_api_key:
            api_keys = [self.settings.openrouter_api_key]
        
        if not api_keys:
            logger.warning("No OpenRouter API keys configured, AI features will use fallback responses")
            return
        
        for i, api_key in enumerate(api_keys):
            try:
                client = AsyncOpenAI(
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                self.clients.append({
                    'client': client,
                    'api_key': api_key,
                    'index': i,
                    'failures': 0,
                    'last_success': datetime.now()
                })
                logger.info(f"OpenRouter client {i+1} initialized", model=self.model, key_suffix=api_key[-8:])
            except Exception as e:
                logger.error(f"Failed to initialize OpenRouter client {i+1}", error=str(e), key_suffix=api_key[-8:])
        
        if self.clients:
            logger.info(f"OpenRouter initialized with {len(self.clients)} API keys", model=self.model)
        else:
            logger.error("No OpenRouter clients could be initialized")
    
    def _get_next_client(self):
        """Get next available client using round-robin with failure tracking"""
        if not self.clients:
            return None
        
        # Filter out failed clients (more than 3 failures in last hour)
        available_clients = [
            client for client in self.clients 
            if client['failures'] < 3 or 
            (datetime.now() - client['last_success']).seconds > 3600
        ]
        
        if not available_clients:
            # Reset failure counts if all clients are marked as failed
            for client in self.clients:
                client['failures'] = 0
            available_clients = self.clients
        
        # Round-robin selection
        client = available_clients[self.current_client_index % len(available_clients)]
        self.current_client_index = (self.current_client_index + 1) % len(available_clients)
        
        return client
    
    async def is_available(self) -> bool:
        """Check if OpenRouter is available"""
        return len(self.clients) > 0
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        use_cache: bool = True
    ) -> Optional[str]:
        """Get chat completion from OpenRouter with automatic failover"""
        
        if not await self.is_available():
            logger.warning("OpenRouter not available, returning None")
            return None
        
        # Create cache key
        cache_key = None
        if use_cache:
            cache_key = self._create_cache_key(messages, temperature, max_tokens)
            if cache_key in self.cache:
                logger.debug("Cache hit for OpenRouter request")
                return self.cache[cache_key]
        
        # Try each available client
        last_error = None
        for attempt in range(len(self.clients)):
            client_info = self._get_next_client()
            if not client_info:
                break
                
            try:
                logger.info(
                    "Making OpenRouter API request",
                    model=self.model,
                    client_index=client_info['index'],
                    messages_count=len(messages),
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                response = await client_info['client'].chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    extra_headers={
                        "HTTP-Referer": "https://gitaiops.com",
                        "X-Title": "GitAIOps Platform - Claude Sonnet 4"
                    }
                )
                
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    
                    # Mark success
                    client_info['last_success'] = datetime.now()
                    client_info['failures'] = max(0, client_info['failures'] - 1)
                    
                    # Cache the response
                    if use_cache and cache_key:
                        self.cache[cache_key] = content
                    
                    logger.info(
                        "OpenRouter API request successful",
                        model=self.model,
                        client_index=client_info['index'],
                        response_length=len(content) if content else 0,
                        usage=response.usage.total_tokens if response.usage else None
                    )
                    
                    return content
                else:
                    logger.warning("No response content from OpenRouter", client_index=client_info['index'])
                    client_info['failures'] += 1
                    continue
                    
            except Exception as e:
                client_info['failures'] += 1
                last_error = e
                logger.warning(
                    "OpenRouter API request failed, trying next client",
                    model=self.model,
                    client_index=client_info['index'],
                    error=str(e),
                    attempt=attempt + 1,
                    total_clients=len(self.clients)
                )
                continue
        
        # All clients failed
        logger.error(
            "All OpenRouter clients failed",
            model=self.model,
            total_attempts=len(self.clients),
            last_error=str(last_error) if last_error else "Unknown"
        )
        return None
    
    def _create_cache_key(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
        """Create cache key for request"""
        import hashlib
        
        # Create a unique key based on request parameters
        key_data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def analyze_merge_request(
        self,
        mr_data: Dict[str, Any],
        changes_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze merge request using AI"""
        
        # Prepare context for AI
        mr_title = mr_data.get("title", "")
        mr_description = mr_data.get("description", "")
        
        # Summarize changes to avoid token limits
        changes_summary = []
        total_additions = 0
        total_deletions = 0
        file_types = set()
        
        for change in changes_data[:20]:  # Limit to first 20 files
            file_path = change.get("old_path", change.get("new_path", ""))
            if file_path:
                file_ext = file_path.split('.')[-1] if '.' in file_path else "unknown"
                file_types.add(file_ext)
                
                additions = change.get("additions", 0) or 0
                deletions = change.get("deletions", 0) or 0
                
                try:
                    additions = int(additions) if isinstance(additions, str) else additions
                    deletions = int(deletions) if isinstance(deletions, str) else deletions
                except (ValueError, TypeError):
                    additions = deletions = 0
                
                total_additions += additions
                total_deletions += deletions
                
                changes_summary.append({
                    "file": file_path,
                    "additions": additions,
                    "deletions": deletions,
                    "type": file_ext
                })
        
        prompt = f"""Analyze this GitLab merge request and provide a JSON response with risk assessment and recommendations.

**Merge Request Details:**
- Title: {mr_title}
- Description: {mr_description}
- Total files changed: {len(changes_data)}
- Total additions: {total_additions}
- Total deletions: {total_deletions}
- File types: {', '.join(file_types)}

**Key Changes:**
{json.dumps(changes_summary[:10], indent=2)}

Please analyze this merge request and respond with a JSON object containing:
1. risk_level (low, medium, high, critical)
2. risk_score (0.0 to 1.0)
3. mr_type (feature, bugfix, docs, security, refactor, test, config)
4. complexity (simple, moderate, complex, very_complex)
5. estimated_review_hours (decimal number)
6. risk_factors (array of strings describing specific risks)
7. review_requirements (object with boolean flags for security_review, performance_review, etc.)
8. suggested_labels (array of strings)
9. confidence_score (0.0 to 1.0 indicating analysis confidence)
10. reasoning (brief explanation of the analysis)

Consider factors like:
- Security implications (auth changes, permission changes, etc.)
- Database/migration changes
- Core system modifications
- Test coverage
- Breaking changes
- Performance impacts

Respond only with valid JSON."""
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert DevOps engineer and code reviewer specializing in risk assessment for merge requests. Provide thorough, accurate analysis in the requested JSON format."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        try:
            response = await self.chat_completion(messages, temperature=0.3, max_tokens=2000)
            if response:
                # Try to parse JSON response
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    # Extract JSON from response if it's wrapped in text
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    else:
                        logger.error("Could not parse AI response as JSON", response=response[:200])
                        return self._fallback_mr_analysis()
            else:
                return self._fallback_mr_analysis()
                
        except Exception as e:
            logger.error("AI merge request analysis failed", error=str(e))
            return self._fallback_mr_analysis()
    
    async def analyze_pipeline_optimization(
        self,
        pipeline_data: Dict[str, Any],
        current_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze pipeline for optimization opportunities"""
        
        prompt = f"""Analyze this CI/CD pipeline for optimization opportunities and provide recommendations.

**Pipeline Metrics:**
{json.dumps(current_metrics, indent=2)}

**Pipeline Data:**
{json.dumps(pipeline_data, indent=2)}

Please analyze this pipeline and respond with a JSON object containing:
1. optimization_score (0-100)
2. recommendations (array of objects with type, description, estimated_impact, difficulty, risk_level)
3. predicted_improvements (object with duration_reduction, cost_savings percentages)
4. bottlenecks (array of identified bottleneck stages)
5. quick_wins (array of easy optimization opportunities)
6. reasoning (explanation of analysis)

Focus on:
- Parallelization opportunities
- Caching strategies
- Resource optimization
- Image optimization
- Test optimization
- Dependency management

Respond only with valid JSON."""

        messages = [
            {
                "role": "system",
                "content": "You are an expert DevOps engineer specializing in CI/CD pipeline optimization. Provide detailed, actionable recommendations in the requested JSON format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = await self.chat_completion(messages, temperature=0.4, max_tokens=3000)
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    else:
                        return self._fallback_pipeline_analysis()
            else:
                return self._fallback_pipeline_analysis()
                
        except Exception as e:
            logger.error("AI pipeline optimization analysis failed", error=str(e))
            return self._fallback_pipeline_analysis()
    
    async def process_chatops_message(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process ChatOps message with AI"""
        
        prompt = f"""You are an intelligent DevOps assistant for GitAIOps platform. Analyze this user message and provide helpful assistance.

**User Message:** {message}
**Context:** {json.dumps(context, indent=2)}

Based on the message, determine the user's intent and provide a helpful response. Consider these capabilities:
- Build/Pipeline diagnosis and troubleshooting
- Merge request analysis
- Optimization suggestions
- Error explanation
- General DevOps guidance

Respond with a JSON object containing:
1. intent (diagnose_build, analyze_mr, explain_error, optimize_pipeline, provide_help, unknown)
2. confidence (0.0 to 1.0)
3. response_text (helpful response to the user)
4. suggested_actions (array of next steps)
5. requires_escalation (boolean)
6. extracted_data (object with any IDs, numbers, or specific data extracted from the message)

Provide practical, actionable advice. If you can't help with something, suggest alternatives or escalation.

Respond only with valid JSON."""

        messages = [
            {
                "role": "system",
                "content": "You are an expert DevOps assistant with deep knowledge of CI/CD, GitLab, debugging, and software development best practices. Provide helpful, accurate, and actionable guidance."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = await self.chat_completion(messages, temperature=0.6, max_tokens=1500)
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    else:
                        return self._fallback_chatops_response(message)
            else:
                return self._fallback_chatops_response(message)
                
        except Exception as e:
            logger.error("AI ChatOps processing failed", error=str(e))
            return self._fallback_chatops_response(message)
    
    def _fallback_mr_analysis(self) -> Dict[str, Any]:
        """Fallback analysis when AI is unavailable"""
        return {
            "risk_level": "medium",
            "risk_score": 0.5,
            "mr_type": "feature",
            "complexity": "moderate",
            "estimated_review_hours": 1.0,
            "risk_factors": ["AI analysis unavailable - manual review recommended"],
            "review_requirements": {
                "security_review": False,
                "performance_review": False,
                "architecture_review": False
            },
            "suggested_labels": ["needs-review"],
            "confidence_score": 0.1,
            "reasoning": "Fallback analysis - OpenRouter AI unavailable"
        }
    
    def _fallback_pipeline_analysis(self) -> Dict[str, Any]:
        """Fallback pipeline analysis when AI is unavailable"""
        return {
            "optimization_score": 50,
            "recommendations": [
                {
                    "type": "caching",
                    "description": "Consider adding dependency caching",
                    "estimated_impact": {"duration_reduction": 0.2, "cost_savings": 0.15},
                    "difficulty": "easy",
                    "risk_level": "low"
                }
            ],
            "predicted_improvements": {
                "duration_reduction": 0.2,
                "cost_savings": 0.15
            },
            "bottlenecks": ["unknown"],
            "quick_wins": ["Add dependency caching"],
            "reasoning": "Fallback analysis - OpenRouter AI unavailable"
        }
    
    def _fallback_chatops_response(self, message: str) -> Dict[str, Any]:
        """Fallback ChatOps response when AI is unavailable"""
        return {
            "intent": "provide_help",
            "confidence": 0.1,
            "response_text": f"I received your message: '{message}', but AI analysis is currently unavailable. Please check the GitAIOps documentation or contact support for assistance.",
            "suggested_actions": ["Check documentation", "Contact support", "Try again later"],
            "requires_escalation": True,
            "extracted_data": {}
        }

# Global instance
_openrouter_client: Optional[OpenRouterClient] = None

def get_openrouter_client() -> OpenRouterClient:
    """Get or create OpenRouter client instance"""
    global _openrouter_client
    if _openrouter_client is None:
        _openrouter_client = OpenRouterClient()
    return _openrouter_client