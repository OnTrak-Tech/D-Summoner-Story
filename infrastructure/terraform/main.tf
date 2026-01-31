###############################################
# Root composition using Terraform modules
###############################################

locals {
  name_prefix = lower(replace("${var.project_name}-${var.environment}", " ", "-"))
  common_tags = merge(var.tags, {
    Project     = var.project_name,
    Environment = var.environment,
    ManagedBy   = "terraform"
  })
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# S3 buckets
module "s3_raw_data" {
  source                      = "./modules/s3_bucket"
  bucket_name                 = "${local.name_prefix}-raw-data"
  versioning_enabled          = true
  transition_to_ia_after_days = 30
  expire_after_days           = 365
  tags                        = local.common_tags

  # Event-driven: trigger data_processor when new raw data is uploaded
  lambda_notifications = [
    {
      lambda_function_arn = module.lambda_data_processor.lambda_arn
      events              = ["s3:ObjectCreated:*"]
      filter_prefix       = "raw/"
      filter_suffix       = ".json"
    }
  ]
}

module "s3_processed_insights" {
  source                      = "./modules/s3_bucket"
  bucket_name                 = "${local.name_prefix}-processed-insights"
  versioning_enabled          = true
  transition_to_ia_after_days = 30
  expire_after_days           = 365
  tags                        = local.common_tags
}

module "s3_static_website" {
  source             = "./modules/s3_bucket"
  bucket_name        = "${local.name_prefix}-website"
  versioning_enabled = true
  tags               = local.common_tags
}

# DynamoDB tables
module "ddb_player_stats" {
  source     = "./modules/dynamodb_table"
  table_name = "${local.name_prefix}-player-stats"
  hash_key   = "PK"
  range_key  = "SK"
  attributes = [
    { name = "PK", type = "S" },
    { name = "SK", type = "S" }
  ]
  ttl_enabled            = true
  ttl_attribute_name     = "ttl"
  billing_mode           = "PAY_PER_REQUEST"
  point_in_time_recovery = true
  tags                   = local.common_tags
}

module "ddb_processing_jobs" {
  source     = "./modules/dynamodb_table"
  table_name = "${local.name_prefix}-processing-jobs"
  hash_key   = "PK"
  attributes = [
    { name = "PK", type = "S" }
  ]
  ttl_enabled            = true
  ttl_attribute_name     = "ttl"
  billing_mode           = "PAY_PER_REQUEST"
  point_in_time_recovery = true
  tags                   = local.common_tags

  # Event-driven: stream changes to trigger insight_generator
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"
}

###############################################
# SQS Queue for Insight Generation
###############################################

module "sqs_insight_queue" {
  source     = "./modules/sqs_queue"
  queue_name = "${local.name_prefix}-insight-queue"

  # Match Lambda timeout (180s) + buffer
  visibility_timeout_seconds    = 300
  message_retention_seconds     = 86400 # 1 day
  max_receive_count             = 3
  create_dlq                    = true
  dlq_message_retention_seconds = 1209600 # 14 days

  tags = local.common_tags
}

###############################################
# Bedrock Models (Optional - for reference only)
###############################################

module "bedrock_models" {
  source = "./modules/bedrock_models"
}

###############################################
# SSM Parameter Store (replaces Secrets Manager - FREE)
###############################################

module "ssm_parameters" {
  source       = "./modules/ssm_parameters"
  project_name = var.project_name
  environment  = var.environment
  common_tags  = local.common_tags

  parameters = {
    # Platform API Keys
    "riot-api-key" = {
      description = "Riot Games API key for League of Legends data access"
      type        = "SecureString"
      value       = "PLACEHOLDER_RIOT_API_KEY"
    }
    "steam-api-key" = {
      description = "Steam Web API key"
      type        = "SecureString"
      value       = "PLACEHOLDER_STEAM_API_KEY"
    }
    "xbox-client-id" = {
      description = "Xbox/Microsoft OAuth client ID"
      type        = "SecureString"
      value       = "PLACEHOLDER_XBOX_CLIENT_ID"
    }
    "xbox-client-secret" = {
      description = "Xbox/Microsoft OAuth client secret"
      type        = "SecureString"
      value       = "PLACEHOLDER_XBOX_CLIENT_SECRET"
    }

    # AI Provider
    "gemini-api-key" = {
      description = "Google Gemini API key for AI insights"
      type        = "SecureString"
      value       = "PLACEHOLDER_GEMINI_API_KEY"
    }

    # Firebase (for token validation)
    "firebase-project-id" = {
      description = "Firebase project ID for auth validation"
      type        = "String"
      value       = "PLACEHOLDER_FIREBASE_PROJECT_ID"
    }
  }
}

###############################################
# IAM Policies for Lambda Functions
###############################################

# DynamoDB access policy
resource "aws_iam_policy" "lambda_dynamodb" {
  name        = "${local.name_prefix}-lambda-dynamodb"
  description = "DynamoDB access for Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          module.ddb_player_stats.table_arn,
          module.ddb_processing_jobs.table_arn,
          "${module.ddb_player_stats.table_arn}/*",
          "${module.ddb_processing_jobs.table_arn}/*"
        ]
      }
    ]
  })
}

