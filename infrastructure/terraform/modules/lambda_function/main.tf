data "archive_file" "zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.module}/build/${var.function_name}.zip"
}

data "aws_iam_policy" "basic_exec" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "this" {
  name = "${var.function_name}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = { Service = "lambda.amazonaws.com" },
        Action    = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "basic" {
  count      = var.attach_basic_execution_role ? 1 : 0
  role       = aws_iam_role.this.name
  policy_arn = data.aws_iam_policy.basic_exec.arn
}

resource "aws_iam_role_policy_attachment" "extra" {
  count      = length(var.policy_arns)
  role       = aws_iam_role.this.name
  policy_arn = var.policy_arns[count.index]
}

resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = aws_iam_role.this.arn
  handler       = var.handler
  runtime       = var.runtime
  memory_size   = var.memory_size
  timeout       = var.timeout
  layers        = var.layers

  filename         = data.archive_file.zip.output_path
  source_code_hash = data.archive_file.zip.output_base64sha256

  environment {
    variables = var.environment
  }
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${aws_lambda_function.this.function_name}"
  retention_in_days = var.log_retention_in_days
}
