"""
Gemini AI client for GitAIOps platform
"""
import asyncio
import json
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import structlog
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings

logger = structlog.get_logger(__name__)

class GeminiClient:
    """Client for Google Gemini AI API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = "AIzaSyB4YZNa8VKU9wycDgeQEiskINX57xf24Gc"  # Using provided API key
        self.model = "gemini-2.0-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.cache = TTLCache(maxsize=1000, ttl=1800)  # 30 min cache
        self.session = None
        self._init_session()
    
    def _init_session(self):
        """Initialize aiohttp session"""
        if not self.api_key:
            logger.warning("Gemini API key not configured, AI features will use fallback responses")
            return
        
        try:
            self.session = aiohttp.ClientSession()
            logger.info("Gemini client initialized", model=self.model)
        except Exception as e:
            logger.error("Failed to initialize Gemini client", error=str(e))
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def is_available(self) -> bool:
        """Check if Gemini is available"""
        return self.session is not None and self.api_key is not None
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Convert OpenAI-style messages to Gemini format"""
        contents = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            # Gemini doesn't have a system role, so we'll prepend system messages to the first user message
            if role == "system":
                if contents and contents[0]["role"] == "user":
                    contents[0]["parts"][0]["text"] = f"{content}\n\n{contents[0]['parts'][0]['text']}"
                else:
                    contents.insert(0, {
                        "role": "user",
                        "parts": [{"text": f"System: {content}\n\nUser: Please acknowledge this system prompt."}]
                    })
                    contents.insert(1, {
                        "role": "model",
                        "parts": [{"text": "I understand the system context and will follow the instructions."}]
                    })
            elif role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role == "assistant":
                contents.append({
                    "role": "model",
                    "parts": [{"text": content}]
                })
        
        return contents
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        use_cache: bool = True
    ) -> Optional[str]:
        """Get chat completion from Gemini"""
        
        if not await self.is_available():
            logger.warning("Gemini not available, returning None")
            return None
        
        # Create cache key
        cache_key = None
        if use_cache:
            cache_key = self._create_cache_key(messages, temperature, max_tokens)
            if cache_key in self.cache:
                logger.debug("Cache hit for Gemini request")
                return self.cache[cache_key]
        
        try:
            logger.info(
                "Making Gemini API request",
                model=self.model,
                messages_count=len(messages),
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Convert messages to Gemini format
            contents = self._convert_messages_to_gemini_format(messages)
            
            # Build request body
            request_body = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.95,
                    "topK": 40
                }
            }
            
            # Make API request
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            
            async with self.session.post(url, json=request_body) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        "Gemini API request failed",
                        status=response.status,
                        error=error_text
                    )
                    return None
                
                data = await response.json()
                
                # Extract response text
                if data.get("candidates") and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if candidate.get("content") and candidate["content"].get("parts"):
                        content = candidate["content"]["parts"][0].get("text", "")
                        
                        # Cache the response
                        if use_cache and cache_key and content:
                            self.cache[cache_key] = content
                        
                        logger.info(
                            "Gemini API request successful",
                            model=self.model,
                            response_length=len(content) if content else 0
                        )
                        
                        return content
                
                logger.warning("No response content from Gemini")
                return None
                
        except Exception as e:
            logger.error(
                "Gemini API request failed",
                model=self.model,
                error=str(e),
                exc_info=True
            )
            raise
    
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
            "reasoning": "Fallback analysis - Gemini AI unavailable"
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
            "reasoning": "Fallback analysis - Gemini AI unavailable"
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
_gemini_client: Optional[GeminiClient] = None

def get_gemini_client() -> GeminiClient:
    """Get or create Gemini client instance"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client