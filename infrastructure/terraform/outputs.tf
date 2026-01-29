output "raw_data_bucket_name" {
  value = module.s3_raw_data.bucket_name
}

output "processed_insights_bucket_name" {
  value = module.s3_processed_insights.bucket_name
}

output "static_website_bucket_name" {
  value = module.s3_static_website.bucket_name
}

output "player_stats_table_name" {
  value = module.ddb_player_stats.table_name
}

output "processing_jobs_table_name" {
  value = module.ddb_processing_jobs.table_name
}

output "api_endpoint" {
  value = "${module.http_api.api_endpoint}/${module.http_api.stage_name}"
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.website.id
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.website.domain_name
}

output "website_url" {
  value = "https://${aws_cloudfront_distribution.website.domain_name}"
}

output "riot_api_secret_arn" {
  value = aws_secretsmanager_secret.riot_api_key.arn
}

output "sns_alerts_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "cloudwatch_dashboard_url" {
  value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

# Lambda function ARNs for reference
output "lambda_functions" {
  value = {
    auth              = module.lambda_auth.lambda_arn
    data_fetcher      = module.lambda_data_fetcher.lambda_arn
    data_processor    = module.lambda_data_processor.lambda_arn
    insight_generator = module.lambda_insight_generator.lambda_arn
    recap_server      = module.lambda_recap_server.lambda_arn
  }
}

# Bedrock model information
output "bedrock_models" {
  description = "Available Bedrock models and recommendations"
  value = {
    recommended = module.bedrock_models.recommended_models
    claude_arn  = module.bedrock_models.claude_model_arn
  }
}
