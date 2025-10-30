# Amazon Bedrock Setup Guide

This guide explains how to set up Amazon Bedrock for the League of Legends Year in Review application.

## Overview

Amazon Bedrock provides access to foundation models from leading AI companies. Our application uses Bedrock to generate personalized gaming narratives similar to "Spotify Wrapped" but for League of Legends.

## Model Requirements

Our application uses these Bedrock models:

### Primary Model
- **Claude 3 Sonnet** (`anthropic.claude-3-sonnet-20240229-v1:0`)
  - Purpose: Generate engaging, personalized gaming narratives
  - Provider: Anthropic
  - Use Case: Text generation with gaming terminology and statistics

### Alternative Models (Optional)
- **Claude 3 Haiku** (`anthropic.claude-3-haiku-20240307-v1:0`)
  - Purpose: Faster, cost-effective text generation
  - Use Case: Quick insights or fallback option

- **Amazon Titan Text** (`amazon.titan-text-express-v1`)
  - Purpose: AWS-native text generation
  - Use Case: Backup option if Anthropic models unavailable

## Setup Steps

### 1. Check Regional Availability

Bedrock is not available in all AWS regions. Verify your region supports the required models:

```bash
# Check available models in your region
aws bedrock list-foundation-models --region us-east-1

# Check specific model availability
aws bedrock get-foundation-model \
  --model-identifier anthropic.claude-3-sonnet-20240229-v1:0 \
  --region us-east-1
```

**Recommended Regions:**
- `us-east-1` (N. Virginia) - Full model availability
- `us-west-2` (Oregon) - Most models available
- `eu-west-1` (Ireland) - Limited model selection

### 2. Request Model Access

Most Bedrock models require explicit access requests:

