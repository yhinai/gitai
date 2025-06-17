"""
Configuration management for GitAIOps platform
"""
import os
from typing import Optional, Dict, Any
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "GitAIOps Platform"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8080, env="API_PORT")
    api_prefix: str = "/api/v1"
    
    # Google Cloud
    gcp_project_id: Optional[str] = Field(default=None, env="GCP_PROJECT_ID")
    gcp_location: str = Field(default="us-central1", env="GCP_LOCATION")
    
    # GitLab - Hardcoded credentials
    gitlab_url: str = Field(default="https://gitlab.com", env="GITLAB_URL")
    gitlab_api_url: str = Field(default="https://gitlab.com/api/v4", env="GITLAB_API_URL")
    gitlab_token: Optional[str] = Field(default="glpat-aTrQQ4EqmxGpGh3Ddcgm", env="GITLAB_TOKEN")
    gitlab_access_token: Optional[str] = Field(default="glpat-aTrQQ4EqmxGpGh3Ddcgm", env="GITLAB_ACCESS_TOKEN")
    gitlab_project_id: Optional[int] = Field(default=278964, env="GITLAB_PROJECT_ID")
    gitlab_webhook_secret: Optional[str] = Field(default=None, env="GITLAB_WEBHOOK_SECRET")
    
    # Database
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Neo4j (for CodeCompass knowledge graph)
    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USERNAME: str = Field(default="neo4j", env="NEO4J_USERNAME") 
    NEO4J_PASSWORD: str = Field(default="password", env="NEO4J_PASSWORD")
    NEO4J_DATABASE: str = Field(default="neo4j", env="NEO4J_DATABASE")
    
    # AI/ML - OpenRouter with Claude Sonnet 4 as main decision-making LLM
    vertex_ai_endpoint: Optional[str] = Field(default=None, env="VERTEX_AI_ENDPOINT")
    ai_model_cache_ttl: int = Field(default=3600, env="MODEL_CACHE_TTL")
    openrouter_api_key: Optional[str] = Field(default="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", env="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="anthropic/claude-sonnet-4", env="OPENROUTER_MODEL")
    
    # Additional OpenRouter API keys for load balancing and redundancy
    openrouter_api_keys: list = Field(default=[
        "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",
        "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",
        "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",
        "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"
    ])
    
    # Feature flags
    enable_mr_triage: bool = Field(default=True, env="ENABLE_MR_TRIAGE")
    enable_expert_finder: bool = Field(default=True, env="ENABLE_EXPERT_FINDER")
    enable_pipeline_optimizer: bool = Field(default=True, env="ENABLE_PIPELINE_OPTIMIZER")
    enable_vulnerability_scanner: bool = Field(default=True, env="ENABLE_VULNERABILITY_SCANNER")
    enable_chatops_bot: bool = Field(default=True, env="ENABLE_CHATOPS_BOT")
    
    # Service settings
    neo4j_enabled: bool = Field(default=False, env="NEO4J_ENABLED")
    ai_services_enabled: bool = Field(default=True, env="AI_SERVICES_ENABLED")
    
    # Performance settings
    max_concurrent_analyses: int = Field(default=5, env="MAX_CONCURRENT_ANALYSES")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    
    # Security
    secret_key: str = Field(default="dev-secret-key", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = "json"
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        protected_namespaces = ('settings_',)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def get_config() -> Dict[str, Any]:
    """Get configuration as dictionary"""
    settings = get_settings()
    return settings.dict()


# Environment-specific configurations
ENVIRONMENTS = {
    "development": {
        "debug": True,
        "log_level": "DEBUG",
        "reload": True
    },
    "staging": {
        "debug": False,
        "log_level": "INFO",
        "reload": False
    },
    "production": {
        "debug": False,
        "log_level": "WARNING",
        "reload": False
    }
}


def get_environment_config(env: str) -> Dict[str, Any]:
    """Get environment-specific configuration"""
    return ENVIRONMENTS.get(env, ENVIRONMENTS["development"])
