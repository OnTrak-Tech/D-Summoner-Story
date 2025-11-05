# D-Summoner-Story

League of Legends Year in Review - A serverless application that analyzes player performance data and generates AI-powered insights with interactive visualizations.

## Architecture Overview

### System Components
- **Backend**: 5 Python Lambda functions handling data processing and AI generation
- **Frontend**: React application with TypeScript, D3.js, and Chart.js
- **Infrastructure**: Terraform-managed AWS serverless stack
- **CI/CD**: GitHub Actions for automated testing and deployment

### Data Processing Workflow

1. **data_fetcher.py**
   - Accepts summoner name and region via API Gateway
   - Fetches summoner info from Riot API
   - Retrieves match history (up to 100 matches)
   - Stores raw match data in S3
   - Invokes data_processor asynchronously

2. **data_processor.py**
   - Processes raw match data from S3
   - Calculates statistics (KDA, win rates, champion performance)
   - Identifies trends and behavioral patterns
   - Stores processed statistics in DynamoDB
   - Triggers insight_generator

3. **insight_generator.py**
   - Loads processed statistics from DynamoDB
   - Generates AI narrative using AWS Bedrock (Claude)
   - Creates highlights and recommendations
   - Performs advanced analytics (personality profiling, predictions)
   - Stores insights in S3

4. **recap_server.py**
   - Serves aggregated data to frontend
   - Handles interactive Q&A requests
   - Provides chart configurations
   - Manages sharing functionality

5. **Frontend Application**
   - Displays interactive dashboard with multiple visualization types
   - Champion Mastery Constellation using D3.js force simulation
   - Real-time AI chat interface
   - Social sharing with image generation

## Implementation Steps

### Prerequisites
- AWS CLI configured with appropriate permissions
- Terraform >= 1.0
- Python 3.12
- Node.js 18+
- Riot Games API key

### 1. Infrastructure Deployment

```bash
# Navigate to infrastructure directory
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Deploy infrastructure
terraform apply

# Store Riot API key in Secrets Manager
aws secretsmanager create-secret --name "riot-api-key" --secret-string '{"api_key":"your-riot-api-key"}'
```

### 2. Backend Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Run tests
pytest backend/tests/ -v

# Deploy Lambda functions
cd infrastructure/terraform
terraform apply -target=aws_lambda_function
```

### 3. Frontend Development

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Deploy to S3
aws s3 sync dist/ s3://your-bucket-name/
```

## Configuration and Security

### Environment Variables

**GitHub Repository Secrets:**
```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

**Lambda Environment Variables:**
```
PLAYER_STATS_TABLE=d-summoner-story-player-stats
RAW_MATCH_DATA_BUCKET=d-summoner-story-raw-match-data
PROCESSED_INSIGHTS_BUCKET=d-summoner-story-processed-insights
RIOT_API_SECRET_NAME=riot-api-key
```

### Security Implementation

**IAM Policies:**
- Lambda execution roles with minimal required permissions
- S3 bucket policies restricting access to specific functions
- DynamoDB table policies for read/write operations
- Secrets Manager access for API key retrieval

**Data Encryption:**
- S3 buckets encrypted with AES-256
- DynamoDB tables encrypted at rest
- API Gateway with SSL/TLS termination
- CloudFront distribution with HTTPS redirect

### Monitoring and Logging

**CloudWatch Configuration:**
```bash
# Lambda function logs
/aws/lambda/data-fetcher
/aws/lambda/data-processor
/aws/lambda/insight-generator
/aws/lambda/recap-server