# S3 access policy
resource "aws_iam_policy" "lambda_s3" {
  name        = "${local.name_prefix}-lambda-s3"
  description = "S3 access for Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.s3_raw_data.bucket_arn,
          "${module.s3_raw_data.bucket_arn}/*",
          module.s3_processed_insights.bucket_arn,
          "${module.s3_processed_insights.bucket_arn}/*"
        ]
      }
    ]
  })
}

# SSM Parameter Store access policy
resource "aws_iam_policy" "lambda_ssm" {
  name        = "${local.name_prefix}-lambda-ssm"
  description = "SSM Parameter Store access for Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = [
          "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.project_name}/${var.environment}/*"
        ]
      }
    ]
  })
}

# Bedrock access policy
resource "aws_iam_policy" "lambda_bedrock" {
  name        = "${local.name_prefix}-lambda-bedrock"
  description = "Amazon Bedrock access for Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "aws-marketplace:ViewSubscriptions",
          "aws-marketplace:Subscribe"
        ]
        Resource = "*"
      }
    ]
  })
}


# Lambda invoke policy
resource "aws_iam_policy" "lambda_invoke" {
  name        = "${local.name_prefix}-lambda-invoke"
  description = "Lambda invoke access for Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          module.lambda_data_fetcher.lambda_arn,
          module.lambda_data_processor.lambda_arn,
          module.lambda_insight_generator.lambda_arn
        ]
      }
    ]
  })
}

# DynamoDB Streams access policy for event-driven Lambda
resource "aws_iam_policy" "lambda_dynamodb_streams" {
  name        = "${local.name_prefix}-lambda-dynamodb-streams"
  description = "DynamoDB Streams access for event-driven Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:DescribeStream",
          "dynamodb:ListStreams"
        ]
        Resource = [
          module.ddb_processing_jobs.stream_arn
        ]
      }
    ]
  })
}

# SQS access policy for Lambda functions
resource "aws_iam_policy" "lambda_sqs" {
  name        = "${local.name_prefix}-lambda-sqs"
  description = "SQS access for Lambda functions - insight queue"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl"
        ]
        Resource = [
          module.sqs_insight_queue.queue_arn,
          module.sqs_insight_queue.dlq_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = [
          module.sqs_insight_queue.queue_arn
        ]
      }
    ]
  })
}

###############################################
# Lambda Layer for Shared Modules
###############################################

# Lambda Layer for shared modules
data "archive_file" "shared_layer" {
  type        = "zip"
  source_dir  = "${path.module}/layer"
  output_path = "${path.module}/build/shared-layer.zip"
}

resource "aws_lambda_layer_version" "shared" {
  filename         = data.archive_file.shared_layer.output_path
  layer_name       = "${local.name_prefix}-shared"
  source_code_hash = data.archive_file.shared_layer.output_base64sha256

  compatible_runtimes = ["python3.12"]
  description         = "Shared modules for League of Legends recap Lambda functions"
}

