# Terraform Infrastructure

This directory contains the complete Infrastructure-as-Code for the League of Legends Year in Review serverless application.

## Architecture Overview

The infrastructure provisions a fully serverless architecture on AWS including:

- **S3 Buckets**: Raw data storage, processed insights, and static website hosting
- **DynamoDB Tables**: Player statistics and processing job tracking with TTL
- **Lambda Functions**: Complete data processing pipeline (auth, fetch, process, generate, serve)
- **API Gateway**: HTTP API with CORS for all backend endpoints
- **CloudFront**: CDN distribution for static website and API caching
- **Secrets Manager**: Secure storage for Riot Games API credentials
- **CloudWatch**: Comprehensive monitoring, dashboards, and alerting
- **IAM**: Least-privilege access policies for all services

## Module Structure

Reusable modules under `infrastructure/terraform/modules/`:

- `modules/s3_bucket` — S3 bucket with versioning, lifecycle, encryption, and security
- `modules/dynamodb_table` — DynamoDB table with TTL, PITR, and flexible schema
- `modules/lambda_function` — Lambda with IAM role, policies, and CloudWatch logging
- `modules/apigateway_http` — HTTP API Gateway v2 with CORS and Lambda integrations

## Infrastructure Components

### Storage Layer
- **Raw Data Bucket**: Stores match data from Riot API with lifecycle policies
- **Processed Insights Bucket**: Caches AI-generated narratives and visualizations
- **Static Website Bucket**: Hosts React frontend with CloudFront integration

### Compute Layer
- **Auth Lambda**: Session management and summoner validation (10s timeout, 256MB)
- **Data Fetcher Lambda**: Riot API integration with rate limiting (5min timeout, 512MB)
- **Data Processor Lambda**: Statistical analysis and trend calculation (5min timeout, 1GB)
- **Insight Generator Lambda**: AI narrative generation via Bedrock (3min timeout, 512MB)
- **Recap Server Lambda**: API responses and data aggregation (30s timeout, 256MB)

### Data Layer
- **Player Stats Table**: Processed statistics with PK/SK pattern and TTL
- **Processing Jobs Table**: Async job tracking with status and progress

### Security & Monitoring
- **Secrets Manager**: Riot API key with automatic rotation support
- **CloudWatch Dashboard**: Real-time metrics for all services
- **CloudWatch Alarms**: Error rates, duration thresholds, and cost monitoring
- **SNS Alerts**: Notifications for critical failures and cost overruns

## Configuration

### Variables
```hcl
variable "aws_region" {
  default = "us-east-1"  # Required for Bedrock availability
}

variable "project_name" {
  default = "d-summoner-story"
}

variable "environment" {
  default = "dev"  # dev, staging, prod
}

variable "tags" {
  default = {}  # Additional resource tags
}
```

### Resource Naming
All resources use the pattern: `${project_name}-${environment}-${resource_type}`
Example: `d-summoner-story-dev-auth` for the auth Lambda function.

## Deployment Guide

