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

# S3 buckets
module "s3_raw_data" {
  source                       = "./modules/s3_bucket"
  bucket_name                  = "${local.name_prefix}-raw-data"
  versioning_enabled           = true
  transition_to_ia_after_days  = 30
  expire_after_days            = 365
  tags                         = local.common_tags
}

module "s3_processed_insights" {
  source                       = "./modules/s3_bucket"
  bucket_name                  = "${local.name_prefix}-processed-insights"
  versioning_enabled           = true
  transition_to_ia_after_days  = 30
  expire_after_days            = 365
  tags                         = local.common_tags
}

module "s3_static_website" {
  source             = "./modules/s3_bucket"
  bucket_name        = "${local.name_prefix}-website"
  versioning_enabled = true
  tags               = local.common_tags
}

# DynamoDB tables
module "ddb_player_stats" {
  source                    = "./modules/dynamodb_table"
  table_name                = "${local.name_prefix}-player-stats"
  hash_key                  = "PK"
  range_key                 = "SK"
  attributes                = [
    { name = "PK",  type = "S" },
    { name = "SK",  type = "S" }
  ]
  ttl_enabled               = true
  ttl_attribute_name        = "ttl"
  billing_mode              = "PAY_PER_REQUEST"
  point_in_time_recovery    = true
  tags                      = local.common_tags
}

module "ddb_processing_jobs" {
  source                    = "./modules/dynamodb_table"
  table_name                = "${local.name_prefix}-processing-jobs"
  hash_key                  = "PK"
  attributes                = [
    { name = "PK",  type = "S" }
  ]
  ttl_enabled               = true
  ttl_attribute_name        = "ttl"
  billing_mode              = "PAY_PER_REQUEST"
  point_in_time_recovery    = true
  tags                      = local.common_tags
}

###############################################
# Bedrock Models (Optional - for reference only)
###############################################

module "bedrock_models" {
  source = "./modules/bedrock_models"
}

###############################################
# Secrets Manager
###############################################

resource "aws_secretsmanager_secret" "riot_api_key" {
  name        = "${local.name_prefix}-riot-api-key"
  description = "Riot Games API key for League of Legends data access"
  tags        = local.common_tags
}

resource "aws_secretsmanager_secret_version" "riot_api_key" {
  secret_id     = aws_secretsmanager_secret.riot_api_key.id
  secret_string = jsonencode({
    api_key = "PLACEHOLDER_RIOT_API_KEY"
  })
  
  lifecycle {
    ignore_changes = [secret_string]
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

# Secrets Manager access policy
resource "aws_iam_policy" "lambda_secrets" {
  name        = "${local.name_prefix}-lambda-secrets"
  description = "Secrets Manager access for Lambda functions"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.riot_api_key.arn
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
  environment   = {
    LOG_LEVEL                = "INFO"
    PLAYER_STATS_TABLE       = module.ddb_player_stats.table_name
    PROCESSING_JOBS_TABLE    = module.ddb_processing_jobs.table_name
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
  environment   = {
    LOG_LEVEL                = "INFO"
    RAW_DATA_BUCKET          = module.s3_raw_data.bucket_name
    PROCESSING_JOBS_TABLE    = module.ddb_processing_jobs.table_name
    RIOT_API_SECRET_ARN      = aws_secretsmanager_secret.riot_api_key.arn
  }
  policy_arns = [
    aws_iam_policy.lambda_dynamodb.arn,
    aws_iam_policy.lambda_s3.arn,
    aws_iam_policy.lambda_secrets.arn
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
  environment   = {
    LOG_LEVEL                = "INFO"
    RAW_DATA_BUCKET          = module.s3_raw_data.bucket_name
    PLAYER_STATS_TABLE       = module.ddb_player_stats.table_name
    PROCESSING_JOBS_TABLE    = module.ddb_processing_jobs.table_name
  }
  policy_arns = [
    aws_iam_policy.lambda_dynamodb.arn,
    aws_iam_policy.lambda_s3.arn
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
  environment   = {
    LOG_LEVEL                = "INFO"
    PLAYER_STATS_TABLE       = module.ddb_player_stats.table_name
    PROCESSED_INSIGHTS_BUCKET = module.s3_processed_insights.bucket_name
    PROCESSING_JOBS_TABLE    = module.ddb_processing_jobs.table_name
  }
  policy_arns = [
    aws_iam_policy.lambda_dynamodb.arn,
    aws_iam_policy.lambda_s3.arn,
    aws_iam_policy.lambda_bedrock.arn
  ]
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
  environment   = {
    LOG_LEVEL                = "INFO"
    PLAYER_STATS_TABLE       = module.ddb_player_stats.table_name
    PROCESSED_INSIGHTS_BUCKET = module.s3_processed_insights.bucket_name
  }
  policy_arns = [
    aws_iam_policy.lambda_dynamodb.arn,
    aws_iam_policy.lambda_s3.arn
  ]
}

###############################################
# API Gateway HTTP (v2)
###############################################

module "http_api" {
  source                 = "./modules/apigateway_http"
  api_name               = "${local.name_prefix}-api"
  stage_name             = var.environment
  cors_allowed_origins   = ["*"]
  cors_allowed_headers   = ["*"]
  cors_allowed_methods   = ["GET", "POST", "OPTIONS"]
  routes = {
    "POST /api/v1/auth" = {
      target_lambda_arn = module.lambda_auth.lambda_arn
    }
    "POST /api/v1/fetch" = {
      target_lambda_arn = module.lambda_data_fetcher.lambda_arn
    }
    "GET /api/v1/status/{jobId}" = {
      target_lambda_arn = module.lambda_data_processor.lambda_arn
    }
    "GET /api/v1/recap/{sessionId}" = {
      target_lambda_arn = module.lambda_recap_server.lambda_arn
    }
    "POST /api/v1/share/{sessionId}" = {
      target_lambda_arn = module.lambda_recap_server.lambda_arn
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
    auth             = module.lambda_auth.function_name
    data_fetcher     = module.lambda_data_fetcher.function_name
    data_processor   = module.lambda_data_processor.function_name
    insight_generator = module.lambda_insight_generator.function_name
    recap_server     = module.lambda_recap_server.function_name
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
    auth             = { name = module.lambda_auth.function_name, threshold = 8000 }
    data_fetcher     = { name = module.lambda_data_fetcher.function_name, threshold = 240000 }
    data_processor   = { name = module.lambda_data_processor.function_name, threshold = 240000 }
    insight_generator = { name = module.lambda_insight_generator.function_name, threshold = 150000 }
    recap_server     = { name = module.lambda_recap_server.function_name, threshold = 25000 }
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