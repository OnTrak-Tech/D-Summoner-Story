"""
Simplified unit tests for the auth_handler Lambda function.
Tests core functionality without complex imports.
"""

import json
import pytest
import sys
import os

# Add the Lambda function to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'lambdas'))

from auth_handler import handler


class TestAuthHandlerSimple:
    """Simplified test cases for auth_handler Lambda function"""
    
    def test_valid_auth_request(self):
        """Test successful authentication with valid input"""
        event = {
            "body": json.dumps({
                "summoner_name": "TestSummoner",
                "region": "na1"
            })
        }
        context = {}
        
        response = handler(event, context)
        
        assert response["statusCode"] == 200
        assert "headers" in response
        assert response["headers"]["Content-Type"] == "application/json"
        
        body = json.loads(response["body"])
        assert "session_id" in body
        assert body["status"] == "valid"
        assert len(body["session_id"]) > 0
    
    def test_missing_summoner_name(self):
        """Test authentication with missing summoner name"""
        event = {
            "body": json.dumps({
                "region": "na1"
            })
        }
        context = {}
        
        response = handler(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        # New sanitized error format uses generic message
        assert "error" in body or "message" in body
    
    def test_missing_region(self):
        """Test authentication with missing region"""
        event = {
            "body": json.dumps({
                "summoner_name": "TestSummoner"
            })
        }
        context = {}
        
        response = handler(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        # New sanitized error format uses generic message
        assert "error" in body or "message" in body
    
    def test_empty_summoner_name(self):
        """Test authentication with empty summoner name"""
        event = {
            "body": json.dumps({
                "summoner_name": "   ",
                "region": "na1"
            })
        }
        context = {}
        
        response = handler(event, context)
        
        assert response["statusCode"] == 400
    
    def test_invalid_json_body(self):
        """Test authentication with invalid JSON in body"""
        event = {
            "body": "invalid json"
        }
        context = {}
        
        response = handler(event, context)
        
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        # New sanitized error format - any error indicator is valid
        assert "error" in body or "message" in body
    
    def test_dict_body(self):
        """Test authentication with dict body (not string)"""
        event = {
            "body": {
                "summoner_name": "TestSummoner",
                "region": "na1"
            }
        }
        context = {}
        
        response = handler(event, context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "valid"
    
    def test_no_body(self):
        """Test authentication with no body"""
        event = {}
        context = {}
        
        response = handler(event, context)
        
        assert response["statusCode"] == 400
    
    def test_session_id_uniqueness(self):
        """Test that multiple requests generate unique session IDs"""
        event = {
            "body": json.dumps({
                "summoner_name": "TestSummoner",
                "region": "na1"
            })
        }
        context = {}
        
        response1 = handler(event, context)
        response2 = handler(event, context)
        
        body1 = json.loads(response1["body"])
        body2 = json.loads(response2["body"])
        
        assert body1["session_id"] != body2["session_id"]


if __name__ == "__main__":
    pytest.main([__file__])