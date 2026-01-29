"""
Lambda Authorizer for API Gateway

Validates Firebase ID tokens and returns IAM policy for API Gateway.
This is a REQUEST-type authorizer that validates the Authorization header.
"""

import os
import sys
import json
import logging
from typing import Any, Dict

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.firebase_auth import (
    verify_firebase_token,
    get_token_from_event,
    FirebaseAuthError,
    TokenExpiredError,
    InvalidTokenError,
)


# Setup logging
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def generate_policy(
    principal_id: str,
    effect: str,
    resource: str,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate IAM policy document for API Gateway authorizer.
    
    Args:
        principal_id: User identifier (Firebase UID)
        effect: "Allow" or "Deny"
        resource: API Gateway method ARN
        context: Additional context to pass to backend Lambda
        
    Returns:
        IAM policy document
    """
    policy = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource
                }
            ]
        }
    }
    
    if context:
        # Context values must be strings, numbers, or booleans
        policy["context"] = {
            k: str(v) if not isinstance(v, (str, int, float, bool)) else v
            for k, v in context.items()
            if v is not None
        }
    
    return policy


def generate_allow_policy(
    user_claims: Dict[str, Any],
    resource: str
) -> Dict[str, Any]:
    """Generate Allow policy with user context"""
    return generate_policy(
        principal_id=user_claims.get("uid", "unknown"),
        effect="Allow",
        resource=resource,
        context={
            "uid": user_claims.get("uid"),
            "email": user_claims.get("email"),
            "name": user_claims.get("name"),
            "email_verified": user_claims.get("email_verified", False),
        }
    )


def generate_deny_policy(principal_id: str, resource: str) -> Dict[str, Any]:
    """Generate Deny policy"""
    return generate_policy(
        principal_id=principal_id,
        effect="Deny",
        resource=resource
    )


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda Authorizer handler.
    
    Event structure for REQUEST authorizer:
    {
        "type": "REQUEST",
        "methodArn": "arn:aws:execute-api:...",
        "headers": {
            "Authorization": "Bearer <token>"
        },
        ...
    }
    
    Returns:
        IAM policy document allowing or denying access
    """
    logger.info("Authorizer invoked")
    logger.debug(f"Event: {json.dumps(event, default=str)}")
    
    # Get the method ARN for the policy
    method_arn = event.get("methodArn", "*")
    
    # For wildcard resource access (all methods in the API)
    # This allows the authorizer result to be cached across routes
    arn_parts = method_arn.split("/")
    if len(arn_parts) >= 2:
        # Replace specific method with wildcard
        # arn:aws:execute-api:region:account:api-id/stage/method/path
        # becomes: arn:aws:execute-api:region:account:api-id/stage/*
        wildcard_arn = "/".join(arn_parts[:2]) + "/*"
    else:
        wildcard_arn = method_arn
    
    try:
        # Extract token from headers
        token = get_token_from_event(event)
        
        if not token:
            logger.warning("No authorization token provided")
            # Return Deny policy
            return generate_deny_policy("anonymous", wildcard_arn)
        
        # Verify the Firebase token
        user_claims = verify_firebase_token(token)
        
        logger.info(f"Token validated for user: {user_claims.get('uid')}")
        
        # Return Allow policy with user context
        return generate_allow_policy(user_claims, wildcard_arn)
        
    except TokenExpiredError as e:
        logger.warning(f"Token expired: {e}")
        return generate_deny_policy("expired-token", wildcard_arn)
        
    except InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return generate_deny_policy("invalid-token", wildcard_arn)
        
    except FirebaseAuthError as e:
        logger.error(f"Firebase auth error: {e}")
        return generate_deny_policy("auth-error", wildcard_arn)
        
    except Exception as e:
        logger.error(f"Unexpected error in authorizer: {e}", exc_info=True)
        # Return Deny on any unexpected error
        return generate_deny_policy("error", wildcard_arn)