# API Gateway logs
/aws/apigateway/d-summoner-story-api
```

**Alarms and Metrics:**
- Lambda function duration and error rates
- API Gateway 4xx/5xx error rates
- DynamoDB throttling and capacity metrics
- S3 request metrics and error rates

## Technical Implementation Details

### Backend Architecture

**Shared Modules (`backend/src/shared/`):**
- `models.py`: Pydantic data models for type safety
- `aws_clients.py`: Boto3 client wrappers with error handling
- `riot_client.py`: Riot API integration with rate limiting
- `utils.py`: Common utilities and analytics functions

**Lambda Functions:**

1. **data_fetcher.py**
   - API Gateway integration with CORS support
   - Async match history processing to handle API Gateway timeout
   - Error handling for invalid summoner names and regions
   - S3 storage with organized key structure

2. **data_processor.py**
   - Statistical analysis algorithms for performance metrics
   - Champion performance aggregation and ranking
   - Monthly trend calculation and smoothing
   - Behavioral pattern identification

3. **insight_generator.py**
   - AWS Bedrock integration with Claude Haiku model
   - Prompt engineering for narrative generation
   - Advanced analytics: personality profiling, predictions
   - Structured output formatting for frontend consumption

4. **recap_server.py**
   - RESTful API endpoints for data retrieval
   - Interactive Q&A using Bedrock for real-time responses
   - Chart.js configuration generation
   - Social sharing URL generation

### Frontend Architecture

**Core Components:**
- `RecapViewer.tsx`: Main dashboard with tabbed interface
- `StatisticsCharts.tsx`: Chart.js integration with multiple chart types
- `ChampionConstellation.tsx`: D3.js force simulation visualization
- `ShareModal.tsx`: Social sharing with canvas-based image generation

**Key Features:**
- Champion Mastery Constellation with physics-based positioning
- Interactive tooltips and drag functionality
- Role-based clustering and connection algorithms
- Responsive design with mobile optimization

**State Management:**
- React hooks for component state
- Local storage for user preferences
- API service layer with error handling
- Loading states and user feedback

### Data Models

**Core Data Structures:**
```python
class ProcessedStats(BaseModel):
    summoner_name: str
    region: str
    total_games: int
    win_rate: float
    avg_kda: float
    champion_stats: List[ChampionStats]
    monthly_trends: List[MonthlyTrend]
    highlight_matches: List[HighlightMatch]
    behavioral_patterns: List[BehavioralPattern]
    personality_profile: Dict[str, Any]
```

**API Response Format:**
```json
{
  "session_id": "uuid",
  "summoner_name": "string",
  "region": "string",
  "narrative": "string",
  "statistics": {},
  "visualizations": [],
  "highlights": [],
  "achievements": []
}
```

## Testing and Validation

### Backend Testing
```bash
# Unit tests for Lambda functions
pytest backend/tests/test_data_processor.py -v
pytest backend/tests/test_insight_generator.py -v

# Integration tests with mocked AWS services
pytest backend/tests/integration/ -v

# Load testing with sample data
python backend/tests/load_test.py
```

### Frontend Testing
```bash
# Component testing
npm test

# End-to-end testing
npm run test:e2e

# Build verification
npm run build && npm run preview
```

### Performance Optimization

**Backend Optimizations:**
- Lambda cold start reduction with provisioned concurrency
- DynamoDB query optimization with proper indexing
- S3 object lifecycle policies for cost management
- Bedrock request batching for AI operations

**Frontend Optimizations:**
- Code splitting with dynamic imports
- Image optimization and lazy loading
- Local storage caching for API responses
- Bundle size optimization with tree shaking

## Deployment Pipeline

### CI/CD Workflow

1. **Pull Request Validation:**
   - Backend unit tests and linting
   - Frontend build verification
   - Terraform plan validation

2. **Main Branch Deployment:**
   - Infrastructure updates via Terraform
   - Lambda function deployment with versioning
   - Frontend build and S3 sync
   - CloudFront cache invalidation

3. **Post-Deployment Verification:**
   - Health check endpoints
   - Integration test suite
   - Performance monitoring alerts

### Rollback Strategy

```bash
# Lambda function rollback
aws lambda update-function-code --function-name data-fetcher --s3-bucket deployment-bucket --s3-key previous-version.zip

# Frontend rollback
aws s3 sync s3://backup-bucket/ s3://production-bucket/
aws cloudfront create-invalidation --distribution-id DISTRIBUTION_ID --paths "/*"
```

## Troubleshooting

### Common Issues

**Lambda Timeout Errors:**
- Check CloudWatch logs for execution duration
- Verify API Gateway timeout settings (30s max)
- Implement async processing for long-running operations

**Riot API Rate Limiting:**
- Monitor rate limit headers in responses
- Implement exponential backoff retry logic
- Use development API key limits appropriately

**Frontend Build Failures:**
- Verify Node.js version compatibility
- Check for TypeScript compilation errors
- Ensure all dependencies are properly installed

### Monitoring and Alerts

**Key Metrics to Monitor:**
- Lambda function error rates and duration
- API Gateway request latency and error codes
- DynamoDB read/write capacity utilization
- S3 request metrics and storage costs
- CloudFront cache hit ratios

**Alert Thresholds:**
- Lambda error rate > 5%
- API response time > 10 seconds
- DynamoDB throttling events
- S3 4xx/5xx error rate > 1%