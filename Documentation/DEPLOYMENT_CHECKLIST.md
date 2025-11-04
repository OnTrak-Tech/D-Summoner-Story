# D-Summoner-Story Deployment Checklist

Complete checklist for deploying the League of Legends Year in Review infrastructure.

## Pre-Deployment Requirements

###  Prerequisites
- [ ] AWS CLI installed and configured
- [ ] Terraform >= 1.6.0 installed
- [ ] Python 3.12 for Lambda packaging
- [ ] Node.js 18+ for frontend development
- [ ] Git repository access
- [ ] Riot Games Developer Account

###  AWS Account Setup
- [ ] AWS account with appropriate permissions
- [ ] IAM user with deployment permissions
- [ ] AWS region selected (recommended: us-east-1)
- [ ] Billing alerts configured (optional)

###  API Keys and Secrets
- [ ] Riot Games API key obtained from [developer.riotgames.com](https://developer.riotgames.com/)
- [ ] API key tested with Riot API endpoints
- [ ] Email address for monitoring alerts

## Infrastructure Deployment

### Step 1: Initial Setup
```bash
# Clone repository and navigate to infrastructure
cd infrastructure/terraform

# Review configuration
cat README.md
cat BEDROCK_SETUP.md

# Check prerequisites
make help
```

### Step 2: Deploy Infrastructure
```bash
# Option A: Automated deployment
make full-setup ENV=dev REGION=us-east-1

# Option B: Manual deployment
make deploy ENV=dev
```

### Step 3: Validate Deployment
```bash
# Run comprehensive validation
make validate ENV=dev

# Check specific components
make status ENV=dev
make output ENV=dev
```

## Post-Deployment Configuration

### Step 4: Configure Secrets
```bash
# Update Riot API key
make update-secret API_KEY=RGAPI-your-actual-key-here

# Verify secret update
aws secretsmanager get-secret-value \
  --secret-id $(terraform output -raw riot_api_secret_arn) \
  --query SecretString --output text
```

### Step 5: Set Up Bedrock Access
```bash
# Check Bedrock availability
make bedrock-check REGION=us-east-1

# Follow setup guide for model access
make bedrock-setup

# Manual steps in AWS Console:
# 1. Go to Amazon Bedrock Console
# 2. Navigate to Model access
# 3. Request access to Claude 3 Sonnet
# 4. Wait for approval (usually < 24 hours)
```

### Step 6: Configure Monitoring
```bash
# Subscribe to alerts
make setup-alerts EMAIL=your-email@example.com

# Open monitoring dashboard
make dashboard ENV=dev

# Test log streaming
make tail-auth ENV=dev
```

## Application Deployment

### Step 7: Deploy Backend Code
```bash
# Backend code is automatically packaged with Terraform
# Verify Lambda functions are deployed
aws lambda list-functions --query 'Functions[?contains(FunctionName, `d-summoner-story-dev`)].FunctionName'
```

### Step 8: Deploy Frontend
```bash
# Build and deploy React frontend
cd ../../frontend
npm install
npm run build

# Deploy to S3
BUCKET_NAME=$(cd ../infrastructure/terraform && terraform output -raw static_website_bucket_name)
aws s3 sync dist/ s3://$BUCKET_NAME/

# Invalidate CloudFront cache
DISTRIBUTION_ID=$(cd ../infrastructure/terraform && terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"
```

### Step 9: Test End-to-End
```bash
# Get application URLs
cd infrastructure/terraform
echo "Website URL: $(terraform output -raw website_url)"
echo "API Endpoint: $(terraform output -raw api_endpoint)"

# Test API endpoints
API_ENDPOINT=$(terraform output -raw api_endpoint)
curl -X POST "$API_ENDPOINT/api/v1/auth" \
  -H "Content-Type: application/json" \
  -d '{"summoner_name":"test","region":"na1"}'
```

## Verification Checklist

###  Infrastructure Components
- [ ] S3 buckets created and accessible
- [ ] DynamoDB tables created with TTL enabled
- [ ] Lambda functions deployed and configured
- [ ] API Gateway endpoints responding
- [ ] CloudFront distribution active
- [ ] Secrets Manager secret configured
- [ ] CloudWatch dashboard accessible
- [ ] SNS alerts configured

###  Security Configuration
- [ ] S3 buckets have public access blocked
- [ ] IAM roles follow least privilege principle
- [ ] Secrets stored in AWS Secrets Manager
- [ ] CloudFront enforces HTTPS
- [ ] API Gateway has CORS configured

###  Monitoring Setup
- [ ] CloudWatch logs collecting data
- [ ] CloudWatch alarms configured
- [ ] SNS topic has email subscription
- [ ] Dashboard shows real-time metrics
- [ ] Cost monitoring alerts active

###  Bedrock Integration
- [ ] Bedrock service available in region
- [ ] Claude 3 Sonnet model access granted
- [ ] Lambda functions have Bedrock permissions
- [ ] Test API call successful

###  Application Testing
- [ ] Frontend loads successfully
- [ ] API endpoints return expected responses
- [ ] Error handling works correctly
- [ ] Monitoring captures metrics
- [ ] End-to-end user flow functional

## Troubleshooting

### Common Issues and Solutions

#### 1. Terraform Deployment Fails
```bash
# Check AWS credentials
aws sts get-caller-identity

# Validate Terraform configuration
terraform validate

# Check for resource conflicts
terraform plan
```

#### 2. Lambda Functions Not Working
```bash
# Check function logs
make tail-auth ENV=dev

# Verify IAM permissions
aws lambda get-policy --function-name d-summoner-story-dev-auth

# Test function directly
aws lambda invoke --function-name d-summoner-story-dev-auth \
  --payload '{"test": true}' /tmp/response.json
```

#### 3. Bedrock Access Denied
```bash
# Check model access status
aws bedrock list-foundation-models --region us-east-1

# Verify IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) \
  --action-names bedrock:InvokeModel \
  --resource-arns "*"
```

#### 4. CloudFront Not Serving Content
```bash
# Check distribution status
aws cloudfront get-distribution --id $(terraform output -raw cloudfront_distribution_id)

# Verify S3 bucket policy
aws s3api get-bucket-policy --bucket $(terraform output -raw static_website_bucket_name)

# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

#### 5. API Gateway Errors
```bash
# Check API Gateway logs
aws logs tail /aws/apigateway/$(terraform output -raw api_endpoint | cut -d'/' -f3) --follow

# Test API connectivity
curl -v $(terraform output -raw api_endpoint)/api/v1/auth
```

## Maintenance Tasks

### Regular Maintenance
- [ ] Monitor AWS costs weekly
- [ ] Review CloudWatch alarms monthly
- [ ] Update Lambda function code as needed
- [ ] Rotate Riot API key if required
- [ ] Check Bedrock model availability

### Scaling Considerations
- [ ] Monitor DynamoDB capacity usage
- [ ] Review Lambda timeout and memory settings
- [ ] Check S3 storage costs and lifecycle policies
- [ ] Evaluate CloudFront cache hit ratios

### Security Updates
- [ ] Review IAM policies quarterly
- [ ] Update Lambda runtime versions
- [ ] Monitor AWS security bulletins
- [ ] Audit access logs regularly

## Environment Management

### Development Environment
```bash
# Deploy to dev
make deploy ENV=dev

# Quick testing
make validate ENV=dev
```

### Staging Environment
```bash
# Deploy to staging
make deploy ENV=staging

# Run integration tests
# (Add your test commands here)
```

### Production Environment
```bash
# Deploy to production (with extra caution)
make deploy ENV=prod

# Verify production deployment
make validate ENV=prod

# Monitor production metrics
make dashboard ENV=prod
```

## Cleanup and Teardown

### Temporary Cleanup
```bash
# Clean local Terraform files
make clean

# Remove old Lambda deployment packages
rm -rf .terraform/modules/*/build/
```

### Complete Environment Teardown
```bash
# Destroy specific environment
make destroy ENV=dev

# Or use the destroy script with confirmation
./destroy.sh -e dev -r us-east-1
```

## Support and Documentation

### Additional Resources
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Riot Games API Documentation](https://developer.riotgames.com/docs/lol)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Project GitHub Repository](https://github.com/your-org/d-summoner-story)

### Getting Help
1. Check the troubleshooting section above
2. Review CloudWatch logs for error details
3. Validate infrastructure with `make validate`
4. Check AWS service health dashboards
5. Consult project documentation and README files

---

**Deployment Date**: ___________  
**Deployed By**: ___________  
**Environment**: ___________  
**Version**: ___________  

**Notes**:
_Use this space for deployment-specific notes, issues encountered, or customizations made._