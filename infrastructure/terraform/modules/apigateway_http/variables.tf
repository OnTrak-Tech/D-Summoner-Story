variable "api_name" {
  type        = string
  description = "Name of the HTTP API"
}

variable "stage_name" {
  type        = string
  description = "Deployment stage name"
  default     = "prod"
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "CORS allowed origins"
  default     = ["*"]
}

variable "cors_allowed_headers" {
  type        = list(string)
  description = "CORS allowed headers"
  default     = ["*"]
}

variable "cors_allowed_methods" {
  type        = list(string)
  description = "CORS allowed methods"
  default     = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
}

variable "routes" {
  description = "Map of route_key ('METHOD /path') to target Lambda ARN and auth config"
  type = map(object({
    target_lambda_arn = string
    require_auth      = optional(bool, true)  # Default to requiring auth
  }))
  default = {}
}

variable "authorizer_lambda_arn" {
  type        = string
  description = "ARN of the Lambda function to use as authorizer"
  default     = null
}

variable "authorizer_lambda_invoke_arn" {
  type        = string
  description = "Invoke ARN of the Lambda function to use as authorizer"
  default     = null
}

variable "throttling_burst_limit" {
  type        = number
  description = "Maximum number of requests that can be processed in a burst"
  default     = 100
}

variable "throttling_rate_limit" {
  type        = number
  description = "Maximum number of requests per second"
  default     = 50
}

