variable "alarm_name_prefix" {
  description = "Prefix for alarm names"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to monitor"
  type        = string
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications (optional)"
  type        = string
  default     = null
}

variable "error_threshold" {
  description = "Number of errors to trigger alarm"
  type        = number
  default     = 1
}

variable "error_evaluation_periods" {
  description = "Number of periods to evaluate for errors"
  type        = number
  default     = 1
}

variable "error_period" {
  description = "Period in seconds for error evaluation"
  type        = number
  default     = 300 # 5 minutes
}

variable "throttle_threshold" {
  description = "Number of throttles to trigger alarm"
  type        = number
  default     = 1
}

variable "duration_threshold_ms" {
  description = "Duration in milliseconds to trigger alarm"
  type        = number
  default     = 60000 # 1 minute
}

variable "dlq_queue_name" {
  description = "Name of the DLQ to monitor (optional)"
  type        = string
  default     = null
}

variable "dlq_message_threshold" {
  description = "Number of DLQ messages to trigger alarm"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Tags for the resources"
  type        = map(string)
  default     = {}
}
