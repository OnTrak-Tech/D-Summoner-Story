#!/bin/bash

# Infrastructure Validation Script
# Checks if all components are properly deployed and configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}

print_status() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Check if Terraform is initialized and state exists
check_terraform_state() {
    print_header "Terraform State"
    
    if [[ ! -d ".terraform" ]]; then
        print_error "Terraform not initialized. Run 'terraform init' first."
        return 1
    fi
    
    if terraform show &>/dev/null; then
        print_success "Terraform state is valid"
    else
        print_error "No Terraform state found or state is invalid"
        return 1
    fi
}

# Check AWS credentials and region
check_aws_config() {
    print_header "AWS Configuration"
    
    if ! aws sts get-caller-identity &>/dev/null; then
        print_error "AWS credentials not configured"
        return 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    CURRENT_REGION=$(aws configure get region)
    
    print_success "AWS Account: $ACCOUNT_ID"
    print_success "AWS Region: $CURRENT_REGION"
    
    if [[ "$CURRENT_REGION" != "$REGION" ]]; then
        print_warning "Current region ($CURRENT_REGION) differs from target region ($REGION)"
    fi
}

# Check S3 buckets
check_s3_buckets() {
    print_header "S3 Buckets"
    
    local buckets=(
        "raw_data_bucket_name"
        "processed_insights_bucket_name" 
        "static_website_bucket_name"
    )
    
    for bucket_output in "${buckets[@]}"; do
        if bucket_name=$(terraform output -raw "$bucket_output" 2>/dev/null); then
            if aws s3 ls "s3://$bucket_name" &>/dev/null; then
                print_success "S3 bucket exists: $bucket_name"
            else
                print_error "S3 bucket not accessible: $bucket_name"
            fi
        else
            print_error "Cannot get bucket name for: $bucket_output"
        fi
    done
}

# Check DynamoDB tables
check_dynamodb_tables() {
    print_header "DynamoDB Tables"
    
    local tables=(
        "player_stats_table_name"
        "processing_jobs_table_name"
    )
    
    for table_output in "${tables[@]}"; do
        if table_name=$(terraform output -raw "$table_output" 2>/dev/null); then
            if aws dynamodb describe-table --table-name "$table_name" &>/dev/null; then
                print_success "DynamoDB table exists: $table_name"
                
                # Check TTL configuration
                ttl_status=$(aws dynamodb describe-time-to-live --table-name "$table_name" --query 'TimeToLiveDescription.TimeToLiveStatus' --output text 2>/dev/null || echo "UNKNOWN")
                if [[ "$ttl_status" == "ENABLED" ]]; then
                    print_success "  TTL enabled"
                else
                    print_warning "  TTL not enabled or unknown status: $ttl_status"
                fi
            else
                print_error "DynamoDB table not accessible: $table_name"
            fi
        else
            print_error "Cannot get table name for: $table_output"
        fi
    done
}

# Check Lambda functions
check_lambda_functions() {
    print_header "Lambda Functions"
    
    if lambda_functions=$(terraform output -json lambda_functions 2>/dev/null); then
        echo "$lambda_functions" | jq -r 'to_entries[] | "\(.key): \(.value)"' | while IFS=': ' read -r name arn; do
            function_name=$(echo "$arn" | cut -d':' -f7)
            
            if aws lambda get-function --function-name "$function_name" &>/dev/null; then
                print_success "Lambda function exists: $name ($function_name)"
                
                # Check function configuration
                runtime=$(aws lambda get-function-configuration --function-name "$function_name" --query Runtime --output text)
                timeout=$(aws lambda get-function-configuration --function-name "$function_name" --query Timeout --output text)
                memory=$(aws lambda get-function-configuration --function-name "$function_name" --query MemorySize --output text)
                
                print_success "  Runtime: $runtime, Timeout: ${timeout}s, Memory: ${memory}MB"
            else
                print_error "Lambda function not accessible: $name"
            fi
        done
    else
        print_error "Cannot get Lambda function information"
    fi
}

# Check API Gateway
check_api_gateway() {
    print_header "API Gateway"
    
    if api_endpoint=$(terraform output -raw api_endpoint 2>/dev/null); then
        print_success "API Gateway endpoint: $api_endpoint"
        
        # Test API connectivity
        if curl -s -o /dev/null -w "%{http_code}" "$api_endpoint" | grep -q "404\|403\|200"; then
            print_success "API Gateway is responding"
        else
            print_warning "API Gateway may not be responding correctly"
        fi
    else
        print_error "Cannot get API Gateway endpoint"
    fi
}

# Check CloudFront distribution
check_cloudfront() {
    print_header "CloudFront Distribution"
    
    if distribution_id=$(terraform output -raw cloudfront_distribution_id 2>/dev/null); then
        if aws cloudfront get-distribution --id "$distribution_id" &>/dev/null; then
            print_success "CloudFront distribution exists: $distribution_id"
            
            status=$(aws cloudfront get-distribution --id "$distribution_id" --query 'Distribution.Status' --output text)
            print_success "  Status: $status"
            
            if website_url=$(terraform output -raw website_url 2>/dev/null); then
                print_success "  Website URL: $website_url"
            fi
        else
            print_error "CloudFront distribution not accessible: $distribution_id"
        fi
    else
        print_error "Cannot get CloudFront distribution ID"
    fi
}

