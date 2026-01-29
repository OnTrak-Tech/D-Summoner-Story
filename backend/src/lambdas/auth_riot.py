"""
Auth Riot Lambda Function
Validates Riot Games accounts and links them to authenticated Firebase users.

Flow:
1. User is authenticated via Firebase (authorizer passes uid)
2. User provides Riot summoner_name + region
3. Lambda validates the account exists via Riot API
4. Lambda links the account to user in DynamoDB
"""

import json
import os
import sys
import logging
from typing import Any, Dict, Optional
from datetime import datetime

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils import format_lambda_response, setup_logging, validate_region, sanitize_summoner_name
from shared.errors import AppError, ErrorCode, handle_exception
from shared.firebase_auth import extract_user_from_event
from shared.riot_client import get_riot_client, RiotAPIError, SummonerNotFound
from shared.aws_clients import get_dynamodb_client, get_table_name

# Setup logging
setup_logging(os.environ.get('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for linking Riot accounts to Firebase users.
    
    Request body:
    {
        "summoner_name": "PlayerName",
        "region": "na1"  // or euw1, kr, etc.
    }
    
    Response:
    {
        "linked": true,
        "platform": "riot",
        "account": {
            "summoner_name": "PlayerName",
            "summoner_id": "...",
            "puuid": "...",
            "region": "na1",
            "profile_icon_id": 123,
            "summoner_level": 100
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
        logger.info(f"Linking Riot account for user: {user_id}")
        
        # Parse request body
        body = event.get("body", "{}")
        if isinstance(body, str):
            body = json.loads(body)
        
        summoner_name = (body.get("summoner_name") or "").strip()
        region = (body.get("region") or "").strip().lower()
        
        # Validate inputs
        if not summoner_name:
            return format_lambda_response(400, {
                "error": "Missing required field",
                "message": "summoner_name is required"
            })
        
        if not region:
            return format_lambda_response(400, {
                "error": "Missing required field",
                "message": "region is required"
            })
        
        # Validate region
        if not validate_region(region):
            return format_lambda_response(400, {
                "error": "Invalid region",
                "message": f"Region '{region}' is not supported"
            })
        
        # Sanitize summoner name
        sanitized_name = sanitize_summoner_name(summoner_name)
        
        # Validate with Riot API
        try:
            riot_client = get_riot_client()
            summoner = riot_client.get_summoner_by_name(region, sanitized_name)
        except SummonerNotFound:
            return format_lambda_response(404, {
                "error": "Summoner not found",
                "message": f"Could not find summoner '{summoner_name}' in region '{region}'"
            })
        except RiotAPIError as e:
            logger.error(f"Riot API error: {e}")
            return format_lambda_response(502, {
                "error": "Platform error",
                "message": "Failed to validate account with Riot Games API"
            })
        
        # Link account in DynamoDB
        account_data = {
            "summoner_name": summoner.name,
            "summoner_id": summoner.id,
            "puuid": summoner.puuid,
            "account_id": getattr(summoner, 'account_id', None),
            "region": region,
            "profile_icon_id": summoner.profile_icon_id,
            "summoner_level": summoner.summoner_level
        }
        
        link_result = _link_platform_account(
            user_id=user_id,
            platform="riot",
            account_data=account_data
        )
        
        return format_lambda_response(200, {
            "linked": True,
            "platform": "riot",
            "account": account_data,
            "message": "Riot account successfully linked"
        })
        
    except Exception as e:
        error = handle_exception(e)
        return format_lambda_response(error.status_code, error.to_response())


def _link_platform_account(
    user_id: str,
    platform: str,
    account_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Link a gaming platform account to a Firebase user in DynamoDB.
    
    DynamoDB Item:
    PK: USER#{user_id}
    SK: PLATFORM#riot
    
    Args:
        user_id: Firebase user ID
        platform: Platform name (riot, steam, xbox)
        account_data: Platform-specific account data
        
    Returns:
        Updated item data
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
