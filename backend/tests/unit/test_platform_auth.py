"""
Unit tests for platform authentication handlers.
Tests Auth_Riot and Auth_Steam Lambda functions.
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


class TestAuthSteam:
    """Test cases for Auth_Steam Lambda handler"""
    
    def test_missing_firebase_auth_returns_401(self):
        """Test that unauthenticated requests return 401"""
        from lambdas.auth_steam import handler
        
        event = {
            "requestContext": {},  # No authorizer
            "body": json.dumps({
                "steam_id": "76561198012345678"
            })
        }
        
        result = handler(event, {})
        
        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert "Unauthorized" in body.get("error", "")
    
    def test_missing_steam_id_and_vanity_url_returns_400(self):
        """Test that missing both steam_id and vanity_url returns 400"""
        from lambdas.auth_steam import handler
        
        event = {
            "requestContext": {
                "authorizer": {
                    "uid": "user-123",
                    "email": "test@example.com"
                }
            },
            "body": json.dumps({})  # No steam_id or vanity_url
        }
        
        result = handler(event, {})
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "steam_id" in body.get("message", "").lower() or "vanity_url" in body.get("message", "").lower()
    
    def test_invalid_steam_id_format_returns_400(self):
        """Test that invalid Steam ID format returns 400"""
        from lambdas.auth_steam import handler
        
        # Mock SSM to avoid network call
        with patch('lambdas.auth_steam._get_steam_api_key', return_value="fake_key"):
            event = {
                "requestContext": {
                    "authorizer": {
                        "uid": "user-123",
                        "email": "test@example.com"
                    }
                },
                "body": json.dumps({
                    "steam_id": "invalid123"  # Not 17 digits
                })
            }
            
            result = handler(event, {})
            
            assert result["statusCode"] == 400
            body = json.loads(result["body"])
            assert "Steam ID" in body.get("message", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
