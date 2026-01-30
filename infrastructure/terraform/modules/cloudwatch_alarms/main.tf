# CloudWatch Alarms for Lambda Function Monitoring

# Lambda Errors Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.alarm_name_prefix}-${var.lambda_function_name}-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = var.error_evaluation_periods
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = var.error_period
  statistic           = "Sum"
  threshold           = var.error_threshold
  alarm_description   = "Lambda function ${var.lambda_function_name} has errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  alarm_actions = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
  ok_actions    = var.sns_topic_arn != null ? [var.sns_topic_arn] : []

  tags = var.tags
}

# Lambda Throttles Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${var.alarm_name_prefix}-${var.lambda_function_name}-throttles"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = var.throttle_threshold
  alarm_description   = "Lambda function ${var.lambda_function_name} is being throttled"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  alarm_actions = var.sns_topic_arn != null ? [var.sns_topic_arn] : []

  tags = var.tags
}

# Lambda Duration Alarm (approaching timeout)
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.alarm_name_prefix}-${var.lambda_function_name}-duration"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Maximum"
  threshold           = var.duration_threshold_ms
  alarm_description   = "Lambda function ${var.lambda_function_name} is approaching timeout"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  alarm_actions = var.sns_topic_arn != null ? [var.sns_topic_arn] : []

  tags = var.tags
}

# DLQ Messages Alarm (optional)
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  count = var.dlq_queue_name != null ? 1 : 0

  alarm_name          = "${var.alarm_name_prefix}-${var.dlq_queue_name}-messages"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = var.dlq_message_threshold
  alarm_description   = "DLQ ${var.dlq_queue_name} has messages - failures need investigation"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = var.dlq_queue_name
  }

  alarm_actions = var.sns_topic_arn != null ? [var.sns_topic_arn] : []

  tags = var.tags
}
