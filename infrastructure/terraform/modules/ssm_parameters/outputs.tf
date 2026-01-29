output "parameter_arns" {
  description = "Map of parameter names to their ARNs"
  value       = { for k, v in aws_ssm_parameter.this : k => v.arn }
}

output "parameter_names" {
  description = "Map of parameter keys to their full SSM names"
  value       = { for k, v in aws_ssm_parameter.this : k => v.name }
}

output "ssm_path_prefix" {
  description = "SSM path prefix for this environment"
  value       = "/${var.project_name}/${var.environment}"
}
