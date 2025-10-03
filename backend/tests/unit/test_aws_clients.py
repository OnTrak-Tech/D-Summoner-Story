"""
Unit tests for AWS client wrappers.
Tests DynamoDB, S3, Secrets Manager, and Bedrock client functionality with mocking.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, Mock
from botocore.exceptions import ClientError

# Import AWS clients
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from shared.aws_clients import (
    DynamoDBClient, S3Client, SecretsManagerClient, BedrockClient,
    AWSClientError, get_dynamodb_client, get_s3_client,
    get_secrets_client, get_bedrock_client
)


class TestDynamoDBClient:
    """Test cases for DynamoDB client wrapper"""
    
    @patch('boto3.resource')
    @patch('boto3.client')
    def test_put_item_success(self, mock_client, mock_resource):
        """Test successful item insertion"""
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        
        client = DynamoDBClient()
        result = client.put_item("test-table", {"PK": "test", "data": "value"})
        
        assert result == True
        mock_table.put_item.assert_called_once_with(Item={"PK": "test", "data": "value"})
    
    @patch('boto3.resource')
    @patch('boto3.client')
    def test_put_item_error(self, mock_client, mock_resource):
        """Test item insertion with error"""
        mock_table = MagicMock()
        mock_table.put_item.side_effect = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid item"}},
            "PutItem"
        )
        mock_resource.return_value.Table.return_value = mock_table
        
        client = DynamoDBClient()
        
        with pytest.raises(AWSClientError):
            client.put_item("test-table", {"PK": "test"})
    
    @patch('boto3.resource')
    @patch('boto3.client')
    def test_get_item_success(self, mock_client, mock_resource):
        """Test successful item retrieval"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {"Item": {"PK": "test", "data": "value"}}
        mock_resource.return_value.Table.return_value = mock_table
        
        client = DynamoDBClient()
        result = client.get_item("test-table", {"PK": "test"})
        
        assert result == {"PK": "test", "data": "value"}
    
    @patch('boto3.resource')
    @patch('boto3.client')
    def test_get_item_not_found(self, mock_client, mock_resource):
        """Test item retrieval when item doesn't exist"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # No Item key
        mock_resource.return_value.Table.return_value = mock_table
        
        client = DynamoDBClient()
        result = client.get_item("test-table", {"PK": "test"})
        
        assert result is None


class TestS3Client:
    """Test cases for S3 client wrapper"""
    
    @patch('boto3.client')
    def test_put_object_success(self, mock_boto_client):
        """Test successful object upload"""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        client = S3Client()
        result = client.put_object("test-bucket", "test-key", "test-content")
        
        assert result == True
        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-key",
            Body="test-content",
            ContentType="application/json"
        )
    
    @patch('boto3.client')
    def test_put_object_error(self, mock_boto_client):
        """Test object upload with error"""
        mock_s3 = MagicMock()
        mock_s3.put_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}},
            "PutObject"
        )
        mock_boto_client.return_value = mock_s3
        
        client = S3Client()
        
        with pytest.raises(AWSClientError):
            client.put_object("test-bucket", "test-key", "test-content")
    
    @patch('boto3.client')
    def test_get_object_success(self, mock_boto_client):
        """Test successful object retrieval"""
        mock_s3 = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = b"test-content"
        mock_s3.get_object.return_value = {"Body": mock_body}
        mock_boto_client.return_value = mock_s3
        
        client = S3Client()
        result = client.get_object("test-bucket", "test-key")
        
        assert result == "test-content"
    
    @patch('boto3.client')
    def test_get_object_not_found(self, mock_boto_client):
        """Test object retrieval when object doesn't exist"""
        mock_s3 = MagicMock()
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
            "GetObject"
        )
        mock_boto_client.return_value = mock_s3
        
        client = S3Client()
        result = client.get_object("test-bucket", "test-key")
        
        assert result is None
    
    @patch('boto3.client')
    def test_list_objects_success(self, mock_boto_client):
        """Test successful object listing"""
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "file1.json"},
                {"Key": "file2.json"}
            ]
        }
        mock_boto_client.return_value = mock_s3
        
        client = S3Client()
        result = client.list_objects("test-bucket", "prefix/")
        
        assert result == ["file1.json", "file2.json"]
    
    @patch('boto3.client')
    def test_list_objects_empty(self, mock_boto_client):
        """Test object listing with no objects"""
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.return_value = {}  # No Contents key
        mock_boto_client.return_value = mock_s3
        
        client = S3Client()
        result = client.list_objects("test-bucket", "prefix/")
        
        assert result == []


