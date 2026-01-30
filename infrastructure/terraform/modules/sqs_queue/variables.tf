variable "queue_name" {
  description = "Name of the SQS queue"
  type        = string
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout for messages in seconds"
  type        = number
  default     = 300 # 5 minutes - should be >= Lambda timeout
}

variable "message_retention_seconds" {
  description = "Message retention period in seconds"
  type        = number
  default     = 86400 # 1 day
}

variable "delay_seconds" {
  description = "Delay before messages become available"
  type        = number
  default     = 0
}

variable "max_receive_count" {
  description = "Number of retries before sending to DLQ"
  type        = number
  default     = 3
}

variable "create_dlq" {
  description = "Whether to create a Dead Letter Queue"
  type        = bool
  default     = true
}

variable "dlq_message_retention_seconds" {
  description = "DLQ message retention period in seconds"
  type        = number
  default     = 1209600 # 14 days
}

variable "tags" {
  description = "Tags for the resources"
  type        = map(string)
  default     = {}
}
