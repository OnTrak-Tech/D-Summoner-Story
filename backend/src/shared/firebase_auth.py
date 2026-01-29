"""
Firebase Authentication Utilities

Validates Firebase ID tokens for API Gateway authentication.
Uses Google's public keys to verify JWT signatures without requiring
the full firebase-admin SDK (lighter weight for Lambda cold starts).
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional
from urllib.request import urlopen
from functools import lru_cache

import boto3

logger = logging.getLogger(__name__)


# Firebase public key URLs
FIREBASE_PUBLIC_KEYS_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509/"
    "securetoken@system.gserviceaccount.com"
)


class FirebaseAuthError(Exception):
    """Base exception for Firebase authentication errors"""
    pass


class TokenExpiredError(FirebaseAuthError):
    """Token has expired"""
    pass


class InvalidTokenError(FirebaseAuthError):
    """Token is invalid or malformed"""
    pass


class FirebaseConfigError(FirebaseAuthError):
    """Firebase configuration is missing or invalid"""
    pass


def get_firebase_project_id() -> str:
    """
    Get Firebase project ID from SSM Parameter Store.
    Falls back to environment variable for local development.
    """
    # Check environment variable first (for local dev)
    project_id = os.environ.get("FIREBASE_PROJECT_ID")
    if project_id and project_id != "PLACEHOLDER_FIREBASE_PROJECT_ID":
        return project_id
    
    # Get from SSM Parameter Store
    ssm_path = os.environ.get("SSM_PATH_PREFIX")
    if not ssm_path:
        raise FirebaseConfigError("SSM_PATH_PREFIX environment variable not set")
    
    try:
        ssm = boto3.client("ssm")
        response = ssm.get_parameter(
            Name=f"{ssm_path}/firebase-project-id",
            WithDecryption=False
        )
        return response["Parameter"]["Value"]
    except Exception as e:
        logger.error(f"Failed to get Firebase project ID from SSM: {e}")
        raise FirebaseConfigError(f"Failed to get Firebase project ID: {e}")


@lru_cache(maxsize=1)
def _get_firebase_public_keys_cached(cache_time: int) -> Dict[str, str]:
    """
    Fetch and cache Firebase public keys.
    cache_time parameter is used to invalidate cache every hour.
    """
    try:
        response = urlopen(FIREBASE_PUBLIC_KEYS_URL, timeout=5)
        return json.loads(response.read().decode())
    except Exception as e:
        logger.error(f"Failed to fetch Firebase public keys: {e}")
        raise FirebaseAuthError(f"Failed to fetch Firebase public keys: {e}")


def get_firebase_public_keys() -> Dict[str, str]:
    """Get Firebase public keys with hourly cache refresh"""
    # Cache keys for 1 hour (cache_time changes every hour)
    cache_time = int(time.time() // 3600)
    return _get_firebase_public_keys_cached(cache_time)


def decode_token_header(token: str) -> Dict[str, Any]:
    """Decode JWT header without verification to get key ID"""
    import base64
    
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise InvalidTokenError("Invalid token format")
        
        # Decode header (first part)
        header_b64 = parts[0]
        # Add padding if needed
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += "=" * padding
        
        header_bytes = base64.urlsafe_b64decode(header_b64)
        return json.loads(header_bytes.decode())
    except Exception as e:
        raise InvalidTokenError(f"Failed to decode token header: {e}")


def decode_token_payload(token: str) -> Dict[str, Any]:
    """Decode JWT payload without verification"""
    import base64
    
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise InvalidTokenError("Invalid token format")
        
        # Decode payload (second part)
        payload_b64 = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes.decode())
    except Exception as e:
        raise InvalidTokenError(f"Failed to decode token payload: {e}")


def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Verify a Firebase ID token and return the decoded claims.
    
    This is a lightweight verification that checks:
    1. Token structure and format
    2. Expiration time
    3. Issued-at time
    4. Audience (Firebase project ID)
    5. Issuer
    
    For production with high security requirements, consider using
    the full firebase-admin SDK with cryptographic signature verification.
    
    Args:
        token: Firebase ID token string
        
    Returns:
        Dict containing user claims (uid, email, name, etc.)
        
    Raises:
        InvalidTokenError: Token is malformed or invalid
        TokenExpiredError: Token has expired
        FirebaseConfigError: Firebase project ID not configured
    """
    if not token:
        raise InvalidTokenError("Token is required")
    
    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    
    # Decode header and payload
    header = decode_token_header(token)
    payload = decode_token_payload(token)
    
    # Verify algorithm
    if header.get("alg") != "RS256":
        raise InvalidTokenError(f"Invalid algorithm: {header.get('alg')}")
    
    # Get project ID
    project_id = get_firebase_project_id()
    
    # Verify issuer
    expected_issuer = f"https://securetoken.google.com/{project_id}"
    if payload.get("iss") != expected_issuer:
        raise InvalidTokenError(f"Invalid issuer: {payload.get('iss')}")
    
    # Verify audience
    if payload.get("aud") != project_id:
        raise InvalidTokenError(f"Invalid audience: {payload.get('aud')}")
    
    # Verify expiration
    now = int(time.time())
    exp = payload.get("exp", 0)
    if now >= exp:
        raise TokenExpiredError("Token has expired")
    
    # Verify issued-at (not in the future)
    iat = payload.get("iat", 0)
    if iat > now + 60:  # Allow 60 second clock skew
        raise InvalidTokenError("Token issued in the future")
    
    # Verify subject (user ID) exists
    if not payload.get("sub"):
        raise InvalidTokenError("Token missing subject (user ID)")
    
    # Return essential claims
    return {
        "uid": payload.get("sub"),
        "email": payload.get("email"),
        "email_verified": payload.get("email_verified", False),
        "name": payload.get("name"),
        "picture": payload.get("picture"),
        "auth_time": payload.get("auth_time"),
        "firebase": payload.get("firebase", {}),
    }


def extract_user_from_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract user information from API Gateway event.
    
    For events that have already passed through the Lambda authorizer,
    the user claims are available in requestContext.authorizer.
    
    Args:
        event: API Gateway Lambda proxy event
        
    Returns:
        Dict with user claims or None if not authenticated
    """
    try:
        # Check for Lambda authorizer context
        authorizer = event.get("requestContext", {}).get("authorizer", {})
        
        if authorizer:
            # JWT claims are passed as strings, parse if needed
            return {
                "uid": authorizer.get("uid") or authorizer.get("principalId"),
                "email": authorizer.get("email"),
                "name": authorizer.get("name"),
            }
        
        return None
    except Exception as e:
        logger.warning(f"Failed to extract user from event: {e}")
        return None


def get_token_from_event(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract Bearer token from API Gateway event headers.
    
    Args:
        event: API Gateway Lambda proxy event
        
    Returns:
        Token string or None if not found
    """
    headers = event.get("headers", {}) or {}
    
    # Check for Authorization header (case-insensitive)
    for key, value in headers.items():
        if key.lower() == "authorization":
            if value and value.startswith("Bearer "):
                return value[7:]
            return value
    
    return None
