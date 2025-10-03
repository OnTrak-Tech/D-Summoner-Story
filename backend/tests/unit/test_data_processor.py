"""
Unit tests for the data_processor Lambda function.
Tests statistical analysis, data processing, and DynamoDB operations.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the Lambda function to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'lambdas'))

from data_processor import handler, load_matches_from_s3


class TestDataProcessor:
    """Test cases for data_processor Lambda function"""
    
    @pytest.fixture
    def valid_process_request(self):
        """Valid process request payload"""
        return {
            "body": json.dumps({
                "session_id": "test-session-123",
                "job_id": "test-job-456"
            })
        }
    
    @pytest.fixture
    def api_gateway_status_request(self):
        """API Gateway status check request"""
        return {
            "httpMethod": "GET",
            "pathParameters": {
                "jobId": "test-job-456"
            }
        }
    
    @pytest.fixture
    def mock_aws_clients(self):
        """Mock AWS service clients"""
        with patch('data_processor.get_s3_client') as mock_s3, \
             patch('data_processor.get_dynamodb_client') as mock_ddb, \
             patch('data_processor.get_bucket_name') as mock_bucket, \
             patch('data_processor.get_table_name') as mock_table:
            
            mock_bucket.return_value = "test-bucket"
            mock_table.return_value = "test-table"
            
            yield {
                's3': mock_s3.return_value,
                'dynamodb': mock_ddb.return_value,
                'bucket_name': mock_bucket,
                'table_name': mock_table
            }
    
    @pytest.fixture
    def sample_match_data(self):
        """Sample match data for processing"""
        return {
            "matches": [
                {
                    "match_id": "NA1_1234567890",
                    "game_creation": 1704067200000,
                    "game_duration": 1800,
                    "game_mode": "CLASSIC",
                    "game_type": "MATCHED_GAME",
                    "queue_id": 420,
                    "participants": [
                        {
                            "summoner_id": "test_summoner_id",
                            "champion_id": 1,
                            "champion_name": "Annie",
                            "kills": 8,
                            "deaths": 3,
                            "assists": 12,
                            "win": True,
                            "game_duration": 1800,
                            "item0": 3031,
                            "item1": 3006,
                            "total_damage_dealt": 25000,
                            "gold_earned": 15000,
                            "cs_total": 180
                        }
                    ]
                },
                {
                    "match_id": "NA1_0987654321",
                    "game_creation": 1704153600000,
                    "game_duration": 2100,
                    "game_mode": "CLASSIC",
                    "game_type": "MATCHED_GAME",
                    "queue_id": 420,
                    "participants": [
                        {
                            "summoner_id": "test_summoner_id",
                            "champion_id": 2,
                            "champion_name": "Olaf",
                            "kills": 5,
                            "deaths": 7,
                            "assists": 8,
                            "win": False,
                            "game_duration": 2100,
                            "item0": 3031,
                            "item1": 3006,
                            "total_damage_dealt": 20000,
                            "gold_earned": 12000,
                            "cs_total": 150
                        }
                    ]
                }
            ]
        }
    
    def test_successful_processing(self, valid_process_request, mock_aws_clients, sample_match_data, lambda_context):
        """Test successful data processing workflow"""
        # Setup mock responses
        mock_job_item = {
            "PK": "JOB#test-job-456",
            "status": "pending",
            "session_id": "test-session-123"
        }
        mock_aws_clients['dynamodb'].get_item.return_value = mock_job_item
        mock_aws_clients['s3'].list_objects.return_value = ["raw-matches/summoner/file.json"]
        mock_aws_clients['s3'].get_object.return_value = json.dumps(sample_match_data)
        
        with patch('data_processor.process_match_statistics') as mock_process, \
             patch('data_processor.create_player_stats_item') as mock_create_stats:
            
            mock_stats = MagicMock()
            mock_stats.summoner_name = "TestSummoner"
            mock_stats.total_games = 2
            mock_stats.win_rate = 50.0
            mock_stats.avg_kda = 1.85
            mock_process.return_value = mock_stats
            
            mock_stats_item = MagicMock()
            mock_create_stats.return_value = mock_stats_item
            
            response = handler(valid_process_request, lambda_context)
        
        # Verify response
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "completed"
        assert body["statistics"]["summoner_name"] == "TestSummoner"
        assert body["statistics"]["total_games"] == 2
        
        # Verify processing calls
        mock_process.assert_called_once()
        mock_create_stats.assert_called_once()
        mock_aws_clients['dynamodb'].put_item.assert_called_once()
    
    def test_api_gateway_status_check(self, api_gateway_status_request, mock_aws_clients, lambda_context):
        """Test API Gateway status check endpoint"""
        mock_job_item = {
            "PK": "JOB#test-job-456",
            "status": "processing",
            "progress": 75,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:05:00Z"
        }
        mock_aws_clients['dynamodb'].get_item.return_value = mock_job_item
        
        response = handler(api_gateway_status_request, lambda_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["job_id"] == "test-job-456"
        assert body["status"] == "processing"
        assert body["progress"] == 75
    
    def test_job_not_found(self, api_gateway_status_request, mock_aws_clients, lambda_context):
        """Test handling when job is not found"""
        mock_aws_clients['dynamodb'].get_item.return_value = None
        
        response = handler(api_gateway_status_request, lambda_context)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"] == "JOB_NOT_FOUND"
    
    def test_missing_job_id_in_path(self, mock_aws_clients, lambda_context):
        """Test handling missing job ID in path parameters"""
        request_without_job_id = {
            "httpMethod": "GET",
            "pathParameters": {}
        }
        
        response = handler(request_without_job_id, lambda_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "MISSING_JOB_ID"
    
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
    
    def test_no_match_data_found(self, valid_process_request, mock_aws_clients, lambda_context):
        """Test handling when no match data is found"""
        mock_job_item = {
            "PK": "JOB#test-job-456",
            "status": "pending"
        }
        mock_aws_clients['dynamodb'].get_item.return_value = mock_job_item
        mock_aws_clients['s3'].list_objects.return_value = []  # No files
        
        with patch('data_processor.load_matches_from_s3', return_value=[]):
            response = handler(valid_process_request, lambda_context)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"] == "NO_DATA"
    
    def test_load_matches_from_s3(self, mock_aws_clients, sample_match_data):
        """Test loading and parsing matches from S3"""
        mock_aws_clients['s3'].list_objects.return_value = ["raw-matches/summoner/2024/01/file.json"]
        mock_aws_clients['s3'].get_object.return_value = json.dumps(sample_match_data)
        
        matches = load_matches_from_s3(mock_aws_clients['s3'], "test-bucket", "test_summoner_id")
        
        assert len(matches) == 2
        assert matches[0].match_id == "NA1_1234567890"
        assert matches[0].participants[0].champion_name == "Annie"
        assert matches[1].match_id == "NA1_0987654321"
        assert matches[1].participants[0].champion_name == "Olaf"
    
    def test_load_matches_s3_error(self, mock_aws_clients):
        """Test handling S3 errors when loading matches"""
        mock_aws_clients['s3'].list_objects.side_effect = Exception("S3 Error")
        
        with pytest.raises(Exception, match="S3 Error"):
            load_matches_from_s3(mock_aws_clients['s3'], "test-bucket", "test_summoner_id")
    
    def test_processing_job_updates(self, valid_process_request, mock_aws_clients, sample_match_data, lambda_context):
        """Test that processing job status is updated correctly"""
        mock_job_item = {
            "PK": "JOB#test-job-456",
            "status": "pending"
        }
        mock_aws_clients['dynamodb'].get_item.return_value = mock_job_item
        mock_aws_clients['s3'].list_objects.return_value = ["file.json"]
        mock_aws_clients['s3'].get_object.return_value = json.dumps(sample_match_data)
        
        with patch('data_processor.process_match_statistics') as mock_process, \
             patch('data_processor.create_player_stats_item'):
            
            mock_stats = MagicMock()
            mock_process.return_value = mock_stats
            
            response = handler(valid_process_request, lambda_context)
        
        # Verify job status updates
        update_calls = mock_aws_clients['dynamodb'].update_item.call_args_list
        assert len(update_calls) >= 3  # Initial processing, progress, completion
        
        # Check that status was updated to processing and then completed
        status_updates = [call[1] for call in update_calls if ':status' in str(call)]
        assert any('processing' in str(update) for update in status_updates)
        assert any('completed' in str(update) for update in status_updates)
    
    def test_processing_error_handling(self, valid_process_request, mock_aws_clients, lambda_context):
        """Test error handling during processing"""
        mock_job_item = {
            "PK": "JOB#test-job-456",
            "status": "pending"
        }
        mock_aws_clients['dynamodb'].get_item.return_value = mock_job_item
        
        # Mock processing error
        with patch('data_processor.load_matches_from_s3', side_effect=Exception("Processing Error")):
            response = handler(valid_process_request, lambda_context)
        
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"] == "INTERNAL_ERROR"
        
        # Verify job was marked as failed
        update_calls = mock_aws_clients['dynamodb'].update_item.call_args_list
        failed_update = any('failed' in str(call) for call in update_calls)
        assert failed_update
    
    def test_dict_body_format(self, mock_aws_clients, lambda_context):
        """Test handling of dict body format (not string)"""
        dict_request = {
            "body": {
                "session_id": "test-session-123",
                "job_id": "test-job-456"
            }
        }
        
        mock_job_item = {
            "PK": "JOB#test-job-456",
            "status": "pending"
        }
        mock_aws_clients['dynamodb'].get_item.return_value = mock_job_item
        
        with patch('data_processor.load_matches_from_s3', return_value=[]):
            response = handler(dict_request, lambda_context)
        
        # Should handle dict format gracefully
        assert response["statusCode"] in [200, 404]  # Either success or no data
    
    @patch('data_processor.get_current_timestamp')
    def test_timestamp_tracking(self, mock_timestamp, valid_process_request, mock_aws_clients, sample_match_data, lambda_context):
        """Test that timestamps are properly tracked"""
        mock_timestamp.return_value = 1704067200
        
        mock_job_item = {
            "PK": "JOB#test-job-456",
            "status": "pending"
        }
        mock_aws_clients['dynamodb'].get_item.return_value = mock_job_item
        mock_aws_clients['s3'].list_objects.return_value = ["file.json"]
        mock_aws_clients['s3'].get_object.return_value = json.dumps(sample_match_data)
        
        with patch('data_processor.process_match_statistics') as mock_process, \
             patch('data_processor.create_player_stats_item'):
            
            mock_process.return_value = MagicMock()
            response = handler(valid_process_request, lambda_context)
        
        # Verify timestamp was used in updates
        update_calls = mock_aws_clients['dynamodb'].update_item.call_args_list
        timestamp_used = any('1704067200' in str(call) for call in update_calls)
        assert timestamp_used


if __name__ == "__main__":
    pytest.main([__file__])