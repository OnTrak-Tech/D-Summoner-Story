"""
Unit tests for platform authentication handlers.
Tests Auth_Riot and Auth_Fortnite Lambda functions.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestAuthRiot:
    """Test cases for Auth_Riot Lambda handler"""
    
    def test_missing_firebase_auth_returns_401(self):
        """Test that unauthenticated requests return 401"""
        from lambdas.auth_riot import handler
        
        event = {
            "requestContext": {},  # No authorizer
            "body": json.dumps({
                "summoner_name": "TestPlayer",
                "region": "na1"
            })
        }
        
        result = handler(event, {})
        
        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert "Unauthorized" in body.get("error", "")
    
    def test_missing_summoner_name_returns_400(self):
        """Test that missing summoner_name returns 400"""
        from lambdas.auth_riot import handler
        
        event = {
            "requestContext": {
                "authorizer": {
                    "uid": "user-123",
                    "email": "test@example.com"
                }
            },
            "body": json.dumps({
                "region": "na1"
                # Missing summoner_name
            })
        }
        
        result = handler(event, {})
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "summoner_name" in body.get("message", "").lower()
    
    def test_missing_region_returns_400(self):
        """Test that missing region returns 400"""
        from lambdas.auth_riot import handler
        
        event = {
            "requestContext": {
                "authorizer": {
                    "uid": "user-123",
                    "email": "test@example.com"
                }
            },
            "body": json.dumps({
                "summoner_name": "TestPlayer"
                # Missing region
            })
        }
        
        result = handler(event, {})
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "region" in body.get("message", "").lower()
    
    def test_invalid_region_returns_400(self):
        """Test that invalid region returns 400"""
        from lambdas.auth_riot import handler
        
        event = {
            "requestContext": {
                "authorizer": {
                    "uid": "user-123",
                    "email": "test@example.com"
                }
            },
            "body": json.dumps({
                "summoner_name": "TestPlayer",
                "region": "invalid_region"
            })
        }
        
        result = handler(event, {})
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "region" in body.get("message", "").lower()


class TestAuthFortnite:
    """Test cases for Auth_Fortnite Lambda handler"""
    
    def test_missing_firebase_auth_returns_401(self):
        """Test that unauthenticated requests return 401"""
        from lambdas.auth_fortnite import handler
        
        event = {
            "requestContext": {},  # No authorizer
            "body": json.dumps({
                "epic_username": "TestPlayer"
            })
        }
        
        result = handler(event, {})
        
        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert "Unauthorized" in body.get("error", "")
    
    def test_missing_epic_username_returns_400(self):
        """Test that missing epic_username returns 400"""
        from lambdas.auth_fortnite import handler
        
        event = {
            "requestContext": {
                "authorizer": {
                    "uid": "user-123",
                    "email": "test@example.com"
                }
            },
            "body": json.dumps({})  # No epic_username
        }
        
        result = handler(event, {})
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "epic_username" in body.get("message", "").lower()
    
    def test_invalid_account_type_returns_400(self):
        """Test that invalid account_type returns 400"""
        from lambdas.auth_fortnite import handler
        
        event = {
            "requestContext": {
                "authorizer": {
                    "uid": "user-123",
                    "email": "test@example.com"
                }
            },
            "body": json.dumps({
                "epic_username": "TestPlayer",
                "account_type": "invalid_type"
            })
        }
        
        result = handler(event, {})
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "account_type" in body.get("message", "").lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
