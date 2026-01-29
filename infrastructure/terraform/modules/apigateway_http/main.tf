data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

resource "aws_apigatewayv2_api" "this" {
  name          = var.api_name
  protocol_type = "HTTP"

  cors_configuration {
    allow_credentials = false
    allow_headers     = var.cors_allowed_headers
    allow_methods     = var.cors_allowed_methods
    allow_origins     = var.cors_allowed_origins
  }
}

resource "aws_apigatewayv2_stage" "this" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = var.stage_name
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = var.throttling_burst_limit
    throttling_rate_limit  = var.throttling_rate_limit
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  for_each = var.routes

  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = each.value.target_lambda_arn
  payload_format_version = "2.0"
}

# Lambda Authorizer (only created if authorizer_lambda_arn is provided)
resource "aws_apigatewayv2_authorizer" "lambda" {
  count = var.authorizer_lambda_invoke_arn != null ? 1 : 0

  api_id                            = aws_apigatewayv2_api.this.id
  authorizer_type                   = "REQUEST"
  authorizer_uri                    = var.authorizer_lambda_invoke_arn
  identity_sources                  = ["$request.header.Authorization"]
  name                              = "${var.api_name}-authorizer"
  authorizer_payload_format_version = "2.0"
  authorizer_result_ttl_in_seconds  = 300  # Cache for 5 minutes
  enable_simple_responses           = false
}

# Permission for API Gateway to invoke the authorizer Lambda
resource "aws_lambda_permission" "authorizer" {
  count = var.authorizer_lambda_arn != null ? 1 : 0

  statement_id  = "AllowAPIGatewayInvokeAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = var.authorizer_lambda_arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/authorizers/*"
}

resource "aws_apigatewayv2_route" "route" {
  for_each = var.routes

  api_id    = aws_apigatewayv2_api.this.id
  route_key = each.key
  target    = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"

  # Configure authorization based on route setting
  authorization_type = (
    each.value.require_auth && var.authorizer_lambda_invoke_arn != null
    ? "CUSTOM"
    : "NONE"
  )
  authorizer_id = (
    each.value.require_auth && var.authorizer_lambda_invoke_arn != null
    ? aws_apigatewayv2_authorizer.lambda[0].id
    : null
  )
}

resource "aws_lambda_permission" "apigw" {
  for_each = var.routes

  statement_id  = "AllowAPIGatewayInvoke-${replace(replace(replace(replace(each.key, " ", "-"), "/", "-"), "{", ""), "}", "")}"
  action        = "lambda:InvokeFunction"
  function_name = each.value.target_lambda_arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${aws_apigatewayv2_api.this.id}/${aws_apigatewayv2_stage.this.name}/*"
}
