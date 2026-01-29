"""
Basic integration tests for the Lambda workflow.
Tests the core functionality without requiring real AWS services.
"""

import json
import pytest
import sys
import os

# Add the Lambda functions to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'lambdas'))

from auth_handler import handler as auth_handler


class TestBasicWorkflow:
    """Test basic workflow integration"""
    
    def test_auth_to_processing_workflow(self):
        """Test the basic workflow from auth to processing"""
        # Step 1: Authentication
        auth_event = {
            "body": json.dumps({
                "summoner_name": "TestSummoner",
                "region": "na1"
            })
        }
        
        auth_response = auth_handler(auth_event, {})
        
        # Verify auth response
        assert auth_response["statusCode"] == 200
        auth_body = json.loads(auth_response["body"])
        assert "session_id" in auth_body
        assert auth_body["status"] == "valid"
        
        session_id = auth_body["session_id"]
        
        # Verify session ID format (UUID4)
        assert len(session_id) == 36  # UUID4 length with hyphens
        assert session_id.count('-') == 4  # UUID4 has 4 hyphens
    
    def test_error_handling_workflow(self):
        """Test error handling throughout the workflow"""
        # Test invalid auth request
        invalid_auth_event = {
            "body": json.dumps({
                "summoner_name": "",
                "region": "na1"
            })
        }
        
        auth_response = auth_handler(invalid_auth_event, {})
        
        assert auth_response["statusCode"] == 400
        auth_body = json.loads(auth_response["body"])
        # Case-insensitive check for error message
        assert "required" in auth_body.get("message", "").lower() or "error" in auth_body
    
    def test_multiple_auth_requests(self):
        """Test multiple authentication requests generate unique sessions"""
        auth_event = {
            "body": json.dumps({
                "summoner_name": "TestSummoner",
                "region": "na1"
            })
        }
        
        # Generate multiple sessions
        sessions = []
        for _ in range(5):
            response = auth_handler(auth_event, {})
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            sessions.append(body["session_id"])
        
        # Verify all sessions are unique
        assert len(set(sessions)) == 5
    
    def test_different_regions(self):
        """Test authentication with different regions"""
        regions = ["na1", "euw1", "kr", "br1"]
        
        for region in regions:
            auth_event = {
                "body": json.dumps({
                    "summoner_name": "TestSummoner",
                    "region": region
                })
            }
            
            response = auth_handler(auth_event, {})
            assert response["statusCode"] == 200
            
            body = json.loads(response["body"])
            assert body["status"] == "valid"
    
    def test_summoner_name_variations(self):
        """Test authentication with various summoner name formats"""
        summoner_names = [
            "TestSummoner",
            "Test Summoner",
            "TestSummoner123",
            "Test_Summoner",
            "Test-Summoner"
        ]
        
        for summoner_name in summoner_names:
            auth_event = {
                "body": json.dumps({
                    "summoner_name": summoner_name,
                    "region": "na1"
                })
            }
            
            response = auth_handler(auth_event, {})
            assert response["statusCode"] == 200
            
            body = json.loads(response["body"])
            assert body["status"] == "valid"


if __name__ == "__main__":
    pytest.main([__file__])