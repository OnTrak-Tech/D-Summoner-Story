"""
Centralized error handling for Lambda functions.
Provides secure error responses that don't leak internal details.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Application error codes for client debugging."""
    
    # Authentication errors (1xx)
    MISSING_API_KEY = "ERR_101"
    INVALID_API_KEY = "ERR_102"
    SESSION_EXPIRED = "ERR_103"
    
    # Validation errors (2xx)
    INVALID_REQUEST = "ERR_201"
    INVALID_REGION = "ERR_202"
    MISSING_REQUIRED_FIELD = "ERR_203"
    
    # Resource errors (3xx)
    SUMMONER_NOT_FOUND = "ERR_301"
    JOB_NOT_FOUND = "ERR_302"
    INSIGHTS_NOT_FOUND = "ERR_303"
    
    # External service errors (4xx)
    RIOT_API_ERROR = "ERR_401"
    RIOT_RATE_LIMITED = "ERR_402"
    BEDROCK_ERROR = "ERR_403"
    
    # Internal errors (5xx)
    INTERNAL_ERROR = "ERR_500"
    DATABASE_ERROR = "ERR_501"
    STORAGE_ERROR = "ERR_502"


# Human-readable messages for each error code (safe to show clients)
ERROR_MESSAGES: Dict[ErrorCode, str] = {
    ErrorCode.MISSING_API_KEY: "API key is required",
    ErrorCode.INVALID_API_KEY: "Invalid API key",
    ErrorCode.SESSION_EXPIRED: "Session has expired",
    ErrorCode.INVALID_REQUEST: "Invalid request format",
    ErrorCode.INVALID_REGION: "Region is not supported",
    ErrorCode.MISSING_REQUIRED_FIELD: "Required field is missing",
    ErrorCode.SUMMONER_NOT_FOUND: "Summoner not found in the specified region",
    ErrorCode.JOB_NOT_FOUND: "Job not found",
    ErrorCode.INSIGHTS_NOT_FOUND: "Insights not found for this session",
    ErrorCode.RIOT_API_ERROR: "Failed to fetch data from game server",
    ErrorCode.RIOT_RATE_LIMITED: "Too many requests, please try again later",
    ErrorCode.BEDROCK_ERROR: "AI service temporarily unavailable",
    ErrorCode.INTERNAL_ERROR: "An unexpected error occurred",
    ErrorCode.DATABASE_ERROR: "Database operation failed",
    ErrorCode.STORAGE_ERROR: "Storage operation failed",
}


class AppError(Exception):
    """Application error with error code and optional internal details."""
    
    def __init__(
        self, 
        code: ErrorCode, 
        internal_message: Optional[str] = None,
        status_code: int = 400
    ):
        self.code = code
        self.internal_message = internal_message
        self.status_code = status_code
        self.message = ERROR_MESSAGES.get(code, "An error occurred")
        super().__init__(self.message)
    
    def to_response(self) -> Dict[str, Any]:
        """Return client-safe error response."""
        return {
            "error": self.code.name,
            "error_code": self.code.value,
            "message": self.message
        }
    
    def log(self) -> None:
        """Log full error details server-side."""
        log_message = f"[{self.code.value}] {self.code.name}"
        if self.internal_message:
            log_message += f" - {self.internal_message}"
        logger.error(log_message)


def handle_exception(e: Exception, default_code: ErrorCode = ErrorCode.INTERNAL_ERROR) -> AppError:
    """
    Convert any exception to an AppError for safe client response.
    Logs the original exception server-side.
    """
    if isinstance(e, AppError):
        e.log()
        return e
    
    # Log the full exception for debugging
    logger.exception(f"Unhandled exception: {type(e).__name__}")
    
    # Return generic error to client
    return AppError(
        code=default_code,
        internal_message=str(e),
        status_code=500
    )