###############################################
# Lambda Functions
###############################################

module "lambda_auth" {
  source        = "./modules/lambda_function"
  function_name = "${local.name_prefix}-auth"
  handler       = "auth_handler.handler"
  source_dir    = "${path.root}/../../backend/src/lambdas"
  runtime       = "python3.12"
  timeout       = 10
  memory_size   = 256
  layers        = [aws_lambda_layer_version.shared.arn]
  environment = {
    LOG_LEVEL             = "INFO"
    PLAYER_STATS_TABLE    = module.ddb_player_stats.table_name
    PROCESSING_JOBS_TABLE = module.ddb_processing_jobs.table_name
  }
  policy_arns = [
    aws_iam_policy.lambda_dynamodb.arn
  ]
}

module "lambda_data_fetcher" {
  source        = "./modules/lambda_function"
  function_name = "${local.name_prefix}-data-fetcher"
  handler       = "data_fetcher.handler"
  source_dir    = "${path.root}/../../backend/src/lambdas"
  runtime       = "python3.12"
  timeout       = 300
  memory_size   = 512
  layers        = [aws_lambda_layer_version.shared.arn]
  environment = {
    LOG_LEVEL                    = "INFO"
    RAW_DATA_BUCKET              = module.s3_raw_data.bucket_name
    PROCESSING_JOBS_TABLE        = module.ddb_processing_jobs.table_name
    SSM_PATH_PREFIX              = module.ssm_parameters.ssm_path_prefix
    DATA_PROCESSOR_FUNCTION_NAME = module.lambda_data_processor.function_name
  }
  policy_arns = [
    aws_iam_policy.lambda_dynamodb.arn,
    aws_iam_policy.lambda_s3.arn,
    aws_iam_policy.lambda_ssm.arn,
    aws_iam_policy.lambda_invoke.arn
  ]
}

# Lambda Authorizer for Firebase token validation
module "lambda_authorizer" {
  source        = "./modules/lambda_function"
  function_name = "${local.name_prefix}-authorizer"
  handler       = "authorizer.handler"
  source_dir    = "${path.root}/../../backend/src/lambdas"
  runtime       = "python3.12"
  timeout       = 10
  memory_size   = 256
  layers        = [aws_lambda_layer_version.shared.arn]
  environment = {
    LOG_LEVEL       = "INFO"
    SSM_PATH_PREFIX = module.ssm_parameters.ssm_path_prefix
  }
  policy_arns = [
    aws_iam_policy.lambda_ssm.arn
  ]
}

# Platform Auth Handlers
module "lambda_auth_riot" {
  source        = "./modules/lambda_function"
  function_name = "${local.name_prefix}-auth-riot"
  handler       = "auth_riot.handler"
  source_dir    = "${path.root}/../../backend/src/lambdas"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 256
  layers        = [aws_lambda_layer_version.shared.arn]
  environment = {
    LOG_LEVEL          = "INFO"
    SSM_PATH_PREFIX    = module.ssm_parameters.ssm_path_prefix
    PLAYER_STATS_TABLE = module.ddb_player_stats.table_name
  }
  policy_arns = [
    aws_iam_policy.lambda_ssm.arn,
    aws_iam_policy.lambda_dynamodb.arn
  ]
}

module "lambda_auth_fortnite" {
  source        = "./modules/lambda_function"
  function_name = "${local.name_prefix}-auth-fortnite"
  handler       = "auth_fortnite.handler"
  source_dir    = "${path.root}/../../backend/src/lambdas"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 256
  layers        = [aws_lambda_layer_version.shared.arn]
  environment = {
    LOG_LEVEL          = "INFO"
    SSM_PATH_PREFIX    = module.ssm_parameters.ssm_path_prefix
    PLAYER_STATS_TABLE = module.ddb_player_stats.table_name
  }
  policy_arns = [
    aws_iam_policy.lambda_ssm.arn,
    aws_iam_policy.lambda_dynamodb.arn
  ]
}

