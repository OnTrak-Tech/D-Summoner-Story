variable "project_name" {
  type        = string
  description = "Project name prefix for resources"
}

variable "environment" {
  type        = string
  description = "Environment (dev, staging, prod)"
}

variable "parameters" {
  type = map(object({
    description = string
    type        = optional(string, "SecureString")  # String, StringList, or SecureString
    value       = string
    tier        = optional(string, "Standard")      # Standard or Advanced
  }))
  description = "Map of parameter names to their configurations"
  default     = {}
}

variable "common_tags" {
  type        = map(string)
  description = "Common tags for all resources"
  default     = {}
}