class TestSecretsManagerClient:
    """Test cases for Secrets Manager client wrapper"""
    
    @patch('boto3.client')
    def test_get_secret_success(self, mock_boto_client):
        """Test successful secret retrieval"""
        mock_secrets = MagicMock()
        mock_secrets.get_secret_value.return_value = {
            "SecretString": json.dumps({"api_key": "test-key"})
        }
        mock_boto_client.return_value = mock_secrets
        
        client = SecretsManagerClient()
        result = client.get_secret("test-secret-arn")
        
        assert result == {"api_key": "test-key"}
    
    @patch('boto3.client')
    def test_get_secret_cached(self, mock_boto_client):
        """Test secret retrieval with caching"""
        mock_secrets = MagicMock()
        mock_secrets.get_secret_value.return_value = {
            "SecretString": json.dumps({"api_key": "test-key"})
        }
        mock_boto_client.return_value = mock_secrets
        
        client = SecretsManagerClient()
        
        # First call
        result1 = client.get_secret("test-secret-arn")
        # Second call (should use cache)
        result2 = client.get_secret("test-secret-arn")
        
        assert result1 == result2
        # Should only call AWS once due to caching
        mock_secrets.get_secret_value.assert_called_once()
    
    @patch('boto3.client')
    def test_get_secret_force_refresh(self, mock_boto_client):
        """Test secret retrieval with forced refresh"""
        mock_secrets = MagicMock()
        mock_secrets.get_secret_value.return_value = {
            "SecretString": json.dumps({"api_key": "test-key"})
        }
        mock_boto_client.return_value = mock_secrets
        
        client = SecretsManagerClient()
        
        # First call
        client.get_secret("test-secret-arn")
        # Second call with force refresh
        client.get_secret("test-secret-arn", force_refresh=True)
        
        # Should call AWS twice due to force refresh
        assert mock_secrets.get_secret_value.call_count == 2
    
    @patch.dict(os.environ, {"RIOT_API_SECRET_ARN": "test-secret-arn"})
    @patch('boto3.client')
    def test_get_riot_api_key_success(self, mock_boto_client):
        """Test Riot API key retrieval"""
        mock_secrets = MagicMock()
        mock_secrets.get_secret_value.return_value = {
            "SecretString": json.dumps({"api_key": "RGAPI-test-key"})
        }
        mock_boto_client.return_value = mock_secrets
        
        client = SecretsManagerClient()
        result = client.get_riot_api_key()
        
        assert result == "RGAPI-test-key"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_riot_api_key_no_env_var(self):
        """Test Riot API key retrieval without environment variable"""
        client = SecretsManagerClient()
        
        with pytest.raises(AWSClientError, match="RIOT_API_SECRET_ARN environment variable not set"):
            client.get_riot_api_key()


class TestBedrockClient:
    """Test cases for Bedrock client wrapper"""
    
    @patch('boto3.client')
    def test_invoke_claude_success(self, mock_boto_client):
        """Test successful Claude model invocation"""
        mock_bedrock = MagicMock()
        mock_response_body = MagicMock()
        mock_response_body.read.return_value = json.dumps({
            "content": [{"text": "Generated response"}]
        }).encode()
        
        mock_bedrock.invoke_model.return_value = {"body": mock_response_body}
        mock_boto_client.return_value = mock_bedrock
        
        client = BedrockClient()
        result = client.invoke_claude("Test prompt")
        
        assert result == "Generated response"
    
    @patch('boto3.client')
    def test_invoke_claude_error(self, mock_boto_client):
        """Test Claude model invocation with error"""
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.side_effect = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid model"}},
            "InvokeModel"
        )
        mock_boto_client.return_value = mock_bedrock
        
        client = BedrockClient()
        
        with pytest.raises(AWSClientError):
            client.invoke_claude("Test prompt")
    
    @patch('boto3.client')
    def test_invoke_titan_embeddings_success(self, mock_boto_client):
        """Test successful Titan embeddings invocation"""
        mock_bedrock = MagicMock()
        mock_response_body = MagicMock()
        mock_response_body.read.return_value = json.dumps({
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
        }).encode()
        
        mock_bedrock.invoke_model.return_value = {"body": mock_response_body}
        mock_boto_client.return_value = mock_bedrock
        
        client = BedrockClient()
        result = client.invoke_titan_embeddings("Test text")
        
        assert result == [0.1, 0.2, 0.3, 0.4, 0.5]


class TestSingletonClients:
    """Test cases for singleton client functions"""
    
    @patch('shared.aws_clients.DynamoDBClient')
    def test_get_dynamodb_client_singleton(self, mock_dynamodb_class):
        """Test that get_dynamodb_client returns singleton"""
        # Reset the global variable
        import shared.aws_clients
        shared.aws_clients._dynamodb_client = None
        
        client1 = get_dynamodb_client()
        client2 = get_dynamodb_client()
        
        assert client1 is client2
        mock_dynamodb_class.assert_called_once()
    
    @patch('shared.aws_clients.S3Client')
    def test_get_s3_client_singleton(self, mock_s3_class):
        """Test that get_s3_client returns singleton"""
        # Reset the global variable
        import shared.aws_clients
        shared.aws_clients._s3_client = None
        
        client1 = get_s3_client()
        client2 = get_s3_client()
        
        assert client1 is client2
        mock_s3_class.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])