module "lambda_data_processor" {
  source        = "./modules/lambda_function"
  function_name = "${local.name_prefix}-data-processor"
  handler       = "data_processor.handler"
  source_dir    = "${path.root}/../../backend/src/lambdas"
  runtime       = "python3.12"
  timeout       = 300
  memory_size   = 1024
  layers        = [aws_lambda_layer_version.shared.arn]
  environment = {
    LOG_LEVEL                       = "INFO"
    RAW_DATA_BUCKET                 = module.s3_raw_data.bucket_name
    PLAYER_STATS_TABLE              = module.ddb_player_stats.table_name
    PROCESSING_JOBS_TABLE           = module.ddb_processing_jobs.table_name
    INSIGHT_GENERATOR_FUNCTION_NAME = module.lambda_insight_generator.function_name
  }
  policy_arns = [
    aws_iam_policy.lambda_dynamodb.arn,
    aws_iam_policy.lambda_s3.arn,
    aws_iam_policy.lambda_invoke.arn
  ]
}

module "lambda_insight_generator" {
  source        = "./modules/lambda_function"
  function_name = "${local.name_prefix}-insight-generator"
  handler       = "insight_generator.handler"
  source_dir    = "${path.root}/../../backend/src/lambdas"
  runtime       = "python3.12"
  timeout       = 180
  memory_size   = 512
  layers        = [aws_lambda_layer_version.shared.arn]
  environment = {
    LOG_LEVEL                 = "INFO"
    PLAYER_STATS_TABLE        = module.ddb_player_stats.table_name
    PROCESSED_INSIGHTS_BUCKET = module.s3_processed_insights.bucket_name
    PROCESSING_JOBS_TABLE     = module.ddb_processing_jobs.table_name
    SSM_PATH_PREFIX           = module.ssm_parameters.ssm_path_prefix
  }
  policy_arns = [
    aws_iam_policy.lambda_dynamodb.arn,
    aws_iam_policy.lambda_s3.arn,
    aws_iam_policy.lambda_ssm.arn,
    aws_iam_policy.lambda_dynamodb_streams.arn # Event-driven: stream trigger
  ]
}

# DynamoDB Stream -> Insight Generator Event Source Mapping
resource "aws_lambda_event_source_mapping" "insight_generator_stream" {
  event_source_arn                   = module.ddb_processing_jobs.stream_arn
  function_name                      = module.lambda_insight_generator.lambda_arn
  starting_position                  = "LATEST"
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5

  # Only trigger when status changes to "completed"
  filter_criteria {
    filter {
      pattern = jsonencode({
        eventName = ["MODIFY"]
        dynamodb = {
          NewImage = {
            status = {
              S = ["completed"]
            }
          }
          OldImage = {
            status = {
              S = [{ "anything-but" = ["completed"] }]
            }
          }
        }
      })
    }
  }
}

###############################################
# Dead Letter Queues for Async Lambdas
###############################################

module "dlq_data_processor" {
  source     = "./modules/sqs_queue"
  queue_name = "${local.name_prefix}-data-processor-dlq"

  visibility_timeout_seconds    = 300
  message_retention_seconds     = 1209600 # 14 days
  create_dlq                    = false   # This IS the DLQ
  dlq_message_retention_seconds = 0

  tags = local.common_tags
}

module "dlq_insight_generator" {
  source     = "./modules/sqs_queue"
  queue_name = "${local.name_prefix}-insight-generator-dlq"

  visibility_timeout_seconds    = 300
  message_retention_seconds     = 1209600 # 14 days
  create_dlq                    = false   # This IS the DLQ
  dlq_message_retention_seconds = 0

  tags = local.common_tags
}

###############################################
# CloudWatch Alarms for Observability
###############################################

module "alarms_data_processor" {
  source = "./modules/cloudwatch_alarms"

