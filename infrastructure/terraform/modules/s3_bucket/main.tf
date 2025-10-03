resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
  tags   = var.tags
}

resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    object_ownership = "ObjectWriter"
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count  = var.transition_to_ia_after_days == null && var.expire_after_days == null ? 0 : 1
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "lifecycle"
    status = "Enabled"

    filter {}

    dynamic "transition" {
      for_each = var.transition_to_ia_after_days == null ? [] : [1]
      content {
        days          = var.transition_to_ia_after_days
        storage_class = "STANDARD_IA"
      }
    }

    dynamic "expiration" {
      for_each = var.expire_after_days == null ? [] : [1]
      content {
        days = var.expire_after_days
      }
    }
  }
}
