variable "aws_region" {
  type        = string
  description = "AWS region to deploy resources into"
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Project name used for resource naming"
  default     = "d-summoner-story"
}

variable "environment" {
  type        = string
  description = "Deployment environment (e.g., dev, staging, prod)"
  default     = "dev"
}

variable "tags" {
  type        = map(string)
  description = "Additional resource tags"
  default     = {}
}
