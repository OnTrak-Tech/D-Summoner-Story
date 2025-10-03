#!/bin/bash

# D-Summoner-Story Infrastructure Cleanup Script
# This script safely destroys the Terraform infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
AWS_REGION="us-east-1"
FORCE=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -e, --environment ENV     Environment to destroy (default: dev)"
    echo "  -r, --region REGION       AWS region (default: us-east-1)"
    echo "  -f, --force               Skip confirmation prompts"
    echo "  -h, --help                Show this help message"
    echo
    echo "Examples:"
    echo "  $0                        # Destroy dev environment with confirmation"
    echo "  $0 -e prod -f            # Force destroy prod environment"
}

# Function to empty S3 buckets
empty_s3_buckets() {
    print_status "Emptying S3 buckets before destruction..."
    
    # Get bucket names from Terraform output
    RAW_DATA_BUCKET=$(terraform output -raw raw_data_bucket_name 2>/dev/null || echo "")
    PROCESSED_INSIGHTS_BUCKET=$(terraform output -raw processed_insights_bucket_name 2>/dev/null || echo "")
    STATIC_WEBSITE_BUCKET=$(terraform output -raw static_website_bucket_name 2>/dev/null || echo "")
    
    # Empty each bucket if it exists
    for BUCKET in "$RAW_DATA_BUCKET" "$PROCESSED_INSIGHTS_BUCKET" "$STATIC_WEBSITE_BUCKET"; do
        if [[ -n "$BUCKET" ]]; then
            print_status "Emptying bucket: $BUCKET"
            aws s3 rm "s3://$BUCKET" --recursive --quiet || {
                print_warning "Failed to empty bucket $BUCKET (it might not exist)"
            }
        fi
    done
    
    print_success "S3 buckets emptied"
}

# Function to disable CloudFront distribution
disable_cloudfront() {
    print_status "Disabling CloudFront distribution..."
    
    DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")
    
    if [[ -n "$DISTRIBUTION_ID" ]]; then
        # Get current distribution config
        ETAG=$(aws cloudfront get-distribution --id "$DISTRIBUTION_ID" --query 'ETag' --output text 2>/dev/null || echo "")
        
        if [[ -n "$ETAG" ]]; then
            # Get distribution config and disable it
            aws cloudfront get-distribution-config --id "$DISTRIBUTION_ID" --query 'DistributionConfig' > /tmp/dist-config.json
            
            # Update enabled status to false
            jq '.Enabled = false' /tmp/dist-config.json > /tmp/dist-config-disabled.json
            
            # Update the distribution
            aws cloudfront update-distribution \
                --id "$DISTRIBUTION_ID" \
                --distribution-config file:///tmp/dist-config-disabled.json \
                --if-match "$ETAG" > /dev/null
            
            print_status "CloudFront distribution disabled. Waiting for deployment..."
            aws cloudfront wait distribution-deployed --id "$DISTRIBUTION_ID"
            
            # Clean up temp files
            rm -f /tmp/dist-config.json /tmp/dist-config-disabled.json
        fi
    fi
    
    print_success "CloudFront distribution disabled"
}

# Function to destroy infrastructure
destroy_infrastructure() {
    print_status "Destroying infrastructure for environment: $ENVIRONMENT"
    
    # Check if Terraform state exists
    if [[ ! -f "terraform.tfstate" ]] && [[ ! -f "backend.tf" ]]; then
        print_error "No Terraform state found. Nothing to destroy."
        exit 1
    fi
    
    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init
    
    # Show what will be destroyed
    print_status "Planning destruction..."
    terraform plan -destroy \
        -var="environment=$ENVIRONMENT" \
        -var="aws_region=$AWS_REGION"
    
    # Confirmation
    if [[ "$FORCE" != "true" ]]; then
        echo
        print_warning "This will permanently destroy all infrastructure resources!"
        print_warning "This action cannot be undone!"
        echo
        read -p "Are you absolutely sure you want to destroy the $ENVIRONMENT environment? (type 'yes' to confirm): " CONFIRMATION
        
        if [[ "$CONFIRMATION" != "yes" ]]; then
            print_warning "Destruction cancelled by user"
            exit 0
        fi
        
        echo
        read -p "Last chance! Type the environment name '$ENVIRONMENT' to proceed: " FINAL_CONFIRMATION
        
        if [[ "$FINAL_CONFIRMATION" != "$ENVIRONMENT" ]]; then
            print_warning "Environment name mismatch. Destruction cancelled."
            exit 0
        fi
    fi
    
    # Prepare for destruction
    empty_s3_buckets
    disable_cloudfront
    
    # Destroy infrastructure
    print_status "Destroying Terraform resources..."
    terraform destroy \
        -var="environment=$ENVIRONMENT" \
        -var="aws_region=$AWS_REGION" \
        -auto-approve
    
    print_success "Infrastructure destruction completed!"
}

# Function to cleanup local files
cleanup_local_files() {
    print_status "Cleaning up local Terraform files..."
    
    # Remove Terraform files
    rm -rf .terraform/
    rm -f terraform.tfstate*
    rm -f tfplan
    rm -f .terraform.lock.hcl
    
    print_success "Local cleanup completed"
}

# Function to show cleanup summary
show_cleanup_summary() {
    print_success "Cleanup Summary"
    echo "================"
    echo
    echo "✓ All AWS resources destroyed"
    echo "✓ S3 buckets emptied and removed"
    echo "✓ CloudFront distribution disabled and removed"
    echo "✓ DynamoDB tables removed"
    echo "✓ Lambda functions removed"
    echo "✓ IAM roles and policies removed"
    echo "✓ CloudWatch resources removed"
    echo "✓ Local Terraform state cleaned up"
    echo
    print_warning "Note: The following may still exist and require manual cleanup:"
    echo "- Terraform state S3 bucket (if using remote backend)"
    echo "- DynamoDB state locking table (if using remote backend)"
    echo "- CloudWatch log groups (may have retention period)"
    echo "- Any manual SNS subscriptions you created"
    echo
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "Starting D-Summoner-Story infrastructure cleanup"
    print_status "Environment: $ENVIRONMENT"
    print_status "AWS Region: $AWS_REGION"
    echo
    
    destroy_infrastructure
    cleanup_local_files
    show_cleanup_summary
    
    print_success "Infrastructure cleanup completed successfully!"
}

# Run main function
main