# Check Secrets Manager
check_secrets_manager() {
    print_header "Secrets Manager"
    
    if secret_arn=$(terraform output -raw riot_api_secret_arn 2>/dev/null); then
        if aws secretsmanager describe-secret --secret-id "$secret_arn" &>/dev/null; then
            print_success "Secret exists: $secret_arn"
            
            # Check if secret has a value (without revealing it)
            if aws secretsmanager get-secret-value --secret-id "$secret_arn" --query 'SecretString' --output text | grep -q "PLACEHOLDER"; then
                print_warning "  Secret contains placeholder value - update with real Riot API key"
            else
                print_success "  Secret appears to be configured"
            fi
        else
            print_error "Secret not accessible: $secret_arn"
        fi
    else
        print_error "Cannot get secret ARN"
    fi
}

# Check Bedrock model access
check_bedrock_access() {
    print_header "Bedrock Model Access"
    
    # Check if Bedrock is available in the region
    if aws bedrock list-foundation-models --region "$REGION" &>/dev/null; then
        print_success "Bedrock service is available in region: $REGION"
        
        # Check specific model access
        if aws bedrock get-foundation-model --model-identifier "anthropic.claude-3-sonnet-20240229-v1:0" --region "$REGION" &>/dev/null; then
            print_success "Claude 3 Sonnet model is available"
        else
            print_warning "Claude 3 Sonnet model access may not be granted - check AWS Console"
        fi
    else
        print_error "Bedrock service not available in region: $REGION"
    fi
}

# Check CloudWatch resources
check_cloudwatch() {
    print_header "CloudWatch Monitoring"
    
    # Check dashboard
    dashboard_name="d-summoner-story-${ENVIRONMENT}-dashboard"
    if aws cloudwatch get-dashboard --dashboard-name "$dashboard_name" &>/dev/null; then
        print_success "CloudWatch dashboard exists: $dashboard_name"
    else
        print_error "CloudWatch dashboard not found: $dashboard_name"
    fi
    
    # Check SNS topic
    if topic_arn=$(terraform output -raw sns_alerts_topic_arn 2>/dev/null); then
        if aws sns get-topic-attributes --topic-arn "$topic_arn" &>/dev/null; then
            print_success "SNS alerts topic exists: $topic_arn"
            
            # Check subscriptions
            subscription_count=$(aws sns list-subscriptions-by-topic --topic-arn "$topic_arn" --query 'length(Subscriptions)' --output text)
            if [[ "$subscription_count" -gt 0 ]]; then
                print_success "  $subscription_count subscription(s) configured"
            else
                print_warning "  No subscriptions configured - add email/SMS alerts"
            fi
        else
            print_error "SNS topic not accessible: $topic_arn"
        fi
    else
        print_error "Cannot get SNS topic ARN"
    fi
}

# Check IAM permissions
check_iam_permissions() {
    print_header "IAM Permissions"
    
    # Check if current user can perform necessary operations
    local permissions_ok=true
    
    # Test S3 permissions
    if bucket_name=$(terraform output -raw raw_data_bucket_name 2>/dev/null); then
        if aws s3api head-bucket --bucket "$bucket_name" &>/dev/null; then
            print_success "S3 access permissions verified"
        else
            print_error "S3 access permissions insufficient"
            permissions_ok=false
        fi
    fi
    
    # Test DynamoDB permissions
    if table_name=$(terraform output -raw player_stats_table_name 2>/dev/null); then
        if aws dynamodb describe-table --table-name "$table_name" &>/dev/null; then
            print_success "DynamoDB access permissions verified"
        else
            print_error "DynamoDB access permissions insufficient"
            permissions_ok=false
        fi
    fi
    
    if [[ "$permissions_ok" == "true" ]]; then
        print_success "IAM permissions appear sufficient"
    else
        print_error "IAM permissions may be insufficient"
    fi
}

# Generate summary report
generate_summary() {
    print_header "Validation Summary"
    
    echo -e "\n${GREEN}Infrastructure Status for Environment: $ENVIRONMENT${NC}"
    echo "Region: $REGION"
    echo "Timestamp: $(date)"
    echo ""
    
    if website_url=$(terraform output -raw website_url 2>/dev/null); then
        echo "🌐 Website URL: $website_url"
    fi
    
    if api_endpoint=$(terraform output -raw api_endpoint 2>/dev/null); then
        echo "🔗 API Endpoint: $api_endpoint"
    fi
    
    if dashboard_url=$(terraform output -raw cloudwatch_dashboard_url 2>/dev/null); then
        echo "📊 Dashboard: $dashboard_url"
    fi
    
    echo ""
    echo "Next steps:"
    echo "1. Update Riot API key in Secrets Manager if needed"
    echo "2. Request Bedrock model access if not already done"
    echo "3. Subscribe to SNS alerts for monitoring"
    echo "4. Deploy frontend application to S3"
    echo "5. Test end-to-end functionality"
}

# Main execution
main() {
    echo -e "${BLUE}D-Summoner-Story Infrastructure Validation${NC}"
    echo "Environment: $ENVIRONMENT"
    echo "Region: $REGION"
    echo ""
    
    # Run all checks
    check_terraform_state
    check_aws_config
    check_s3_buckets
    check_dynamodb_tables
    check_lambda_functions
    check_api_gateway
    check_cloudfront
    check_secrets_manager
    check_bedrock_access
    check_cloudwatch
    check_iam_permissions
    
    generate_summary
    
    echo -e "\n${GREEN}Validation completed!${NC}"
}

# Show usage if help requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: $0 [environment] [region]"
    echo ""
    echo "Arguments:"
    echo "  environment    Deployment environment (default: dev)"
    echo "  region         AWS region (default: us-east-1)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Validate dev environment in us-east-1"
    echo "  $0 prod us-west-2     # Validate prod environment in us-west-2"
    exit 0
fi

# Run main function
main