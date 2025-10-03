variable "preferred_provider" {
  type        = string
  description = "Preferred model provider (anthropic, amazon, ai21, cohere, stability)"
  default     = "anthropic"
}

variable "model_access_required" {
  type        = list(string)
  description = "List of model IDs that require access"
  default = [
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "amazon.titan-embed-text-v1"
  ]
}