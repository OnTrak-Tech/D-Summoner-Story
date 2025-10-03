"""
Simplified integration tests for the League of Legends Year in Review workflow.
Tests basic integration without complex AWS mocking.
"""

import json
import pytest
import sys
import os

# Import Lambda handlers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'lambdas'))

from auth_handler import handler as auth_handler


class TestSimpleIntegration:
    """Simplified integration tests"""
    
    def test_auth_handler_integration(self):
        """Test auth handler integration"""
        
        # Test successful authentication
        auth_event = {
            "body": json.dumps({
                "summoner_name": "TestSummoner",
                "region": "na1"
            })
        }
        
        auth_response = auth_handler(auth_event, {})
        assert auth_response["statusCode"] == 200
        
        auth_body = json.loads(auth_response["body"])
        session_id = auth_body["session_id"]
        
        # Verify session ID can be used for subsequent requests
        assert len(session_id) == 36  # UUID4 format
        assert session_id.count('-') == 4
    
    def test_error_handling_integration(self):
        """Test error handling integration"""
        
        # Test various error scenarios
        error_cases = [
            {"body": json.dumps({"summoner_name": "", "region": "na1"})},
            {"body": json.dumps({"summoner_name": "Test", "region": ""})},
            {"body": "invalid json"},
            {"body": json.dumps({})}
        ]
        
        for event in error_cases:
            response = auth_handler(event, {})
            assert response["statusCode"] in [400, 500]
            
            # Verify error response format
            if response["statusCode"] != 500 or "invalid json" not in str(event):
                body = json.loads(response["body"])
                assert "message" in body
    
    def test_cors_and_headers(self):
        """Test CORS headers and response format"""
        
        auth_event = {
            "body": json.dumps({
                "summoner_name": "TestSummoner",
                "region": "na1"
            })
        }
        
        response = auth_handler(auth_event, {})
        
        # Check response structure
        assert "statusCode" in response
        assert "headers" in response
        assert "body" in response
        
        # Check headers
        headers = response["headers"]
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        
        # Check body is valid JSON
        body = json.loads(response["body"])
        assert isinstance(body, dict)


if __name__ == "__main__":
    pytest.main([__file__])