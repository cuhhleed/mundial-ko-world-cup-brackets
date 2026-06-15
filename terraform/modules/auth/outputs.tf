output "user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "Cognito User Pool ARN"
  value       = aws_cognito_user_pool.main.arn
}

output "jwt_issuer_url" {
  description = "Full HTTPS issuer URL for JWT validation"
  value       = "https://${aws_cognito_user_pool.main.endpoint}"
}

output "app_client_id" {
  description = "Cognito app client ID for the frontend"
  value       = aws_cognito_user_pool_client.frontend.id
}
