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

# S3 Event Notifications to Lambda
resource "aws_s3_bucket_notification" "lambda" {
  count  = length(var.lambda_notifications) > 0 ? 1 : 0
  bucket = aws_s3_bucket.this.id

  dynamic "lambda_function" {
    for_each = var.lambda_notifications
    content {
      lambda_function_arn = lambda_function.value.lambda_function_arn
      events              = lambda_function.value.events
      filter_prefix       = lambda_function.value.filter_prefix
      filter_suffix       = lambda_function.value.filter_suffix
    }
  }

  depends_on = [aws_lambda_permission.s3]
}

# Lambda permission to allow S3 to invoke
resource "aws_lambda_permission" "s3" {
  for_each = { for idx, n in var.lambda_notifications : idx => n }

  statement_id  = "AllowS3Invoke-${var.bucket_name}-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value.lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.this.arn
}
