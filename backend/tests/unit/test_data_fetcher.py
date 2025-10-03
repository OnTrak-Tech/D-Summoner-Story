"""
Unit tests for the data_fetcher Lambda function.
Tests Riot API integration, data storage, and error handling.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the Lambda function to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'lambdas'))

from data_fetcher import handler


class TestDataFetcher:
    """Test cases for data_fetcher Lambda function"""
    
    @pytest.fixture
    def valid_fetch_request(self):
        """Valid fetch request payload"""
        return {
            "body": json.dumps({
                "session_id": "test-session-123",
                "summoner_name": "TestSummoner",
                "region": "na1"
            })
        }
    
    @pytest.fixture
    def mock_riot_client(self):
        """Mock Riot API client"""
        with patch('data_fetcher.get_riot_client') as mock:
            client = MagicMock()
            mock.return_value = client
            yield client
    
    @pytest.fixture
    def mock_aws_clients(self):
        """Mock AWS service clients"""
        with patch('data_fetcher.get_s3_client') as mock_s3, \
             patch('data_fetcher.get_dynamodb_client') as mock_ddb, \
             patch('data_fetcher.get_bucket_name') as mock_bucket, \
             patch('data_fetcher.get_table_name') as mock_table:
            
            mock_bucket.return_value = "test-bucket"
            mock_table.return_value = "test-table"
            
            yield {
                's3': mock_s3.return_value,
                'dynamodb': mock_ddb.return_value,
                'bucket_name': mock_bucket,
                'table_name': mock_table
            }
    
    def test_successful_data_fetch(self, valid_fetch_request, mock_riot_client, mock_aws_clients, lambda_context):
        """Test successful data fetching workflow"""
        # Setup mock responses
        mock_summoner = MagicMock()
        mock_summoner.id = "test_summoner_id"
        mock_summoner.name = "TestSummoner"
        mock_summoner.summoner_level = 150
        
        mock_match = MagicMock()
        mock_match.match_id = "NA1_1234567890"
        
        mock_riot_client.get_summoner_by_name.return_value = mock_summoner
        mock_riot_client.get_full_match_history.return_value = [mock_match]
        
        # Execute
        response = handler(valid_fetch_request, lambda_context)
        
        # Verify
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "job_id" in body
        assert body["status"] == "completed"
        assert body["summoner_info"]["name"] == "TestSummoner"
        assert body["match_count"] == 1
        
        # Verify API calls
        mock_riot_client.get_summoner_by_name.assert_called_once_with("TestSummoner", "na1")
        mock_riot_client.get_full_match_history.assert_called_once()
        
        # Verify AWS operations
        mock_aws_clients['s3'].put_object.assert_called_once()
        mock_aws_clients['dynamodb'].put_item.assert_called()
        mock_aws_clients['dynamodb'].update_item.assert_called()
    
    def test_summoner_not_found(self, valid_fetch_request, mock_riot_client, mock_aws_clients, lambda_context):
        """Test handling of summoner not found error"""
        from data_fetcher import SummonerNotFound
        
        mock_riot_client.get_summoner_by_name.side_effect = SummonerNotFound("Summoner not found")
        
        response = handler(valid_fetch_request, lambda_context)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"] == "SUMMONER_NOT_FOUND"
        assert "not found" in body["message"]
    
    def test_riot_api_error(self, valid_fetch_request, mock_riot_client, mock_aws_clients, lambda_context):
        """Test handling of Riot API errors"""
        from data_fetcher import RiotAPIError
        
        mock_riot_client.get_summoner_by_name.side_effect = RiotAPIError("API Error")
        
        response = handler(valid_fetch_request, lambda_context)
        
        assert response["statusCode"] == 503
        body = json.loads(response["body"])
        assert body["error"] == "RIOT_API_ERROR"
    
    def test_invalid_request_format(self, mock_aws_clients, lambda_context):
        """Test handling of invalid request format"""
        invalid_request = {
            "body": json.dumps({
                "invalid_field": "value"
            })
        }
        
        response = handler(invalid_request, lambda_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "INVALID_REQUEST"
    
    def test_invalid_region(self, mock_aws_clients, lambda_context):
        """Test handling of invalid region"""
        invalid_region_request = {
            "body": json.dumps({
                "session_id": "test-session-123",
                "summoner_name": "TestSummoner",
                "region": "invalid_region"
            })
        }
        
        with patch('data_fetcher.validate_region', return_value=False):
            response = handler(invalid_region_request, lambda_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "INVALID_REGION"
    
    def test_no_match_history(self, valid_fetch_request, mock_riot_client, mock_aws_clients, lambda_context):
        """Test handling when no match history is found"""
        mock_summoner = MagicMock()
        mock_summoner.name = "TestSummoner"
        mock_summoner.summoner_level = 150
        
        mock_riot_client.get_summoner_by_name.return_value = mock_summoner
        mock_riot_client.get_full_match_history.return_value = []  # No matches
        
        response = handler(valid_fetch_request, lambda_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "completed"
        assert "No match history found" in body["message"]
    
    def test_dict_body_format(self, mock_riot_client, mock_aws_clients, lambda_context):
        """Test handling of dict body format (not string)"""
        dict_request = {
            "body": {
                "session_id": "test-session-123",
                "summoner_name": "TestSummoner",
                "region": "na1"
            }
        }
        
        mock_summoner = MagicMock()
        mock_summoner.name = "TestSummoner"
        mock_riot_client.get_summoner_by_name.return_value = mock_summoner
        mock_riot_client.get_full_match_history.return_value = []
        
        response = handler(dict_request, lambda_context)
        
        assert response["statusCode"] == 200
    
    def test_aws_service_error(self, valid_fetch_request, mock_riot_client, mock_aws_clients, lambda_context):
        """Test handling of AWS service errors"""
        mock_summoner = MagicMock()
        mock_riot_client.get_summoner_by_name.return_value = mock_summoner
        
        # Mock S3 error
        mock_aws_clients['s3'].put_object.side_effect = Exception("S3 Error")
        
        response = handler(valid_fetch_request, lambda_context)
        
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"] == "INTERNAL_ERROR"
    
    @patch('data_fetcher.create_processing_job')
    def test_job_creation(self, mock_create_job, valid_fetch_request, mock_riot_client, mock_aws_clients, lambda_context):
        """Test processing job creation and tracking"""
        mock_job = MagicMock()
        mock_job.PK = "JOB#test-job-123"
        mock_create_job.return_value = mock_job
        
        mock_summoner = MagicMock()
        mock_riot_client.get_summoner_by_name.return_value = mock_summoner
        mock_riot_client.get_full_match_history.return_value = []
        
        response = handler(valid_fetch_request, lambda_context)
        
        # Verify job creation
        mock_create_job.assert_called_once()
        mock_aws_clients['dynamodb'].put_item.assert_called()
        
        # Verify job updates
        assert mock_aws_clients['dynamodb'].update_item.call_count >= 2  # At least 2 updates
    
    def test_summoner_name_sanitization(self, mock_riot_client, mock_aws_clients, lambda_context):
        """Test summoner name sanitization"""
        request_with_spaces = {
            "body": json.dumps({
                "session_id": "test-session-123",
                "summoner_name": "  Test Summoner  ",
                "region": "na1"
            })
        }
        
        mock_summoner = MagicMock()
        mock_riot_client.get_summoner_by_name.return_value = mock_summoner
        mock_riot_client.get_full_match_history.return_value = []
        
        with patch('data_fetcher.sanitize_summoner_name', return_value="TestSummoner") as mock_sanitize:
            response = handler(request_with_spaces, lambda_context)
        
        mock_sanitize.assert_called_once_with("  Test Summoner  ")
    
    def test_s3_key_generation(self, valid_fetch_request, mock_riot_client, mock_aws_clients, lambda_context):
        """Test S3 key generation for data storage"""
        mock_summoner = MagicMock()
        mock_summoner.id = "test_summoner_id"
        mock_riot_client.get_summoner_by_name.return_value = mock_summoner
        mock_riot_client.get_full_match_history.return_value = [MagicMock()]
        
        with patch('data_fetcher.generate_s3_key', return_value="test/key/path.json") as mock_key_gen:
            response = handler(valid_fetch_request, lambda_context)
        
        mock_key_gen.assert_called_once_with("test_summoner_id", "raw-matches")
        
        # Verify S3 storage used the generated key
        mock_aws_clients['s3'].put_object.assert_called_once()
        call_args = mock_aws_clients['s3'].put_object.call_args
        assert "test/key/path.json" in str(call_args)


if __name__ == "__main__":
    pytest.main([__file__])