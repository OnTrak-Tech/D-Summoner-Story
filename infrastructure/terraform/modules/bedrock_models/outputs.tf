output "available_models" {
  description = "List of available Bedrock foundation models"
  value       = data.aws_bedrock_foundation_models.available.model_summaries
}

output "claude_model_arn" {
  description = "ARN of the Claude Sonnet model"
  value       = data.aws_bedrock_foundation_model.claude_sonnet.model_arn
}

output "recommended_models" {
  description = "Recommended model IDs for different use cases"
  value       = local.recommended_models
}