  alarm_name_prefix     = local.name_prefix
  lambda_function_name  = module.lambda_data_processor.function_name
  error_threshold       = 1
  throttle_threshold    = 1
  duration_threshold_ms = 240000 # 4 minutes (80% of 5 min timeout)
  dlq_queue_name        = module.dlq_data_processor.queue_name

  tags = local.common_tags
}

module "alarms_insight_generator" {
  source = "./modules/cloudwatch_alarms"

  alarm_name_prefix     = local.name_prefix
  lambda_function_name  = module.lambda_insight_generator.function_name
  error_threshold       = 1
  throttle_threshold    = 1
  duration_threshold_ms = 144000 # 2.4 minutes (80% of 3 min timeout)
  dlq_queue_name        = module.dlq_insight_generator.queue_name

  tags = local.common_tags
}

module "lambda_recap_server" {
  source        = "./modules/lambda_function"
  function_name = "${local.name_prefix}-recap-server"
  handler       = "recap_server.handler"
  source_dir    = "${path.root}/../../backend/src/lambdas"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 256
  layers        = [aws_lambda_layer_version.shared.arn]
  environment = {
    LOG_LEVEL                 = "INFO"
    PLAYER_STATS_TABLE        = module.ddb_player_stats.table_name
    PROCESSED_INSIGHTS_BUCKET = module.s3_processed_insights.bucket_name
    SSM_PATH_PREFIX           = module.ssm_parameters.ssm_path_prefix
  }
  policy_arns = [
    aws_iam_policy.lambda_dynamodb.arn,
    aws_iam_policy.lambda_s3.arn,
    aws_iam_policy.lambda_ssm.arn
  ]
}

###############################################
# API Gateway with Lambda Authorizer
###############################################

module "http_api" {
  source                       = "./modules/apigateway_http"
  api_name                     = "${local.name_prefix}-api"
  stage_name                   = var.environment
  cors_allowed_origins         = ["https://${aws_cloudfront_distribution.website.domain_name}"]
  cors_allowed_headers         = ["Content-Type", "Authorization"]
  cors_allowed_methods         = ["GET", "POST", "OPTIONS"]
  throttling_burst_limit       = 100
  throttling_rate_limit        = 50
  authorizer_lambda_arn        = module.lambda_authorizer.lambda_arn
  authorizer_lambda_invoke_arn = module.lambda_authorizer.lambda_invoke_arn
  routes = {
    # Legacy auth route - no Firebase auth required (user hasn't logged in yet)
    "POST /api/v1/auth" = {
      target_lambda_arn = module.lambda_auth.lambda_arn
      require_auth      = false
    }
    # Platform auth routes - require Firebase auth to link accounts
    "POST /api/v1/auth/riot" = {
      target_lambda_arn = module.lambda_auth_riot.lambda_arn
      require_auth      = true
    }
    "POST /api/v1/auth/fortnite" = {
      target_lambda_arn = module.lambda_auth_fortnite.lambda_arn
      require_auth      = true
    }
    # All other routes require Firebase authentication
    "POST /api/v1/fetch" = {
      target_lambda_arn = module.lambda_data_fetcher.lambda_arn
      require_auth      = true
    }
    "GET /api/v1/status/{jobId}" = {
      target_lambda_arn = module.lambda_data_processor.lambda_arn
      require_auth      = true
    }
    "GET /api/v1/recap/{sessionId}" = {
      target_lambda_arn = module.lambda_recap_server.lambda_arn
      require_auth      = true
    }
    "POST /api/v1/share/{sessionId}" = {
      target_lambda_arn = module.lambda_recap_server.lambda_arn
      require_auth      = true
    }
    "POST /api/v1/recap/{sessionId}/ask" = {
      target_lambda_arn = module.lambda_recap_server.lambda_arn
      require_auth      = true
    }
    # Health check - no auth required
    "GET /health" = {
      target_lambda_arn = module.lambda_auth.lambda_arn
      require_auth      = false
    }
  }
}

###############################################
# CloudFront Distribution for Static Website
###############################################

