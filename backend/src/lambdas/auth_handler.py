from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Dict, Literal
from uuid import uuid4


@dataclass
class AuthRequest:
    summoner_name: str
    region: str


@dataclass
class AuthResponse:
    session_id: str
    status: Literal["valid", "invalid"]


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda entrypoint: validates input and issues a session id.

    This is a minimal placeholder aligned with the Design spec. Full authentication,
    rate limiting, and credential retrieval from AWS Secrets Manager will be added
    in later tasks.
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
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "message": "summoner_name and region are required"
                }),
            }

        session_id = str(uuid4())
        resp = AuthResponse(session_id=session_id, status="valid")
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "session_id": resp.session_id,
                "status": resp.status,
            }),
        }
    except Exception:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Internal server error"}),
        }
