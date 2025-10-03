variable "table_name" {
  type        = string
  description = "Name of the DynamoDB table"
}

variable "hash_key" {
  type        = string
  description = "Hash (partition) key name"
}

variable "range_key" {
  type        = string
  description = "Range (sort) key name"
  default     = null
}

variable "attributes" {
  type = list(object({
    name = string
    type = string # S | N | B
  }))
  description = "Attributes to define on the table (must include keys and any TTL attribute)"
}

variable "billing_mode" {
  type        = string
  description = "Billing mode (PROVISIONED or PAY_PER_REQUEST)"
  default     = "PAY_PER_REQUEST"
}

variable "point_in_time_recovery" {
  type        = bool
  description = "Enable PITR"
  default     = true
}

variable "ttl_enabled" {
  type        = bool
  description = "Enable TTL"
  default     = false
}

variable "ttl_attribute_name" {
  type        = string
  description = "TTL attribute name (required if ttl_enabled)"
  default     = null
}

variable "tags" {
  type        = map(string)
  description = "Tags to apply to the table"
  default     = {}
}
