resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = var.billing_mode

  hash_key  = var.hash_key
  range_key = var.range_key

  dynamic "attribute" {
    for_each = var.attributes
    content {
      name = attribute.value.name
      type = attribute.value.type
    }
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }

  dynamic "ttl" {
    for_each = var.ttl_enabled && var.ttl_attribute_name != null ? [1] : []
    content {
      attribute_name = var.ttl_attribute_name
      enabled        = var.ttl_enabled
    }
  }

  tags = var.tags
}
