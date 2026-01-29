###############################################
# SSM Parameter Store Module
# Stores application secrets and configuration
# Free tier: 10,000 standard parameters
###############################################

resource "aws_ssm_parameter" "this" {
  for_each = var.parameters

  name        = "/${var.project_name}/${var.environment}/${each.key}"
  description = each.value.description
  type        = each.value.type
  value       = each.value.value
  tier        = each.value.tier

  tags = merge(var.common_tags, {
    Name        = each.key
    Environment = var.environment
  })

  lifecycle {
    ignore_changes = [value] # Don't overwrite manually set values
  }
}
