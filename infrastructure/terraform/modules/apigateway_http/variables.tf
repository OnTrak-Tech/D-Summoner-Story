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
  description = "Map of route_key ('METHOD /path') to target Lambda ARN"
  type = map(object({
    target_lambda_arn = string
  }))
  default = {}
}