#### Via AWS Console:
1. Navigate to [Amazon Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Go to **Model access** in the left sidebar
3. Click **Request model access**
4. Select the required models:
   - ✅ **Anthropic Claude 3 Sonnet**
   - ✅ **Anthropic Claude 3 Haiku** (optional)
   - ✅ **Amazon Titan Text Express** (optional)
5. Fill out the use case form:
   - **Use Case**: Gaming analytics and personalized content generation
   - **Description**: Generate year-in-review narratives for League of Legends players
6. Submit the request

#### Via AWS CLI:
```bash
# Request access to Claude 3 Sonnet
aws bedrock put-model-invocation-logging-configuration \
  --logging-config '{
    "cloudWatchConfig": {
      "logGroupName": "/aws/bedrock/modelinvocations",
      "roleArn": "arn:aws:iam::ACCOUNT:role/service-role/AmazonBedrockExecutionRoleForCloudWatchLogs"
    }
  }' \
  --region us-east-1
```

### 3. Verify Access

After approval (usually within 24 hours), verify model access:

```bash
# Test model access
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body '{"anthropic_version": "bedrock-2023-05-31", "max_tokens": 100, "messages": [{"role": "user", "content": "Hello, world!"}]}' \
  --cli-binary-format raw-in-base64-out \
  --region us-east-1 \
  /tmp/response.json

# Check response
cat /tmp/response.json
```

### 4. Configure Application

Update your Lambda environment variables if needed:

```bash
# Get the deployed Lambda function name
LAMBDA_NAME=$(terraform output -raw lambda_functions | jq -r '.insight_generator' | cut -d':' -f6)

# Update environment variables
aws lambda update-function-configuration \
  --function-name "$LAMBDA_NAME" \
  --environment Variables='{
    "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
    "BEDROCK_REGION": "us-east-1",
    "MAX_TOKENS": "1500",
    "TEMPERATURE": "0.7"
  }'
```

## Usage in Lambda Functions

### Basic Implementation

```python
import boto3
import json
import os

def generate_narrative(player_stats):
    """Generate personalized gaming narrative using Bedrock."""
    
    # Initialize Bedrock client
    bedrock = boto3.client(
        'bedrock-runtime',
        region_name=os.environ.get('BEDROCK_REGION', 'us-east-1')
    )
    
    # Craft the prompt
    prompt = create_gaming_prompt(player_stats)
    
    # Prepare request body
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": int(os.environ.get('MAX_TOKENS', 1500)),
        "temperature": float(os.environ.get('TEMPERATURE', 0.7)),
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        # Invoke the model
        response = bedrock.invoke_model(
            modelId=os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
            body=json.dumps(body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        print(f"Bedrock invocation failed: {str(e)}")
        return generate_fallback_narrative(player_stats)

def create_gaming_prompt(stats):
    """Create an engaging prompt for gaming narrative generation."""
    
    return f"""
    Create an engaging, personalized League of Legends year-in-review narrative in the style of "Spotify Wrapped" for a player with these statistics:

    📊 PLAYER STATISTICS:
    • Total Games Played: {stats.get('total_games', 0)}
    • Overall Win Rate: {stats.get('win_rate', 0):.1f}%
    • Average KDA: {stats.get('avg_kda', 0):.2f}
    • Most Played Champion: {stats.get('top_champion', 'Unknown')} ({stats.get('top_champion_games', 0)} games)
    • Best Win Rate Champion: {stats.get('best_wr_champion', 'Unknown')} ({stats.get('best_wr_percentage', 0):.1f}% win rate)
    • Favorite Role: {stats.get('primary_role', 'Unknown')}
    • Peak Performance Month: {stats.get('best_month', 'Unknown')}
    • Improvement Trend: {stats.get('trend', 'Stable')}

    🎯 REQUIREMENTS:
    1. Write in an enthusiastic, celebratory tone like Spotify Wrapped
    2. Use League of Legends terminology and references
    3. Include specific statistics naturally in the narrative
    4. Highlight achievements and improvements
    5. Make it personal and engaging
    6. Keep it between 200-300 words
    7. Include emojis and gaming references
    8. End with an encouraging message for the next season

    🎮 STYLE EXAMPLES:
    - "You absolutely dominated the Rift this year!"
    - "Your {champion} gameplay was *chef's kiss* perfection"
    - "You climbed harder than a Yasuo main in ranked"
    - "That {month} performance? Absolutely legendary"

    Generate the narrative now:
    """

def generate_fallback_narrative(stats):
    """Generate a simple fallback narrative if Bedrock fails."""
    
    return f"""
    🎮 Your League of Legends Year in Review! 🎮
    
    What a year on the Rift! You played {stats.get('total_games', 0)} games with a {stats.get('win_rate', 0):.1f}% win rate. 
    
    Your go-to champion was {stats.get('top_champion', 'your favorite pick')}, and you really showed your skills with an average KDA of {stats.get('avg_kda', 0):.2f}.
    
    Keep climbing, Summoner! Next season is going to be even better! 🚀
    """
```

### Advanced Features

```python
def generate_champion_insights(champion_stats):
    """Generate specific insights about champion performance."""
    
    prompt = f"""
    Analyze this League of Legends champion performance data and provide insights:
    
    Champion: {champion_stats['name']}
    Games Played: {champion_stats['games']}
    Win Rate: {champion_stats['win_rate']}%
    Average KDA: {champion_stats['kda']}
    
    Provide 3 key insights about this champion performance in a fun, engaging way.
    """
    
    # Use same Bedrock invocation pattern
    return invoke_bedrock_model(prompt)

def generate_monthly_summary(monthly_data):
    """Generate month-by-month performance summary."""
    
    best_month = max(monthly_data, key=lambda x: x['win_rate'])
    
    prompt = f"""
    Create a month-by-month League of Legends performance summary:
    
    Best Month: {best_month['month']} ({best_month['win_rate']}% win rate)
    Total Months Active: {len(monthly_data)}
    
    Monthly Data: {json.dumps(monthly_data, indent=2)}
    
    Write a narrative highlighting the player's journey through the year, 
    noting improvements, challenges, and standout months.
    """
    
    return invoke_bedrock_model(prompt)
```

## Cost Optimization

### Token Management
```python
# Optimize token usage
MAX_TOKENS_BY_USE_CASE = {
    'full_narrative': 1500,
    'champion_insight': 500,
    'monthly_summary': 800,
    'quick_stat': 200
}

def optimize_prompt_length(prompt, max_length=2000):
    """Truncate prompts to manage token costs."""
    if len(prompt) > max_length:
        return prompt[:max_length] + "..."
    return prompt
```

### Caching Strategy
```python
import hashlib

def get_narrative_cache_key(stats):
    """Generate cache key for narrative to avoid duplicate API calls."""
    stats_str = json.dumps(stats, sort_keys=True)
    return hashlib.md5(stats_str.encode()).hexdigest()

def cached_narrative_generation(stats, s3_client, bucket):
    """Check S3 cache before calling Bedrock."""
    cache_key = get_narrative_cache_key(stats)
    
    try:
        # Try to get from cache
        response = s3_client.get_object(
            Bucket=bucket,
            Key=f"narratives/{cache_key}.json"
        )
        return json.loads(response['Body'].read())
    except:
        # Generate new narrative
        narrative = generate_narrative(stats)
        
        # Cache the result
        s3_client.put_object(
            Bucket=bucket,
            Key=f"narratives/{cache_key}.json",
            Body=json.dumps(narrative),
            ContentType='application/json'
        )
        
        return narrative
```

## Monitoring and Troubleshooting

### CloudWatch Metrics

Monitor Bedrock usage through CloudWatch:

```bash
# Check Bedrock invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name Invocations \
  --dimensions Name=ModelId,Value=anthropic.claude-3-sonnet-20240229-v1:0 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum

# Check error rates
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name InvocationClientErrors \
  --dimensions Name=ModelId,Value=anthropic.claude-3-sonnet-20240229-v1:0 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### Common Issues

#### 1. Access Denied Errors
```
Error: AccessDeniedException: You don't have access to the model
```
**Solution**: Request model access through AWS Console

#### 2. Region Not Supported
```
Error: ValidationException: The model is not supported in this region
```
**Solution**: Deploy to a supported region (us-east-1, us-west-2)

#### 3. Token Limit Exceeded
```
Error: ValidationException: Input is too long
```
**Solution**: Reduce prompt length or max_tokens parameter

#### 4. Rate Limiting
```
Error: ThrottlingException: Rate exceeded
```
**Solution**: Implement exponential backoff and retry logic

### Debugging Tips

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_bedrock_call(model_id, prompt):
    """Debug Bedrock API calls."""
    logger.debug(f"Model ID: {model_id}")
    logger.debug(f"Prompt length: {len(prompt)} characters")
    logger.debug(f"Prompt preview: {prompt[:200]}...")
    
    # Add timing
    import time
    start_time = time.time()
    
    try:
        result = invoke_bedrock_model(prompt)
        duration = time.time() - start_time
        logger.debug(f"Bedrock call completed in {duration:.2f}s")
        return result
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Bedrock call failed after {duration:.2f}s: {str(e)}")
        raise
```

## Testing

### Unit Tests
```python
import pytest
from moto import mock_bedrock
import boto3

@mock_bedrock
def test_bedrock_narrative_generation():
    """Test Bedrock narrative generation with mocked service."""
    
    # Mock Bedrock client
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Test data
    stats = {
        'total_games': 150,
        'win_rate': 65.5,
        'top_champion': 'Jinx',
        'avg_kda': 2.3
    }
    
    # Test narrative generation
    narrative = generate_narrative(stats)
    
    assert len(narrative) > 100
    assert 'Jinx' in narrative
    assert '150' in narrative
```

### Integration Tests
```python
def test_bedrock_integration():
    """Test actual Bedrock integration (requires model access)."""
    
    if not os.environ.get('BEDROCK_INTEGRATION_TEST'):
        pytest.skip("Bedrock integration test disabled")
    
    stats = {
        'total_games': 50,
        'win_rate': 70.0,
        'top_champion': 'Yasuo',
        'avg_kda': 1.8
    }
    
    narrative = generate_narrative(stats)
    
    # Verify narrative quality
    assert len(narrative) > 200
    assert len(narrative) < 2000
    assert 'Yasuo' in narrative
    assert any(word in narrative.lower() for word in ['year', 'season', 'games'])
```

## Next Steps

1. **Deploy Infrastructure**: Run `make deploy` to create the Lambda functions with Bedrock permissions
2. **Request Model Access**: Follow the AWS Console steps above
3. **Test Integration**: Use the provided test scripts to verify Bedrock connectivity
4. **Monitor Usage**: Set up CloudWatch dashboards for cost and performance tracking
5. **Optimize Prompts**: Iterate on prompt engineering for better narrative quality

For questions or issues, check the [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/) or the project's troubleshooting guide.