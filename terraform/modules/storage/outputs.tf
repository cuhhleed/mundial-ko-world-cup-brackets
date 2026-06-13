# Storage module outputs — DynamoDB + ElastiCache Redis (E1-S2, E1-S3)

output "users_table_name" {
  description = "Name of the Users DynamoDB table"
  value       = aws_dynamodb_table.users.name
}

output "users_table_arn" {
  description = "ARN of the Users DynamoDB table"
  value       = aws_dynamodb_table.users.arn
}

output "brackets_table_name" {
  description = "Name of the Brackets DynamoDB table"
  value       = aws_dynamodb_table.brackets.name
}

output "brackets_table_arn" {
  description = "ARN of the Brackets DynamoDB table"
  value       = aws_dynamodb_table.brackets.arn
}

output "matches_table_name" {
  description = "Name of the Matches DynamoDB table"
  value       = aws_dynamodb_table.matches.name
}

output "matches_table_arn" {
  description = "ARN of the Matches DynamoDB table"
  value       = aws_dynamodb_table.matches.arn
}