### Prerequisites
1. **AWS CLI** configured with appropriate permissions
2. **Terraform** >= 1.6.0 installed
3. **Python 3.12** for Lambda function packaging
4. **Riot Games API Key** from [Riot Developer Portal](https://developer.riotgames.com/)

### Initial Setup

1. **Clone and navigate to infrastructure directory**:
   ```bash
   cd infrastructure/terraform
   ```

2. **Configure remote state backend** (recommended for production):
   ```bash
   # Create S3 bucket for state
   aws s3 mb s3://your-terraform-state-bucket --region us-east-1
   
   # Create DynamoDB table for state locking
   aws dynamodb create-table \
     --table-name terraform-state-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
     --region us-east-1
   
   # Configure backend
   cp backend.tf.example backend.tf
   # Edit backend.tf with your bucket name
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Plan deployment**:
   ```bash
   terraform plan -var="environment=dev"
   ```

5. **Deploy infrastructure**:
   ```bash
   terraform apply -var="environment=dev"
   ```

### Post-Deployment Configuration

1. **Update Riot API Key in Secrets Manager**:
   ```bash
   aws secretsmanager update-secret \
     --secret-id $(terraform output -raw riot_api_secret_arn) \
     --secret-string '{"api_key":"YOUR_RIOT_API_KEY_HERE"}'
   ```

2. **Deploy frontend to S3**:
   ```bash
   cd ../../frontend
   npm run build
   aws s3 sync dist/ s3://$(terraform output -raw static_website_bucket_name)/
   ```

3. **Invalidate CloudFront cache**:
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id $(terraform output -raw cloudfront_distribution_id) \
     --paths "/*"
   ```

### Environment Management

Create separate environments by using different variable values:

```bash
# Development
terraform workspace new dev
terraform apply -var="environment=dev"

# Staging
terraform workspace new staging
terraform apply -var="environment=staging"

# Production
terraform workspace new prod
terraform apply -var="environment=prod"
```

## Monitoring and Observability

### CloudWatch Dashboard
Access the monitoring dashboard:
```bash
echo $(terraform output -raw cloudwatch_dashboard_url)
```

### Key Metrics Monitored
- **Lambda Performance**: Duration, errors, invocations, memory usage
- **API Gateway**: Request count, 4XX/5XX errors, latency
- **DynamoDB**: Read/write capacity, throttling, item count
- **Cost Monitoring**: Daily estimated charges with $50 threshold

### Alerting
SNS topic configured for:
- Lambda function errors (>5 in 10 minutes)
- Lambda duration exceeding 80% of timeout
- API Gateway 5XX errors (>10 in 10 minutes)
- Daily AWS costs exceeding $50

Subscribe to alerts:
```bash
aws sns subscribe \
  --topic-arn $(terraform output -raw sns_alerts_topic_arn) \
  --protocol email \
  --notification-endpoint your-email@example.com
```

## Security Best Practices

### IAM Policies
- **Least Privilege**: Each Lambda has minimal required permissions
- **Resource-Specific**: Policies target specific S3 buckets and DynamoDB tables
- **No Wildcards**: Explicit resource ARNs where possible

### Data Protection
- **S3 Encryption**: AES-256 server-side encryption enabled
- **Secrets Management**: API keys stored in AWS Secrets Manager
- **Public Access**: S3 buckets block all public access except via CloudFront

### Network Security
- **HTTPS Only**: CloudFront redirects HTTP to HTTPS
- **CORS Configuration**: API Gateway configured for frontend domain only

## Cost Optimization

### Free Tier Usage
Designed to stay within AWS Free Tier limits:
- **Lambda**: 1M requests/month, 400,000 GB-seconds compute
- **API Gateway**: 1M requests/month
- **DynamoDB**: 25GB storage, 25 RCU/WCU
- **S3**: 5GB storage, 20,000 GET requests
- **CloudFront**: 50GB data transfer

### Lifecycle Policies
- **S3 Raw Data**: Transition to IA after 30 days, expire after 365 days
- **DynamoDB TTL**: Automatic cleanup of old records
- **CloudWatch Logs**: 14-day retention for Lambda logs

## Troubleshooting

### Common Issues

1. **Lambda Timeout**: Increase timeout in module configuration
2. **DynamoDB Throttling**: Switch to on-demand billing mode
3. **API Rate Limits**: Implement exponential backoff in Lambda code
4. **CloudFront Cache**: Use invalidation for immediate updates

### Useful Commands

```bash
# Check Lambda logs
aws logs tail /aws/lambda/d-summoner-story-dev-auth --follow

# Monitor API Gateway
aws logs tail /aws/apigateway/d-summoner-story-dev-api --follow

# Check DynamoDB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=d-summoner-story-dev-player-stats \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## CI/CD Integration

### GitHub Actions Secrets
Configure these repository secrets:
- `AWS_ACCESS_KEY_ID`: IAM user access key with deployment permissions
- `AWS_SECRET_ACCESS_KEY`: IAM user secret key
- `AWS_REGION`: Deployment region (us-east-1 recommended)

### Deployment Workflow
The infrastructure supports automated deployment via GitHub Actions:
1. **Test**: Run Terraform plan on pull requests
2. **Deploy**: Apply changes on merge to main branch
3. **Notify**: Send deployment status to configured channels

## Outputs Reference

After deployment, access key information:

```bash
# API endpoint for frontend integration
terraform output api_endpoint

# Website URL for users
terraform output website_url

# CloudWatch dashboard for monitoring
terraform output cloudwatch_dashboard_url

# All Lambda function ARNs
terraform output lambda_functions
```
