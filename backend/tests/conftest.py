"""
Simplified pytest configuration and shared fixtures for backend tests.
"""

import pytest
import os
from unittest.mock import MagicMock


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
    
    # Set environment variables for the test
    for key, value in env_vars.items():
        os.environ[key] = value
    
    yield env_vars
    
    # Clean up after test
    for key in env_vars.keys():
        os.environ.pop(key, None)