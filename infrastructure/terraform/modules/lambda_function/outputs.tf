output "lambda_arn" {
  value = aws_lambda_function.this.arn
}

output "lambda_invoke_arn" {
  description = "Invoke ARN for use with API Gateway authorizers"
  value       = aws_lambda_function.this.invoke_arn
}

output "function_name" {
  value = aws_lambda_function.this.function_name
}

output "role_arn" {
  value = aws_iam_role.this.arn
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.this.name
}
