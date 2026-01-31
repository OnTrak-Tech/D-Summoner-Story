"""
Auth Fortnite Lambda Function
Validates Fortnite/Epic accounts and links them to authenticated Firebase users.

Flow:
1. User is authenticated via Firebase (authorizer passes uid)
2. User provides Epic username
3. Lambda validates via FortniteAPI.com and fetches stats
4. Lambda links the account to user in DynamoDB
"""

import json
import os
import sys
import logging
from typing import Any, Dict, Optional
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils import format_lambda_response, setup_logging
from shared.errors import AppError, ErrorCode, handle_exception
from shared.firebase_auth import extract_user_from_event
from shared.aws_clients import get_dynamodb_client, get_table_name, get_ssm_client

# Setup logging
setup_logging(os.environ.get('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Fortnite API constants (using fortnite-api.com)
FORTNITE_API_BASE = "https://fortnite-api.com/v2"


class FortniteAPIError(Exception):
    """Custom exception for Fortnite API errors"""
    pass


class FortniteUserNotFound(FortniteAPIError):
    """Exception for Fortnite user not found"""
    pass


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for linking Fortnite/Epic accounts to Firebase users.
    
    Request body:
    {
        "epic_username": "PlayerName",
        "account_type": "epic"  // epic, psn, xbl (optional, defaults to epic)
    }
    
    Response:
    {
        "linked": true,
        "platform": "fortnite",
        "account": {
            "epic_username": "PlayerName",
            "account_id": "...",
            "stats": {...}
        }
    }
    """
    try:
        # Extract authenticated user from authorizer
        user = extract_user_from_event(event)
        if not user or not user.get('uid'):
            return format_lambda_response(401, {
                "error": "Unauthorized",
                "message": "Valid Firebase authentication required"
            })
        
        user_id = user['uid']
        logger.info(f"Linking Fortnite account for user: {user_id}")
        
        # Parse request body
        body = event.get("body", "{}")
        if isinstance(body, str):
            body = json.loads(body)
        
        epic_username = (body.get("epic_username") or "").strip()
        account_type = (body.get("account_type") or "epic").strip().lower()
        
        # Validate inputs
        if not epic_username:
            return format_lambda_response(400, {
                "error": "Missing required field",
                "message": "epic_username is required"
            })
        
        # Validate account type
        valid_account_types = {"epic", "psn", "xbl"}
        if account_type not in valid_account_types:
            return format_lambda_response(400, {
                "error": "Invalid account type",
                "message": f"account_type must be one of: {', '.join(valid_account_types)}"
            })
        
        # Validate username format (3-16 chars, alphanumeric + some special)
        if not _validate_epic_username(epic_username):
            return format_lambda_response(400, {
                "error": "Invalid username",
                "message": "Epic username must be 3-16 characters"
            })
        
        # Get Fortnite API key from SSM
        api_key = _get_fortnite_api_key()
        
        # Fetch player stats from Fortnite API
        try:
            player_stats = _get_player_stats(api_key, epic_username, account_type)
        except FortniteUserNotFound:
            return format_lambda_response(404, {
                "error": "User not found",
                "message": f"Could not find Fortnite player '{epic_username}'"
            })
        except FortniteAPIError as e:
            logger.error(f"Fortnite API error: {e}")
            return format_lambda_response(502, {
                "error": "Platform error",
                "message": "Failed to validate account with Fortnite API"
            })
        
        # Extract key stats for linking
        account_data = {
            "epic_username": epic_username,
            "account_type": account_type,
            "account_id": player_stats.get("account", {}).get("id", ""),
            "account_name": player_stats.get("account", {}).get("name", epic_username),
            "battle_pass_level": player_stats.get("battlePass", {}).get("level", 0),
            "overall_stats": _extract_overall_stats(player_stats),
        }
        
        link_result = _link_platform_account(
            user_id=user_id,
            platform="fortnite",
            account_data=account_data
        )
        
        return format_lambda_response(200, {
            "linked": True,
            "platform": "fortnite",
            "account": account_data,
            "message": "Fortnite account successfully linked"
        })
        
    except Exception as e:
        error = handle_exception(e)
        return format_lambda_response(error.status_code, error.to_response())


def _validate_epic_username(username: str) -> bool:
    """Validate Epic Games username format."""
    if len(username) < 3 or len(username) > 16:
        return False
    # Epic allows alphanumeric, spaces, dashes, underscores, periods
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.")
    return all(c in allowed_chars for c in username)


def _get_fortnite_api_key() -> str:
    """Get Fortnite API key from SSM Parameter Store."""
    ssm = get_ssm_client()
    ssm_path = os.environ.get('SSM_PATH_PREFIX', '/summoner-story/dev')
    
    try:
        response = ssm.get_parameter(
            Name=f"{ssm_path}/fortnite-api-key",
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f"Failed to get Fortnite API key: {e}")
        raise FortniteAPIError("Failed to retrieve Fortnite API key")


def _get_player_stats(api_key: str, username: str, account_type: str) -> Dict[str, Any]:
    """
    Get Fortnite player stats from FortniteAPI.com.
    
    Endpoint: GET /v2/stats/br/v2
    Params: name, accountType
    """
    url = f"{FORTNITE_API_BASE}/stats/br/v2"
    params = urllib.parse.urlencode({
        "name": username,
        "accountType": account_type
    })
    
    try:
        req = urllib.request.Request(
            f"{url}?{params}",
            headers={
                "Authorization": api_key
            }
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if data.get("status") == 200:
                return data.get("data", {})
            elif data.get("status") == 404:
                raise FortniteUserNotFound(f"Player not found: {username}")
            else:
                raise FortniteAPIError(f"API error: {data.get('error', 'Unknown')}")
                
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise FortniteUserNotFound(f"Player not found: {username}")
        elif e.code == 403:
            # Private profile
            raise FortniteAPIError("Player profile is private")
        raise FortniteAPIError(f"Fortnite API error: {e.code}")
    except urllib.error.URLError as e:
        raise FortniteAPIError(f"Fortnite API connection error: {e.reason}")


def _extract_overall_stats(player_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Extract overall gameplay stats from API response."""
    stats = player_stats.get("stats", {})
    overall = stats.get("all", {}).get("overall", {})
    
    return {
        "wins": overall.get("wins", 0),
        "top5": overall.get("top5", 0),
        "top10": overall.get("top10", 0),
        "top25": overall.get("top25", 0),
        "kills": overall.get("kills", 0),
        "deaths": overall.get("deaths", 0),
        "kd": overall.get("kd", 0.0),
        "matches": overall.get("matches", 0),
        "win_rate": overall.get("winRate", 0.0),
        "minutes_played": overall.get("minutesPlayed", 0),
        "score": overall.get("score", 0),
    }


def _link_platform_account(
    user_id: str,
    platform: str,
    account_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Link a gaming platform account to a Firebase user in DynamoDB.
    
    DynamoDB Item:
    PK: USER#{user_id}
    SK: PLATFORM#fortnite
    """
    dynamodb = get_dynamodb_client()
    table_name = get_table_name("PLAYER_STATS_TABLE")
    
    now = datetime.utcnow().isoformat() + "Z"
    
    # Flatten overall_stats into the item
    overall_stats = account_data.pop("overall_stats", {})
    
    item = {
        "PK": f"USER#{user_id}",
        "SK": f"PLATFORM#{platform}",
        "platform": platform,
        "linked_at": now,
        "updated_at": now,
        **account_data,
        **overall_stats  # Flatten stats into item
    }
    
    dynamodb.put_item(
        TableName=table_name,
        Item={k: _to_dynamodb_value(v) for k, v in item.items() if v is not None}
    )
    
    logger.info(f"Linked {platform} account for user {user_id}")
    return item


def _to_dynamodb_value(value: Any) -> Dict[str, Any]:
    """Convert Python value to DynamoDB attribute value."""
    if isinstance(value, str):
        return {"S": value}
    elif isinstance(value, bool):
        return {"BOOL": value}
    elif isinstance(value, (int, float)):
        return {"N": str(value)}
    elif value is None:
        return {"NULL": True}
    elif isinstance(value, list):
        return {"L": [_to_dynamodb_value(v) for v in value]}
    elif isinstance(value, dict):
        return {"M": {k: _to_dynamodb_value(v) for k, v in value.items()}}
    else:
        return {"S": str(value)}
