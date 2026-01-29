# Optional Bedrock Models module for explicit model access configuration
# This is informational only - Bedrock models don't require provisioning

# Data source to list available foundation models
data "aws_bedrock_foundation_models" "available" {
  by_provider = "anthropic"
}

# Data source for specific Claude model
data "aws_bedrock_foundation_model" "claude_sonnet" {
  model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
}

# Local values for commonly used models
locals {
  recommended_models = {
    text_generation  = "anthropic.claude-3-sonnet-20240229-v1:0"
    text_embedding   = "amazon.titan-embed-text-v1"
    image_generation = "stability.stable-diffusion-xl-v1"
  }
}