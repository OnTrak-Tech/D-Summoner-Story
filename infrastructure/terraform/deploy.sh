#!/bin/bash

# D-Summoner-Story Infrastructure Deployment Script
# This script helps deploy the Terraform infrastructure with proper validation

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
SKIP_BACKEND_SETUP=false
RIOT_API_KEY=""

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if AWS CLI is installed and configured
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install Terraform >= 1.6.0"
        exit 1
    fi
    
    # Check Terraform version
    TERRAFORM_VERSION=$(terraform version -json | jq -r '.terraform_version')
    if [[ $(echo "$TERRAFORM_VERSION 1.6.0" | tr " " "\n" | sort -V | head -n1) != "1.6.0" ]]; then
        print_error "Terraform version must be >= 1.6.0. Current version: $TERRAFORM_VERSION"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Function to setup remote backend
setup_backend() {
    if [[ "$SKIP_BACKEND_SETUP" == "true" ]]; then
        print_warning "Skipping backend setup as requested"
        return
    fi
    
    print_status "Setting up remote backend..."
    
    BUCKET_NAME="terraform-state-$(date +%s)-$(whoami)"
    TABLE_NAME="terraform-state-locks"
    
    # Create S3 bucket for state
    print_status "Creating S3 bucket: $BUCKET_NAME"
    aws s3 mb "s3://$BUCKET_NAME" --region "$AWS_REGION" || {
        print_warning "Bucket creation failed, it might already exist"
    }
    
    # Enable versioning on the bucket
    aws s3api put-bucket-versioning \
        --bucket "$BUCKET_NAME" \
        --versioning-configuration Status=Enabled
    
    # Create DynamoDB table for state locking
    print_status "Creating DynamoDB table: $TABLE_NAME"
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
        --region "$AWS_REGION" || {
        print_warning "DynamoDB table creation failed, it might already exist"
    }
    
    # Create backend configuration
    if [[ ! -f "backend.tf" ]]; then
        print_status "Creating backend configuration..."
        cat > backend.tf << EOF
terraform {
  backend "s3" {
    bucket         = "$BUCKET_NAME"
    key            = "d-summoner-story/terraform.tfstate"
    region         = "$AWS_REGION"
    dynamodb_table = "$TABLE_NAME"
    encrypt        = true
  }
}
EOF
        print_success "Backend configuration created"
    else
        print_warning "backend.tf already exists, skipping creation"
    fi
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure for environment: $ENVIRONMENT"
    
    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init
    
    # Validate configuration
    print_status "Validating Terraform configuration..."
    terraform validate
    
    # Plan deployment
    print_status "Planning deployment..."
    terraform plan \
        -var="environment=$ENVIRONMENT" \
        -var="aws_region=$AWS_REGION" \
        -out=tfplan
    
    # Ask for confirmation
    echo
    read -p "Do you want to apply these changes? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled by user"
        exit 0
    fi
    
    # Apply changes
    print_status "Applying Terraform configuration..."
    terraform apply tfplan
    
    print_success "Infrastructure deployment completed!"
}

# Function to configure secrets
configure_secrets() {
    if [[ -z "$RIOT_API_KEY" ]]; then
        echo
        read -p "Enter your Riot Games API key (or press Enter to skip): " RIOT_API_KEY
    fi
    
    if [[ -n "$RIOT_API_KEY" ]]; then
        print_status "Updating Riot API key in Secrets Manager..."
        
        SECRET_ARN=$(terraform output -raw riot_api_secret_arn)
        aws secretsmanager update-secret \
            --secret-id "$SECRET_ARN" \
            --secret-string "{\"api_key\":\"$RIOT_API_KEY\"}"
        
        print_success "Riot API key updated successfully"
    else
        print_warning "Riot API key not provided. Update it manually later:"
        echo "aws secretsmanager update-secret --secret-id \$(terraform output -raw riot_api_secret_arn) --secret-string '{\"api_key\":\"YOUR_KEY_HERE\"}'"
    fi
}

# Function to display deployment information
show_deployment_info() {
    print_success "Deployment Summary"
    echo "===================="
    echo
    echo "API Endpoint: $(terraform output -raw api_endpoint)"
    echo "Website URL: $(terraform output -raw website_url)"
    echo "CloudWatch Dashboard: $(terraform output -raw cloudwatch_dashboard_url)"
    echo
    echo "Next steps:"
    echo "1. Deploy your frontend to: $(terraform output -raw static_website_bucket_name)"
    echo "2. Subscribe to alerts: aws sns subscribe --topic-arn $(terraform output -raw sns_alerts_topic_arn) --protocol email --notification-endpoint your-email@example.com"
    echo "3. Monitor your application via the CloudWatch dashboard"
    echo
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -e, --environment ENV     Deployment environment (default: dev)"
    echo "  -r, --region REGION       AWS region (default: us-east-1)"
    echo "  -k, --riot-key KEY        Riot Games API key"
    echo "  --skip-backend            Skip remote backend setup"
    echo "  -h, --help                Show this help message"
    echo
    echo "Examples:"
    echo "  $0                                    # Deploy to dev environment"
    echo "  $0 -e prod -r us-west-2             # Deploy to prod in us-west-2"
    echo "  $0 -k RGAPI-xxx --skip-backend      # Deploy with API key, skip backend setup"
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
        -k|--riot-key)
            RIOT_API_KEY="$2"
            shift 2
            ;;
        --skip-backend)
            SKIP_BACKEND_SETUP=true
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
    print_status "Starting D-Summoner-Story infrastructure deployment"
    print_status "Environment: $ENVIRONMENT"
    print_status "AWS Region: $AWS_REGION"
    echo
    
    check_prerequisites
    setup_backend
    deploy_infrastructure
    configure_secrets
    show_deployment_info
    
    print_success "All done! Your League of Legends Year in Review infrastructure is ready."
}

# Run main function
main