"""
Logging configuration for GitAIOps platform
"""
import logging
import sys
from typing import Optional
import structlog
from structlog.stdlib import LoggerFactory
from pythonjsonlogger import jsonlogger
from src.core.config import get_settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """Configure structured logging for the application"""
    settings = get_settings()
    level = log_level or settings.log_level
    
    # Configure Python's logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper())
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer() if settings.log_format == "json" 
            else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


# Configure JSON formatter for standard logging
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['environment'] = get_settings().environment


# Logging utilities
class LogContext:
    """Context manager for adding temporary logging context"""
    
    def __init__(self, logger: structlog.BoundLogger, **kwargs):
        self.logger = logger
        self.context = kwargs
        self.token = None
    
    def __enter__(self):
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            structlog.contextvars.unbind_contextvars(**self.context)


def log_method_call(func):
    """Decorator to log method calls"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.info(
            "method_called",
            method=func.__name__,
            args=args[1:] if args else [],  # Skip self
            kwargs=kwargs
        )
        try:
            result = func(*args, **kwargs)
            logger.info(
                "method_completed",
                method=func.__name__,
                success=True
            )
            return result
        except Exception as e:
            logger.error(
                "method_failed",
                method=func.__name__,
                error=str(e),
                exc_info=True
            )
            raise
    return wrapper
