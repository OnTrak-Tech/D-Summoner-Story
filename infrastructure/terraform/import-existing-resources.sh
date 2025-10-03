#!/bin/bash

# Import existing AWS resources into Terraform state
set -e

ENVIRONMENT=${1:-prod}
REGION=${2:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Importing existing resources for environment: $ENVIRONMENT"

# Import S3 buckets
terraform import module.s3_raw_data.aws_s3_bucket.this "d-summoner-story-${ENVIRONMENT}-raw-data" 2>/dev/null || true
terraform import module.s3_processed_insights.aws_s3_bucket.this "d-summoner-story-${ENVIRONMENT}-processed-insights" 2>/dev/null || true
terraform import module.s3_static_website.aws_s3_bucket.this "d-summoner-story-${ENVIRONMENT}-website" 2>/dev/null || true

# Import DynamoDB tables
terraform import module.ddb_player_stats.aws_dynamodb_table.this "d-summoner-story-${ENVIRONMENT}-player-stats" 2>/dev/null || true
terraform import module.ddb_processing_jobs.aws_dynamodb_table.this "d-summoner-story-${ENVIRONMENT}-processing-jobs" 2>/dev/null || true

# Import Secrets Manager secret
terraform import aws_secretsmanager_secret.riot_api_key "d-summoner-story-${ENVIRONMENT}-riot-api-key" 2>/dev/null || true

# Import IAM roles
terraform import module.lambda_auth.aws_iam_role.this "d-summoner-story-${ENVIRONMENT}-auth-role" 2>/dev/null || true
terraform import module.lambda_data_fetcher.aws_iam_role.this "d-summoner-story-${ENVIRONMENT}-data-fetcher-role" 2>/dev/null || true
terraform import module.lambda_data_processor.aws_iam_role.this "d-summoner-story-${ENVIRONMENT}-data-processor-role" 2>/dev/null || true
terraform import module.lambda_insight_generator.aws_iam_role.this "d-summoner-story-${ENVIRONMENT}-insight-generator-role" 2>/dev/null || true
terraform import module.lambda_recap_server.aws_iam_role.this "d-summoner-story-${ENVIRONMENT}-recap-server-role" 2>/dev/null || true

# Import IAM policies
terraform import aws_iam_policy.lambda_bedrock "arn:aws:iam::${ACCOUNT_ID}:policy/d-summoner-story-${ENVIRONMENT}-lambda-bedrock" 2>/dev/null || true
terraform import aws_iam_policy.lambda_dynamodb "arn:aws:iam::${ACCOUNT_ID}:policy/d-summoner-story-${ENVIRONMENT}-lambda-dynamodb" 2>/dev/null || true
terraform import aws_iam_policy.lambda_s3 "arn:aws:iam::${ACCOUNT_ID}:policy/d-summoner-story-${ENVIRONMENT}-lambda-s3" 2>/dev/null || true
terraform import aws_iam_policy.lambda_secrets "arn:aws:iam::${ACCOUNT_ID}:policy/d-summoner-story-${ENVIRONMENT}-lambda-secrets" 2>/dev/null || true

# Import Lambda functions
terraform import module.lambda_auth.aws_lambda_function.this "d-summoner-story-${ENVIRONMENT}-auth" 2>/dev/null || true
terraform import module.lambda_data_fetcher.aws_lambda_function.this "d-summoner-story-${ENVIRONMENT}-data-fetcher" 2>/dev/null || true
terraform import module.lambda_data_processor.aws_lambda_function.this "d-summoner-story-${ENVIRONMENT}-data-processor" 2>/dev/null || true
terraform import module.lambda_insight_generator.aws_lambda_function.this "d-summoner-story-${ENVIRONMENT}-insight-generator" 2>/dev/null || true
terraform import module.lambda_recap_server.aws_lambda_function.this "d-summoner-story-${ENVIRONMENT}-recap-server" 2>/dev/null || true

# Import CloudWatch Log Groups
terraform import module.lambda_auth.aws_cloudwatch_log_group.this "/aws/lambda/d-summoner-story-${ENVIRONMENT}-auth" 2>/dev/null || true
terraform import module.lambda_data_fetcher.aws_cloudwatch_log_group.this "/aws/lambda/d-summoner-story-${ENVIRONMENT}-data-fetcher" 2>/dev/null || true
terraform import module.lambda_data_processor.aws_cloudwatch_log_group.this "/aws/lambda/d-summoner-story-${ENVIRONMENT}-data-processor" 2>/dev/null || true
terraform import module.lambda_insight_generator.aws_cloudwatch_log_group.this "/aws/lambda/d-summoner-story-${ENVIRONMENT}-insight-generator" 2>/dev/null || true
terraform import module.lambda_recap_server.aws_cloudwatch_log_group.this "/aws/lambda/d-summoner-story-${ENVIRONMENT}-recap-server" 2>/dev/null || true

# Import Lambda permissions (these are tricky - need to get the statement IDs)
terraform import 'module.http_api.aws_lambda_permission.apigw["POST /api/v1/auth"]' "d-summoner-story-${ENVIRONMENT}-auth/AllowAPIGatewayInvoke-POST--api-v1-auth" 2>/dev/null || true
terraform import 'module.http_api.aws_lambda_permission.apigw["POST /api/v1/fetch"]' "d-summoner-story-${ENVIRONMENT}-data-fetcher/AllowAPIGatewayInvoke-POST--api-v1-fetch" 2>/dev/null || true
terraform import 'module.http_api.aws_lambda_permission.apigw["GET /api/v1/status/{jobId}"]' "d-summoner-story-${ENVIRONMENT}-data-processor/AllowAPIGatewayInvoke-GET--api-v1-status-jobId" 2>/dev/null || true
terraform import 'module.http_api.aws_lambda_permission.apigw["GET /api/v1/recap/{sessionId}"]' "d-summoner-story-${ENVIRONMENT}-recap-server/AllowAPIGatewayInvoke-GET--api-v1-recap-sessionId" 2>/dev/null || true
terraform import 'module.http_api.aws_lambda_permission.apigw["POST /api/v1/share/{sessionId}"]' "d-summoner-story-${ENVIRONMENT}-recap-server/AllowAPIGatewayInvoke-POST--api-v1-share-sessionId" 2>/dev/null || true

# Import CloudFront OAC
OAC_ID=$(aws cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?Name=='d-summoner-story-${ENVIRONMENT}-website-oac'].Id" --output text 2>/dev/null || echo "")
if [[ -n "$OAC_ID" ]]; then
    terraform import aws_cloudfront_origin_access_control.website "$OAC_ID" 2>/dev/null || true
fi

echo "Import completed."