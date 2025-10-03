#!/bin/bash

# Import existing AWS resources into Terraform state
# This script imports resources that already exist in AWS but are not in Terraform state

set -e

ENVIRONMENT=${1:-prod}
REGION=${2:-us-east-1}

echo "Importing existing resources for environment: $ENVIRONMENT"

# Import S3 buckets
echo "Importing S3 buckets..."
terraform import module.s3_raw_data.aws_s3_bucket.this "d-summoner-story-${ENVIRONMENT}-raw-data" || echo "Already imported or doesn't exist"
terraform import module.s3_processed_insights.aws_s3_bucket.this "d-summoner-story-${ENVIRONMENT}-processed-insights" || echo "Already imported or doesn't exist"
terraform import module.s3_static_website.aws_s3_bucket.this "d-summoner-story-${ENVIRONMENT}-website" || echo "Already imported or doesn't exist"

# Import DynamoDB tables
echo "Importing DynamoDB tables..."
terraform import module.ddb_player_stats.aws_dynamodb_table.this "d-summoner-story-${ENVIRONMENT}-player-stats" || echo "Already imported or doesn't exist"
terraform import module.ddb_processing_jobs.aws_dynamodb_table.this "d-summoner-story-${ENVIRONMENT}-processing-jobs" || echo "Already imported or doesn't exist"

# Import Secrets Manager secret
echo "Importing Secrets Manager secret..."
terraform import aws_secretsmanager_secret.riot_api_key "d-summoner-story-${ENVIRONMENT}-riot-api-key" || echo "Already imported or doesn't exist"

# Import IAM roles
echo "Importing IAM roles..."
terraform import module.lambda_auth.aws_iam_role.this "d-summoner-story-${ENVIRONMENT}-auth-role" || echo "Already imported or doesn't exist"
terraform import module.lambda_data_fetcher.aws_iam_role.this "d-summoner-story-${ENVIRONMENT}-data-fetcher-role" || echo "Already imported or doesn't exist"
terraform import module.lambda_data_processor.aws_iam_role.this "d-summoner-story-${ENVIRONMENT}-data-processor-role" || echo "Already imported or doesn't exist"
terraform import module.lambda_insight_generator.aws_iam_role.this "d-summoner-story-${ENVIRONMENT}-insight-generator-role" || echo "Already imported or doesn't exist"
terraform import module.lambda_recap_server.aws_iam_role.this "d-summoner-story-${ENVIRONMENT}-recap-server-role" || echo "Already imported or doesn't exist"

# Import IAM policies
echo "Importing IAM policies..."
terraform import aws_iam_policy.lambda_bedrock "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/d-summoner-story-${ENVIRONMENT}-lambda-bedrock" || echo "Already imported or doesn't exist"

# Import CloudFront OAC
echo "Importing CloudFront Origin Access Control..."
OAC_ID=$(aws cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?Name=='d-summoner-story-${ENVIRONMENT}-website-oac'].Id" --output text 2>/dev/null || echo "")
if [[ -n "$OAC_ID" ]]; then
    terraform import aws_cloudfront_origin_access_control.website "$OAC_ID" || echo "Already imported"
fi

echo "Import completed. Run 'terraform plan' to verify state."