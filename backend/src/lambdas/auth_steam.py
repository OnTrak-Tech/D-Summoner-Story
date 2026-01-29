"""
Auth Steam Lambda Function
Validates Steam accounts and links them to authenticated Firebase users.

Flow:
1. User is authenticated via Firebase (authorizer passes uid)
2. User provides Steam ID or vanity URL
3. Lambda validates the account exists via Steam Web API
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

# Steam API constants
STEAM_API_BASE = "https://api.steampowered.com"


class SteamAPIError(Exception):
    """Custom exception for Steam API errors"""
    pass


class SteamUserNotFound(SteamAPIError):
    """Exception for Steam user not found"""
    pass


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for linking Steam accounts to Firebase users.
    
    Request body:
    {
        "steam_id": "76561198012345678",  // 64-bit Steam ID
        // OR
        "vanity_url": "customurl"  // Steam custom URL
    }
    
    Response:
    {
        "linked": true,
        "platform": "steam",
        "account": {
            "steam_id": "76561198012345678",
            "persona_name": "PlayerName",
            "profile_url": "...",
            "avatar_url": "..."
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
        logger.info(f"Linking Steam account for user: {user_id}")
        
        # Parse request body
        body = event.get("body", "{}")
        if isinstance(body, str):
            body = json.loads(body)
        
        steam_id = (body.get("steam_id") or "").strip()
        vanity_url = (body.get("vanity_url") or "").strip()
        
        # Validate inputs - at least one is required
        if not steam_id and not vanity_url:
            return format_lambda_response(400, {
                "error": "Missing required field",
                "message": "Either steam_id or vanity_url is required"
            })
        
        # Get Steam API key from SSM
        api_key = _get_steam_api_key()
        
        # Resolve vanity URL to Steam ID if needed
        if not steam_id and vanity_url:
            try:
                steam_id = _resolve_vanity_url(api_key, vanity_url)
            except SteamUserNotFound:
                return format_lambda_response(404, {
                    "error": "User not found",
                    "message": f"Could not find Steam user with vanity URL '{vanity_url}'"
                })
        
        # Validate Steam ID format (17 digits starting with 765)
        if not steam_id.isdigit() or len(steam_id) != 17:
            return format_lambda_response(400, {
                "error": "Invalid Steam ID",
                "message": "Steam ID must be a 17-digit number"
            })
        
        # Get player summary from Steam API
        try:
            player_summary = _get_player_summary(api_key, steam_id)
        except SteamUserNotFound:
            return format_lambda_response(404, {
                "error": "User not found",
                "message": f"Could not find Steam user with ID '{steam_id}'"
            })
        except SteamAPIError as e:
            logger.error(f"Steam API error: {e}")
            return format_lambda_response(502, {
                "error": "Platform error",
                "message": "Failed to validate account with Steam API"
            })
        
        # Link account in DynamoDB
        account_data = {
            "steam_id": steam_id,
            "persona_name": player_summary.get("personaname", ""),
            "profile_url": player_summary.get("profileurl", ""),
            "avatar_url": player_summary.get("avatarfull", ""),
            "avatar_medium": player_summary.get("avatarmedium", ""),
            "visibility": player_summary.get("communityvisibilitystate", 1),
            "profile_state": player_summary.get("profilestate", 0)
        }
        
        link_result = _link_platform_account(
            user_id=user_id,
            platform="steam",
            account_data=account_data
        )
        
        return format_lambda_response(200, {
            "linked": True,
            "platform": "steam",
            "account": account_data,
            "message": "Steam account successfully linked"
        })
        
    except Exception as e:
        error = handle_exception(e)
        return format_lambda_response(error.status_code, error.to_response())


def _get_steam_api_key() -> str:
    """Get Steam API key from SSM Parameter Store."""
    ssm = get_ssm_client()
    ssm_path = os.environ.get('SSM_PATH_PREFIX', '/summoner-story/dev')
    
    try:
        response = ssm.get_parameter(
            Name=f"{ssm_path}/steam-api-key",
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f"Failed to get Steam API key: {e}")
        raise SteamAPIError("Failed to retrieve Steam API key")


def _resolve_vanity_url(api_key: str, vanity_url: str) -> str:
    """Resolve Steam vanity URL to 64-bit Steam ID."""
    url = f"{STEAM_API_BASE}/ISteamUser/ResolveVanityURL/v1/"
    params = urllib.parse.urlencode({
        "key": api_key,
        "vanityurl": vanity_url
    })
    
    try:
        with urllib.request.urlopen(f"{url}?{params}", timeout=10) as response:
            data = json.loads(response.read().decode())
            result = data.get("response", {})
            
            if result.get("success") == 1:
                return result.get("steamid")
            else:
                raise SteamUserNotFound(f"Vanity URL not found: {vanity_url}")
                
    except urllib.error.HTTPError as e:
        raise SteamAPIError(f"Steam API error: {e.code}")
    except urllib.error.URLError as e:
        raise SteamAPIError(f"Steam API connection error: {e.reason}")


def _get_player_summary(api_key: str, steam_id: str) -> Dict[str, Any]:
    """Get Steam player summary."""
    url = f"{STEAM_API_BASE}/ISteamUser/GetPlayerSummaries/v2/"
    params = urllib.parse.urlencode({
        "key": api_key,
        "steamids": steam_id
    })
    
    try:
        with urllib.request.urlopen(f"{url}?{params}", timeout=10) as response:
            data = json.loads(response.read().decode())
            players = data.get("response", {}).get("players", [])
            
            if players:
                return players[0]
            else:
                raise SteamUserNotFound(f"Steam ID not found: {steam_id}")
                
    except urllib.error.HTTPError as e:
        raise SteamAPIError(f"Steam API error: {e.code}")
    except urllib.error.URLError as e:
        raise SteamAPIError(f"Steam API connection error: {e.reason}")


def _link_platform_account(
    user_id: str,
    platform: str,
    account_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Link a gaming platform account to a Firebase user in DynamoDB.
    
    DynamoDB Item:
    PK: USER#{user_id}
    SK: PLATFORM#steam
    """
    dynamodb = get_dynamodb_client()
    table_name = get_table_name("PLAYER_STATS_TABLE")
    
    now = datetime.utcnow().isoformat() + "Z"
    
    item = {
        "PK": f"USER#{user_id}",
        "SK": f"PLATFORM#{platform}",
        "platform": platform,
        "linked_at": now,
        "updated_at": now,
        **account_data
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
