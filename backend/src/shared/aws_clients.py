"""
AWS service clients and utilities for Lambda functions.
Provides configured clients for DynamoDB, S3, Secrets Manager, and Bedrock.
"""

import json
import os
from typing import Dict, Any, Optional, List
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import logging

logger = logging.getLogger(__name__)


class AWSClientError(Exception):
    """Custom exception for AWS client errors"""
    pass


class DynamoDBClient:
    """DynamoDB client wrapper with error handling and convenience methods"""
    
    def __init__(self):
        self.client = boto3.client('dynamodb')
        self.resource = boto3.resource('dynamodb')
        
    def put_item(self, table_name: str, item: Dict[str, Any]) -> bool:
        """Put item into DynamoDB table"""
        try:
            table = self.resource.Table(table_name)
            table.put_item(Item=item)
            return True
        except ClientError as e:
            logger.error(f"Failed to put item in {table_name}: {e}")
            raise AWSClientError(f"DynamoDB put_item failed: {e}")
    
    def get_item(self, table_name: str, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get item from DynamoDB table"""
        try:
            table = self.resource.Table(table_name)
            response = table.get_item(Key=key)
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Failed to get item from {table_name}: {e}")
            raise AWSClientError(f"DynamoDB get_item failed: {e}")
    
    def update_item(self, table_name: str, key: Dict[str, Any], 
                   update_expression: str, expression_values: Dict[str, Any],
                   expression_names: Optional[Dict[str, str]] = None) -> bool:
        """Update item in DynamoDB table"""
        try:
            table = self.resource.Table(table_name)
            update_params = {
                "Key": key,
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expression_values
            }
            
            if expression_names:
                update_params["ExpressionAttributeNames"] = expression_names
                
            table.update_item(**update_params)
            return True
        except ClientError as e:
            logger.error(f"Failed to update item in {table_name}: {e}")
            raise AWSClientError(f"DynamoDB update_item failed: {e}")
    
    def query_items(self, table_name: str, key_condition: str, 
                   expression_values: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query items from DynamoDB table"""
        try:
            table = self.resource.Table(table_name)
            response = table.query(
                KeyConditionExpression=key_condition,
                ExpressionAttributeValues=expression_values
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Failed to query {table_name}: {e}")
            raise AWSClientError(f"DynamoDB query failed: {e}")


class S3Client:
    """S3 client wrapper with error handling and convenience methods"""
    
    def __init__(self):
        self.client = boto3.client('s3')
    
    def put_object(self, bucket: str, key: str, body: str, 
                  content_type: str = 'application/json') -> bool:
        """Put object into S3 bucket"""
        try:
            self.client.put_object(
                Bucket=bucket,
                Key=key,
                Body=body,
                ContentType=content_type
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to put object {key} in {bucket}: {e}")
            raise AWSClientError(f"S3 put_object failed: {e}")
    
    def get_object(self, bucket: str, key: str) -> Optional[str]:
        """Get object from S3 bucket"""
        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read().decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            logger.error(f"Failed to get object {key} from {bucket}: {e}")
            raise AWSClientError(f"S3 get_object failed: {e}")
    
    def list_objects(self, bucket: str, prefix: str = '') -> List[str]:
        """List objects in S3 bucket with optional prefix"""
        try:
            response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            logger.error(f"Failed to list objects in {bucket}: {e}")
            raise AWSClientError(f"S3 list_objects failed: {e}")
    
    def delete_object(self, bucket: str, key: str) -> bool:
        """Delete object from S3 bucket"""
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            logger.error(f"Failed to delete object {key} from {bucket}: {e}")
            raise AWSClientError(f"S3 delete_object failed: {e}")


class SecretsManagerClient:
    """Secrets Manager client wrapper with caching"""
    
    def __init__(self):
        self.client = boto3.client('secretsmanager')
        self._cache = {}
    
    def get_secret(self, secret_arn: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get secret value with caching"""
        if not force_refresh and secret_arn in self._cache:
            return self._cache[secret_arn]
        
        try:
            response = self.client.get_secret_value(SecretId=secret_arn)
            secret_value = json.loads(response['SecretString'])
            self._cache[secret_arn] = secret_value
            return secret_value
        except ClientError as e:
            logger.error(f"Failed to get secret {secret_arn}: {e}")
            raise AWSClientError(f"Secrets Manager get_secret failed: {e}")
    
    def get_riot_api_key(self) -> str:
        """Get Riot Games API key from secrets"""
        secret_arn = os.environ.get('RIOT_API_SECRET_ARN')
        if not secret_arn:
            raise AWSClientError("RIOT_API_SECRET_ARN environment variable not set")
        
        secret = self.get_secret(secret_arn)
        api_key = secret.get('api_key')
        if not api_key:
            raise AWSClientError("api_key not found in secret")
        
        return api_key


class BedrockClient:
    """Amazon Bedrock client wrapper for AI model invocation"""
    
    def __init__(self):
        self.client = boto3.client('bedrock-runtime')
    
    def invoke_claude(self, prompt: str, max_tokens: int = 1000, 
                     temperature: float = 0.7) -> str:
        """Invoke Claude model for text generation"""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.client.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except ClientError as e:
            logger.error(f"Failed to invoke Claude model: {e}")
            raise AWSClientError(f"Bedrock invoke_model failed: {e}")
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse Bedrock response: {e}")
            raise AWSClientError(f"Bedrock response parsing failed: {e}")
    
    def invoke_titan_embeddings(self, text: str) -> List[float]:
        """Invoke Titan model for text embeddings"""
        try:
            body = {
                "inputText": text
            }
            
            response = self.client.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['embedding']
            
        except ClientError as e:
            logger.error(f"Failed to invoke Titan embeddings: {e}")
            raise AWSClientError(f"Bedrock embeddings failed: {e}")


# Singleton instances for Lambda reuse
_dynamodb_client = None
_s3_client = None
_secrets_client = None
_bedrock_client = None


def get_dynamodb_client() -> DynamoDBClient:
    """Get singleton DynamoDB client"""
    global _dynamodb_client
    if _dynamodb_client is None:
        _dynamodb_client = DynamoDBClient()
    return _dynamodb_client


def get_s3_client() -> S3Client:
    """Get singleton S3 client"""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client


def get_secrets_client() -> SecretsManagerClient:
    """Get singleton Secrets Manager client"""
    global _secrets_client
    if _secrets_client is None:
        _secrets_client = SecretsManagerClient()
    return _secrets_client


def get_bedrock_client() -> BedrockClient:
    """Get singleton Bedrock client"""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client


# Environment variable helpers
def get_table_name(table_type: str) -> str:
    """Get DynamoDB table name from environment"""
    env_var = f"{table_type.upper()}_TABLE"
    table_name = os.environ.get(env_var)
    if not table_name:
        raise AWSClientError(f"{env_var} environment variable not set")
    return table_name


def get_bucket_name(bucket_type: str) -> str:
    """Get S3 bucket name from environment"""
    env_var = f"{bucket_type.upper()}_BUCKET"
    bucket_name = os.environ.get(env_var)
    if not bucket_name:
        raise AWSClientError(f"{env_var} environment variable not set")
    return bucket_name