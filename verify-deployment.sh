#!/bin/bash

# Deployment Verification Script
# Verifies that all components are working correctly after deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Check if required tools are available
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    for tool in curl jq terraform; do
        if command -v $tool &> /dev/null; then
            print_success "$tool is available"
        else
            print_error "$tool is not installed"
            exit 1
        fi
    done
}

# Verify Terraform deployment
verify_terraform() {
    print_header "Verifying Terraform Deployment"
    
    cd infrastructure/terraform
    
    # Check if Terraform state exists
    if terraform show &>/dev/null; then
        print_success "Terraform state is valid"
    else
        print_error "Terraform state not found or invalid"
        return 1
    fi
    
    # Get outputs
    API_ENDPOINT=$(terraform output -raw api_endpoint 2>/dev/null || echo "")
    WEBSITE_URL=$(terraform output -raw website_url 2>/dev/null || echo "")
    
    if [[ -n "$API_ENDPOINT" ]]; then
        print_success "API endpoint: $API_ENDPOINT"
    else
        print_error "API endpoint not found"
    fi
    
    if [[ -n "$WEBSITE_URL" ]]; then
        print_success "Website URL: $WEBSITE_URL"
    else
        print_error "Website URL not found"
    fi
    
    cd ../..
}

# Test API endpoints
test_api() {
    print_header "Testing API Endpoints"
    
    if [[ -z "$API_ENDPOINT" ]]; then
        print_error "API endpoint not available for testing"
        return 1
    fi
    
    # Test auth endpoint
    print_status "Testing auth endpoint..."
    AUTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/auth_response.json \
        -X POST "$API_ENDPOINT/api/v1/auth" \
        -H "Content-Type: application/json" \
        -d '{"summoner_name":"TestSummoner","region":"na1"}' || echo "000")
    
    if [[ "$AUTH_RESPONSE" == "200" ]]; then
        print_success "Auth endpoint responding correctly"
        SESSION_ID=$(jq -r '.session_id' /tmp/auth_response.json 2>/dev/null || echo "")
        if [[ -n "$SESSION_ID" ]]; then
            print_success "Session ID generated: ${SESSION_ID:0:8}..."
        fi
    else
        print_warning "Auth endpoint returned status: $AUTH_RESPONSE (expected for invalid summoner)"
    fi
    
    # Clean up
    rm -f /tmp/auth_response.json
}

# Test website accessibility
test_website() {
    print_header "Testing Website Accessibility"
    
    if [[ -z "$WEBSITE_URL" ]]; then
        print_error "Website URL not available for testing"
        return 1
    fi
    
    print_status "Testing website accessibility..."
    WEBSITE_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$WEBSITE_URL" || echo "000")
    
    if [[ "$WEBSITE_RESPONSE" == "200" ]]; then
        print_success "Website is accessible"
    else
        print_warning "Website returned status: $WEBSITE_RESPONSE (CloudFront may still be deploying)"
    fi
}

# Check AWS resources
check_aws_resources() {
    print_header "Checking AWS Resources"
    
    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity &>/dev/null; then
        print_error "AWS CLI not configured"
        return 1
    fi
    
    print_success "AWS CLI is configured"
    
    # Check S3 buckets
    cd infrastructure/terraform
    RAW_BUCKET=$(terraform output -raw raw_data_bucket_name 2>/dev/null || echo "")
    WEBSITE_BUCKET=$(terraform output -raw static_website_bucket_name 2>/dev/null || echo "")
    
    if [[ -n "$RAW_BUCKET" ]] && aws s3 ls "s3://$RAW_BUCKET" &>/dev/null; then
        print_success "Raw data bucket exists: $RAW_BUCKET"
    else
        print_error "Raw data bucket not accessible"
    fi
    
    if [[ -n "$WEBSITE_BUCKET" ]] && aws s3 ls "s3://$WEBSITE_BUCKET" &>/dev/null; then
        print_success "Website bucket exists: $WEBSITE_BUCKET"
        
        # Check if frontend is deployed
        if aws s3 ls "s3://$WEBSITE_BUCKET/index.html" &>/dev/null; then
            print_success "Frontend is deployed to S3"
        else
            print_warning "Frontend not found in S3 bucket"
        fi
    else
        print_error "Website bucket not accessible"
    fi
    
    cd ../..
}

# Generate summary report
generate_summary() {
    print_header "Deployment Verification Summary"
    
    echo -e "\n${GREEN}✅ Deployment Status${NC}"
    echo "Timestamp: $(date)"
    
    if [[ -n "$API_ENDPOINT" ]]; then
        echo "🔗 API Endpoint: $API_ENDPOINT"
    fi
    
    if [[ -n "$WEBSITE_URL" ]]; then
        echo "🌐 Website URL: $WEBSITE_URL"
    fi
    
    echo ""
    echo "Next steps:"
    echo "1. Test the application with a real summoner name"
    echo "2. Verify all features work as expected"
    echo "3. Check mobile responsiveness"
    echo "4. Test social sharing functionality"
    echo "5. Monitor CloudWatch for any errors"
}

# Main execution
main() {
    echo -e "${BLUE}D-Summoner-Story Deployment Verification${NC}"
    echo "========================================"
    
    check_prerequisites
    verify_terraform
    test_api
    test_website
    check_aws_resources
    generate_summary
    
    echo -e "\n${GREEN}Verification completed!${NC}"
}

# Show usage if help requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: $0"
    echo ""
    echo "This script verifies that the D-Summoner-Story application"
    echo "has been deployed correctly and all components are working."
    echo ""
    echo "Prerequisites:"
    echo "- AWS CLI configured with appropriate credentials"
    echo "- Terraform state available in infrastructure/terraform/"
    echo "- curl and jq installed"
    exit 0
fi

# Run main function
main