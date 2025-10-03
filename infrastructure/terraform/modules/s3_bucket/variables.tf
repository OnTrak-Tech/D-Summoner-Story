variable "bucket_name" {
  type        = string
  description = "Name of the S3 bucket to create"
}

variable "versioning_enabled" {
  type        = bool
  description = "Enable versioning on the bucket"
  default     = true
}

variable "transition_to_ia_after_days" {
  type        = number
  description = "If set, number of days before transitioning objects to STANDARD_IA"
  default     = null
}

variable "expire_after_days" {
  type        = number
  description = "If set, number of days before expiring (deleting) objects"
  default     = null
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to the S3 bucket"
  default     = {}
}