resource "aws_cloudfront_origin_access_control" "website" {
  name                              = "${local.name_prefix}-website-oac"
  description                       = "OAC for static website S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "website" {
  origin {
    domain_name              = module.s3_static_website.bucket_regional_domain_name
    origin_id                = "S3-${module.s3_static_website.bucket_name}"
    origin_access_control_id = aws_cloudfront_origin_access_control.website.id
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${module.s3_static_website.bucket_name}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  # Cache behavior for API calls (no caching)
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "API-${module.http_api.api_id}"
    compress               = true
    viewer_protocol_policy = "https-only"

    forwarded_values {
      query_string = true
      headers      = ["*"]
      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # Add API Gateway as origin for API calls
  origin {
    domain_name = replace(module.http_api.api_endpoint, "https://", "")
    origin_id   = "API-${module.http_api.api_id}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  tags = local.common_tags
}

# S3 bucket policy for CloudFront access
resource "aws_s3_bucket_policy" "website" {
  bucket = module.s3_static_website.bucket_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${module.s3_static_website.bucket_arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.website.arn
          }
        }
      }
    ]
  })
}

###############################################
# CloudWatch Monitoring and Alerting
###############################################

# SNS topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"
  tags = local.common_tags
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", module.lambda_auth.function_name],
            [".", ".", ".", module.lambda_data_fetcher.function_name],
            [".", ".", ".", module.lambda_data_processor.function_name],
            [".", ".", ".", module.lambda_insight_generator.function_name],
            [".", ".", ".", module.lambda_recap_server.function_name]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Function Duration"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", module.lambda_auth.function_name],
            [".", ".", ".", module.lambda_data_fetcher.function_name],
            [".", ".", ".", module.lambda_data_processor.function_name],
            [".", ".", ".", module.lambda_insight_generator.function_name],
            [".", ".", ".", module.lambda_recap_server.function_name]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Function Errors"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApiGatewayV2", "Count", "ApiId", module.http_api.api_id],
            [".", "4XXError", ".", "."],
            [".", "5XXError", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "API Gateway Requests and Errors"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", module.ddb_player_stats.table_name],
            [".", "ConsumedWriteCapacityUnits", ".", "."],
            [".", "ConsumedReadCapacityUnits", ".", module.ddb_processing_jobs.table_name],
            [".", "ConsumedWriteCapacityUnits", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "DynamoDB Capacity Usage"
          period  = 300
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = {
    auth              = module.lambda_auth.function_name
    data_fetcher      = module.lambda_data_fetcher.function_name
    data_processor    = module.lambda_data_processor.function_name
    insight_generator = module.lambda_insight_generator.function_name
    recap_server      = module.lambda_recap_server.function_name
  }

  alarm_name          = "${local.name_prefix}-lambda-errors-${each.key}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors lambda errors for ${each.value}"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = each.value
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  for_each = {
    auth              = { name = module.lambda_auth.function_name, threshold = 8000 }
    data_fetcher      = { name = module.lambda_data_fetcher.function_name, threshold = 240000 }
    data_processor    = { name = module.lambda_data_processor.function_name, threshold = 240000 }
    insight_generator = { name = module.lambda_insight_generator.function_name, threshold = 150000 }
    recap_server      = { name = module.lambda_recap_server.function_name, threshold = 25000 }
  }

  alarm_name          = "${local.name_prefix}-lambda-duration-${each.key}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = each.value.threshold
  alarm_description   = "This metric monitors lambda duration for ${each.value.name}"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = each.value.name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
  alarm_name          = "${local.name_prefix}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGatewayV2"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors API Gateway 5XX errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiId = module.http_api.api_id
  }

  tags = local.common_tags
}

# Cost monitoring alarm
resource "aws_cloudwatch_metric_alarm" "estimated_charges" {
  alarm_name          = "${local.name_prefix}-estimated-charges"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = "86400"
  statistic           = "Maximum"
  threshold           = "50"
  alarm_description   = "This metric monitors estimated AWS charges"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    Currency = "USD"
  }

  tags = local.common_tags
}