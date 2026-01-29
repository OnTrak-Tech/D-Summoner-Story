"""
Unit tests for Firebase authentication utilities.
Tests token validation, user extraction, and error handling.
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from shared.firebase_auth import (
    verify_firebase_token,
    extract_user_from_event,
    get_token_from_event,
    decode_token_header,
    decode_token_payload,
    FirebaseAuthError,
    TokenExpiredError,
    InvalidTokenError,
    FirebaseConfigError,
)


class TestFirebaseAuth:
    """Test cases for Firebase authentication utilities"""
    
    def test_get_token_from_event_with_bearer(self):
        """Test extracting Bearer token from headers"""
        event = {
            "headers": {
                "Authorization": "Bearer test-token-123"
            }
        }
        token = get_token_from_event(event)
        assert token == "test-token-123"
    
    def test_get_token_from_event_lowercase_header(self):
        """Test extracting token with lowercase authorization header"""
        event = {
            "headers": {
                "authorization": "Bearer lowercase-token"
            }
        }
        token = get_token_from_event(event)
        assert token == "lowercase-token"
    
    def test_get_token_from_event_no_header(self):
        """Test when no authorization header present"""
        event = {
            "headers": {}
        }
        token = get_token_from_event(event)
        assert token is None
    
    def test_get_token_from_event_empty_event(self):
        """Test with empty event"""
        event = {}
        token = get_token_from_event(event)
        assert token is None
    
    def test_extract_user_from_event_with_authorizer(self):
        """Test extracting user from authorizer context"""
        event = {
            "requestContext": {
                "authorizer": {
                    "uid": "user-123",
                    "email": "test@example.com",
                    "name": "Test User"
                }
            }
        }
        user = extract_user_from_event(event)
        assert user is not None
        assert user["uid"] == "user-123"
        assert user["email"] == "test@example.com"
    
    def test_extract_user_from_event_with_principal_id(self):
        """Test extracting user when uid is in principalId"""
        event = {
            "requestContext": {
                "authorizer": {
                    "principalId": "user-456",
                    "email": "test2@example.com"
                }
            }
        }
        user = extract_user_from_event(event)
        assert user is not None
        assert user["uid"] == "user-456"
    
    def test_extract_user_from_event_no_authorizer(self):
        """Test when no authorizer context present"""
        event = {
            "requestContext": {}
        }
        user = extract_user_from_event(event)
        assert user is None
    
    def test_decode_token_header_valid(self):
        """Test decoding a valid JWT header"""
        # JWT header: {"alg": "RS256", "typ": "JWT"}
        # Base64URL encoded
        token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
        header = decode_token_header(token)
        assert header["alg"] == "RS256"
        assert header["typ"] == "JWT"
    
    def test_decode_token_header_invalid_format(self):
        """Test decoding invalid token format"""
        with pytest.raises(InvalidTokenError):
            decode_token_header("invalid-token")
    
    def test_verify_token_empty(self):
        """Test verifying empty token"""
        with pytest.raises(InvalidTokenError):
            verify_firebase_token("")
    
    def test_verify_token_none(self):
        """Test verifying None token"""
        with pytest.raises(InvalidTokenError):
            verify_firebase_token(None)
    
    def test_verify_token_strips_bearer(self):
        """Test that Bearer prefix is stripped"""
        # This will fail on token validation, but should not fail on Bearer stripping
        with pytest.raises((InvalidTokenError, FirebaseConfigError)):
            verify_firebase_token("Bearer some.token.here")


class TestAuthorizerHandler:
    """Test cases for the authorizer Lambda handler"""
    
    def test_authorizer_no_token_returns_deny(self):
        """Test that missing token returns Deny policy"""
        # Import here to avoid issues with missing dependencies
        from lambdas.authorizer import handler
        
        event = {
            "methodArn": "arn:aws:execute-api:us-east-1:123456:api/stage/GET/test",
            "headers": {}
        }
        
        result = handler(event, {})
        
        assert result["principalId"] == "anonymous"
        assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
