"""
Pytest configuration and shared fixtures for backend tests.
"""

import pytest
import os
import json
from unittest.mock import MagicMock, patch
from moto import mock_dynamodb, mock_s3, mock_secretsmanager
import boto3


@pytest.fixture
def mock_aws_credentials():
    """Mock AWS credentials for testing"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for Lambda functions"""
    env_vars = {
        'LOG_LEVEL': 'INFO',
        'PLAYER_STATS_TABLE': 'test-player-stats',
        'PROCESSING_JOBS_TABLE': 'test-processing-jobs',
        'RAW_DATA_BUCKET': 'test-raw-data-bucket',
        'PROCESSED_INSIGHTS_BUCKET': 'test-processed-insights-bucket',
        'RIOT_API_SECRET_ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-riot-api-key'
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_dynamodb_tables(mock_aws_credentials):
    """Create mock DynamoDB tables for testing"""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create player stats table
        player_stats_table = dynamodb.create_table(
            TableName='test-player-stats',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create processing jobs table
        processing_jobs_table = dynamodb.create_table(
            TableName='test-processing-jobs',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield {
            'player_stats': player_stats_table,
            'processing_jobs': processing_jobs_table
        }


@pytest.fixture
def mock_s3_buckets(mock_aws_credentials):
    """Create mock S3 buckets for testing"""
    with mock_s3():
        s3 = boto3.client('s3', region_name='us-east-1')
        
        # Create buckets
        s3.create_bucket(Bucket='test-raw-data-bucket')
        s3.create_bucket(Bucket='test-processed-insights-bucket')
        
        yield {
            'raw_data': 'test-raw-data-bucket',
            'processed_insights': 'test-processed-insights-bucket'
        }


@pytest.fixture
def mock_secrets_manager(mock_aws_credentials):
    """Create mock Secrets Manager for testing"""
    with mock_secretsmanager():
        secrets = boto3.client('secretsmanager', region_name='us-east-1')
        
        # Create Riot API key secret
        secret_arn = secrets.create_secret(
            Name='test-riot-api-key',
            SecretString=json.dumps({'api_key': 'RGAPI-test-key-12345'})
        )['ARN']
        
        yield {
            'riot_api_secret_arn': secret_arn,
            'riot_api_key': 'RGAPI-test-key-12345'
        }


@pytest.fixture
def sample_riot_match_data():
    """Sample Riot API match data for testing"""
    return {
        "metadata": {
            "matchId": "NA1_1234567890"
        },
        "info": {
            "gameCreation": 1704067200000,
            "gameDuration": 1800,
            "gameMode": "CLASSIC",
            "gameType": "MATCHED_GAME",
            "queueId": 420,
            "participants": [
                {
                    "summonerId": "test_summoner_id",
                    "championId": 1,
                    "kills": 8,
                    "deaths": 3,
                    "assists": 12,
                    "win": True,
                    "item0": 3031,
                    "item1": 3006,
                    "item2": 3094,
                    "item3": 3033,
                    "item4": 3036,
                    "item5": 3139,
                    "item6": 3340,
                    "totalDamageDealtToChampions": 25000,
                    "goldEarned": 15000,
                    "totalMinionsKilled": 180,
                    "neutralMinionsKilled": 25
                }
            ]
        }
    }


@pytest.fixture
def sample_summoner_data():
    """Sample Riot API summoner data for testing"""
    return {
        "id": "test_summoner_id",
        "accountId": "test_account_id",
        "puuid": "test_puuid",
        "name": "TestSummoner",
        "profileIconId": 1,
        "revisionDate": 1704067200000,
        "summonerLevel": 150
    }


@pytest.fixture
def mock_bedrock_response():
    """Mock Bedrock API response for testing"""
    return {
        "body": MagicMock(read=lambda: json.dumps({
            "content": [{
                "text": "This is a test AI-generated narrative about your League of Legends year in review!"
            }]
        }).encode())
    }


@pytest.fixture
def lambda_context():
    """Mock Lambda context object"""
    context = MagicMock()
    context.function_name = 'test-function'
    context.function_version = '$LATEST'
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
    context.memory_limit_in_mb = 256
    context.get_remaining_time_in_millis = lambda: 30000
    return context


@pytest.fixture
def api_gateway_event():
    """Mock API Gateway event"""
    return {
        "httpMethod": "POST",
        "path": "/api/v1/test",
        "pathParameters": None,
        "queryStringParameters": None,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": None,
        "isBase64Encoded": False,
        "requestContext": {
            "requestId": "test-request-id",
            "stage": "test",
            "httpMethod": "POST",
            "path": "/api/v1/test"
        }
    }