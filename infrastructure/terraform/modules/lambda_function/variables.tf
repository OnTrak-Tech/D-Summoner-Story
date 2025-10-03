variable "function_name" {
  type        = string
  description = "Lambda function name"
}

variable "runtime" {
  type        = string
  description = "Lambda runtime (e.g., python3.12)"
  default     = "python3.12"
}

variable "handler" {
  type        = string
  description = "Lambda handler (module.function)"
}

variable "source_dir" {
  type        = string
  description = "Path to the source directory to zip for the Lambda package"
}

variable "timeout" {
  type        = number
  description = "Lambda timeout in seconds"
  default     = 10
}

variable "memory_size" {
  type        = number
  description = "Lambda memory size in MB"
  default     = 256
}

variable "environment" {
  type        = map(string)
  description = "Environment variables for the Lambda"
  default     = {}
}

variable "log_retention_in_days" {
  type        = number
  description = "CloudWatch log retention in days"
  default     = 14
}

variable "policy_arns" {
  type        = list(string)
  description = "Additional IAM policy ARNs to attach to the Lambda role"
  default     = []
}

variable "attach_basic_execution_role" {
  type        = bool
  description = "Attach AWSLambdaBasicExecutionRole managed policy"
  default     = true
}
