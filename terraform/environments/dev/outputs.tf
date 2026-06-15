output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the two public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the two private subnets"
  value       = module.networking.private_subnet_ids
}

output "alb_security_group_id" {
  description = "Security group ID for the Application Load Balancer"
  value       = module.networking.alb_security_group_id
}

output "ecs_security_group_id" {
  description = "Security group ID for ECS Fargate tasks"
  value       = module.networking.ecs_security_group_id
}

output "elasticache_security_group_id" {
  description = "Security group ID for ElastiCache Redis"
  value       = module.networking.elasticache_security_group_id
}

output "nat_gateway_public_ip" {
  description = "Public IP address of the NAT Gateway"
  value       = module.networking.nat_gateway_public_ip
}

output "users_table_name" {
  description = "Name of the Users DynamoDB table"
  value       = module.storage.users_table_name
}

output "users_table_arn" {
  description = "ARN of the Users DynamoDB table"
  value       = module.storage.users_table_arn
}

output "brackets_table_name" {
  description = "Name of the Brackets DynamoDB table"
  value       = module.storage.brackets_table_name
}

output "brackets_table_arn" {
  description = "ARN of the Brackets DynamoDB table"
  value       = module.storage.brackets_table_arn
}

output "matches_table_name" {
  description = "Name of the Matches DynamoDB table"
  value       = module.storage.matches_table_name
}

output "matches_table_arn" {
  description = "ARN of the Matches DynamoDB table"
  value       = module.storage.matches_table_arn
}

output "redis_endpoint" {
  description = "DNS endpoint of the Valkey cache node"
  value       = module.storage.redis_endpoint
}

output "redis_port" {
  description = "Port of the Valkey cache node"
  value       = module.storage.redis_port
}

output "ecr_repository_url" {
  description = "URL of the ECR repository for the API image"
  value       = module.compute.ecr_repository_url
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.compute.ecs_cluster_name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.compute.ecs_service_name
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.compute.alb_dns_name
}

output "api_url" {
  description = "Public HTTPS URL for the API"
  value       = module.compute.api_url
}

output "acm_certificate_arn" {
  description = "ARN of the ACM wildcard certificate"
  value       = module.compute.acm_certificate_arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for ECS tasks"
  value       = module.compute.cloudwatch_log_group_name
}
