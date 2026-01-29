from __future__ import annotations
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Literal
from uuid import uuid4

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils import format_lambda_response
from shared.errors import AppError, ErrorCode, handle_exception


@dataclass
class AuthRequest:
    summoner_name: str
    region: str


@dataclass
class AuthResponse:
    session_id: str
    status: Literal["valid", "invalid"]


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda entrypoint: validates input and issues a session id.
    
    Note: This is a PUBLIC route - no Firebase auth required.
    Users call this before they're authenticated to validate game accounts.
    """
    try:
        
        body = event.get("body")
        if isinstance(body, str):
            payload = json.loads(body or "{}")
        elif isinstance(body, dict):
            payload = body
        else:
            payload = {}

        summoner_name = (payload.get("summoner_name") or "").strip()
        region = (payload.get("region") or "").strip()

        if not summoner_name or not region:
            error = AppError(
                ErrorCode.MISSING_REQUIRED_FIELD,
                "summoner_name and region are required"
            )
            error.log()
            return format_lambda_response(400, error.to_response())

        session_id = str(uuid4())
        return format_lambda_response(200, {
            "session_id": session_id,
            "status": "valid",
        })
        
    except Exception as e:
        error = handle_exception(e)
        return format_lambda_response(error.status_code, error.to_response())

