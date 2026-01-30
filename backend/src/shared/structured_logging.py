"""
Structured Logging Utility
Provides JSON-formatted logging with correlation IDs for distributed tracing.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, service_name: str = "summoner-story"):
        super().__init__()
        self.service_name = service_name
        self.environment = os.environ.get("ENVIRONMENT", "dev")
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "environment": self.environment,
            "message": record.getMessage(),
            "logger": record.name,
            "location": {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName
            }
        }
        
        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id
        
        # Add request context if available
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
            
        # Add user context if available
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_entry["extra"] = record.extra
            
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)


class StructuredLogger:
    """
    Structured logger with correlation ID support.
    
    Usage:
        logger = StructuredLogger("my-lambda")
        logger.set_correlation_id(event)
        logger.info("Processing request", extra={"session_id": "123"})
    """
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Add structured handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter(service_name=name))
        self.logger.addHandler(handler)
        
        # Context for all log entries
        self.context: Dict[str, Any] = {}
    
    def set_correlation_id(self, event: Optional[Dict[str, Any]] = None) -> str:
        """
        Set or extract correlation ID from event.
        
        Looks for correlation ID in:
        1. Event headers (X-Correlation-ID)
        2. Event requestContext
        3. Generates new UUID if not found
        """
        correlation_id = None
        
        if event:
            # Check headers
            headers = event.get("headers", {}) or {}
            correlation_id = headers.get("X-Correlation-ID") or headers.get("x-correlation-id")
            
            # Check request context
            if not correlation_id:
                request_context = event.get("requestContext", {})
                correlation_id = request_context.get("requestId")
        
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        self.context["correlation_id"] = correlation_id
        return correlation_id
    
    def set_user_context(self, user_id: str, email: Optional[str] = None):
        """Set user context for all subsequent log entries."""
        self.context["user_id"] = user_id
        if email:
            self.context["email"] = email
    
    def set_request_id(self, request_id: str):
        """Set Lambda request ID for tracing."""
        self.context["request_id"] = request_id
    
    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """Internal log method with context injection."""
        log_extra = {**self.context}
        if extra:
            log_extra["extra"] = extra
        
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(unknown file)",
            0,
            message,
            (),
            None
        )
        
        # Inject context as record attributes
        for key, value in log_extra.items():
            setattr(record, key, value)
        
        self.logger.handle(record)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log(logging.DEBUG, message, extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._log(logging.ERROR, message, extra)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        self._log(logging.CRITICAL, message, extra)


def get_structured_logger(name: str, level: str = "INFO") -> StructuredLogger:
    """Get a configured structured logger instance."""
    return StructuredLogger(name, level)


# Lambda-specific helper
def init_lambda_logger(
    event: Dict[str, Any],
    context: Any,
    name: str = "lambda"
) -> StructuredLogger:
    """
    Initialize structured logger for Lambda function.
    
    Args:
        event: Lambda event
        context: Lambda context
        name: Logger name
        
    Returns:
        Configured structured logger with request context
    """
    level = os.environ.get("LOG_LEVEL", "INFO")
    logger = get_structured_logger(name, level)
    
    # Set correlation ID from event
    logger.set_correlation_id(event)
    
    # Set Lambda request ID
    if context and hasattr(context, "aws_request_id"):
        logger.set_request_id(context.aws_request_id)
    
    # Extract user context if available
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    if authorizer.get("uid"):
        logger.set_user_context(
            user_id=authorizer.get("uid"),
            email=authorizer.get("email")
        )
    
    return logger
